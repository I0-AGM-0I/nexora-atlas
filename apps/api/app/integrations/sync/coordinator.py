"""
NEXORA ATLAS - Synchronization Coordinator
Orchestrates end-to-end AWS read-only ingestion into canonical persistence models.
Guarantees:
1. Exact idempotency (0 duplicates on re-sync).
2. Authoritative-only disappearance (partial failure never infers termination).
3. Explicit separation of aggregated vs resource-level billing data.
4. Complete audit provenance and partial failure semantics.
"""

import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import CloudAccount, CloudRegion, Integration, SyncJob
from app.models.resource import CloudResource, Tag
from app.models.cost import CostRecord
from app.models.organization import AuditLog
from app.models.telemetry import ResourceMetricObservation
from app.integrations.providers.base import (
    PermissionStatus,
    CostAttributionLevel,
    DiscoveredResource,
    DiscoveredTag,
    DiscoveredCostRecord,
)
from app.integrations.providers.aws.client import AWSClientFactory
from app.integrations.providers.aws.auth import AWSAuthenticator
from app.integrations.providers.aws.ec2 import AWSEC2Adapter
from app.integrations.providers.aws.ebs import AWSEBSAdapter
from app.integrations.providers.aws.rds import AWSRDSAdapter
from app.integrations.providers.aws.s3 import AWSS3Adapter
from app.integrations.providers.aws.eks import AWSEKSAdapter
from app.integrations.providers.aws.cost import AWSCostExplorerAdapter
from app.integrations.providers.aws.mapper import AWSModelMapper
from app.integrations.providers.aws.telemetry import (
    DEFAULT_TELEMETRY_WINDOW_DAYS,
    TelemetryQueryPlanner,
    AWSTelemetryAdapter,
    TelemetryExecutionReport,
    TelemetryModelMapper,
)
from app.integrations.sync.checkpoints import SyncWindowCalculator

logger = logging.getLogger("atlas.aws.sync")


class SyncCoordinator:
    """Orchestrates ingestion runs from AWS into canonical database models."""

    @classmethod
    async def execute_sync(
        cls,
        session: AsyncSession,
        integration_id: str,
        org_id: str,
        client_factory: Optional[AWSClientFactory] = None,
        target_end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Executes a complete read-only AWS synchronization pass.
        Returns execution summary dictionary.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch Integration
        int_res = await session.execute(
            select(Integration).where(
                Integration.id == integration_id,
                Integration.org_id == org_id,
            )
        )
        integration = int_res.scalars().first()
        if not integration:
            raise ValueError(f"Integration {integration_id} not found for org {org_id}")

        # 2. Create Running SyncJob
        sync_job = SyncJob(
            integration_id=integration.id,
            job_type="AWS_FULL_INGESTION",
            status="RUNNING",
            started_at=now,
            records_synced=0,
        )
        session.add(sync_job)
        await session.commit()
        await session.refresh(sync_job)

        config = integration.config_json or {}
        factory = client_factory or AWSClientFactory(
            role_arn=config.get("role_arn"),
            external_id=config.get("external_id"),
            region_name=config.get("region") or "us-east-1",
        )

        adapter_failures: Dict[str, str] = {}
        resources_discovered_count = 0
        resources_created_count = 0
        resources_updated_count = 0
        cost_records_processed_count = 0
        cost_records_created_count = 0
        cost_records_updated_count = 0
        telemetry_observations_created_count = 0
        telemetry_observations_updated_count = 0
        resources_with_telemetry_count = 0

        try:
            # 3. Validate Connection & STS Identity
            validation = AWSAuthenticator.validate_connection(factory)
            if not validation.is_valid or not validation.account_id:
                err_msg = validation.error_message or "AWS authentication or permission validation failed."
                sync_job.status = "ERROR"
                sync_job.completed_at = datetime.now(timezone.utc)
                sync_job.error_message = err_msg
                integration.status = "ERROR"
                await session.commit()
                return {
                    "sync_job_id": sync_job.id,
                    "status": "ERROR",
                    "error_message": err_msg,
                }

            account_id_native = validation.account_id

            # 4. Resolve CloudAccount entity
            acc_res = await session.execute(
                select(CloudAccount).where(
                    CloudAccount.org_id == org_id,
                    CloudAccount.provider_type == "AWS",
                    CloudAccount.account_id == account_id_native,
                )
            )
            cloud_account = acc_res.scalars().first()
            if not cloud_account:
                account_name = config.get("account_name") or f"AWS-{account_id_native[-4:]}"
                cloud_account = CloudAccount(
                    org_id=org_id,
                    provider_type="AWS",
                    account_id=account_id_native,
                    name=account_name,
                    status="ACTIVE",
                )
                session.add(cloud_account)
                await session.commit()
                await session.refresh(cloud_account)

            sync_job.account_id = cloud_account.id

            # 5. Discover & Upsert CloudRegions
            ec2_adapter = AWSEC2Adapter(factory)
            discovered_regions = ec2_adapter.describe_regions()
            existing_reg_res = await session.execute(
                select(CloudRegion).where(CloudRegion.provider_type == "AWS")
            )
            existing_regions = {r.region_code: r for r in existing_reg_res.scalars().all()}

            for reg_dto in discovered_regions:
                if reg_dto.region_code not in existing_regions:
                    new_reg = AWSModelMapper.to_cloud_region(reg_dto)
                    session.add(new_reg)
                    existing_regions[reg_dto.region_code] = new_reg

            await session.commit()

            # Refresh region map
            reg_map_res = await session.execute(
                select(CloudRegion).where(CloudRegion.provider_type == "AWS")
            )
            region_db_map = {r.region_code: r.id for r in reg_map_res.scalars().all()}

            # 6. Discover Resources across Adapters
            all_discovered_resources: List[DiscoveredResource] = []
            all_discovered_tags: List[DiscoveredTag] = []
            authoritative_successful_services = set()

            target_regions = config.get("regions") or [factory.region_name]

            # EC2 Instances
            ec2_res, ec2_tags, ec2_err = ec2_adapter.describe_instances(account_id_native, target_regions)
            if ec2_err:
                adapter_failures["EC2"] = ec2_err
            else:
                authoritative_successful_services.add("AmazonEC2_INSTANCE")
                all_discovered_resources.extend(ec2_res)
                all_discovered_tags.extend(ec2_tags)

            # EBS Volumes
            ebs_adapter = AWSEBSAdapter(factory)
            ebs_res, ebs_tags, ebs_err = ebs_adapter.describe_volumes(account_id_native, target_regions)
            if ebs_err:
                adapter_failures["EBS"] = ebs_err
            else:
                authoritative_successful_services.add("AmazonEC2_VOLUME")
                all_discovered_resources.extend(ebs_res)
                all_discovered_tags.extend(ebs_tags)

            # RDS Databases
            rds_adapter = AWSRDSAdapter(factory)
            rds_res, rds_tags, rds_err = rds_adapter.describe_db_instances(account_id_native, target_regions)
            if rds_err:
                adapter_failures["RDS"] = rds_err
            else:
                authoritative_successful_services.add("AmazonRDS_DATABASE")
                all_discovered_resources.extend(rds_res)
                all_discovered_tags.extend(rds_tags)

            # S3 Buckets
            s3_adapter = AWSS3Adapter(factory)
            s3_res, s3_tags, s3_err = s3_adapter.describe_buckets(account_id_native)
            if s3_err:
                adapter_failures["S3"] = s3_err
            else:
                authoritative_successful_services.add("AmazonS3_BUCKET")
                all_discovered_resources.extend(s3_res)
                all_discovered_tags.extend(s3_tags)

            # EKS Clusters
            eks_adapter = AWSEKSAdapter(factory)
            eks_res, eks_tags, eks_err = eks_adapter.describe_clusters(account_id_native, target_regions)
            if eks_err:
                adapter_failures["EKS"] = eks_err
            else:
                authoritative_successful_services.add("AmazonEKS_CLUSTER")
                authoritative_successful_services.add("AmazonEKS_NODEGROUP")
                all_discovered_resources.extend(eks_res)
                all_discovered_tags.extend(eks_tags)

            resources_discovered_count = len(all_discovered_resources)

            # 7. Upsert Resources into Database with Composite Identity Deduplication
            existing_db_res = await session.execute(
                select(CloudResource).where(CloudResource.account_id == cloud_account.id)
            )
            # Map by native_id and service_name (prevents collision across services)
            existing_res_map = {
                f"{r.service_name}::{r.native_id}": r
                for r in existing_db_res.scalars().all()
            }

            discovered_identity_keys = set()
            persisted_res_by_native_id: Dict[str, CloudResource] = {}

            for dto in all_discovered_resources:
                ident_key = f"{dto.service_name}::{dto.native_id}"
                discovered_identity_keys.add(ident_key)
                reg_id = region_db_map.get(dto.region_code) if dto.region_code else None

                if ident_key in existing_res_map:
                    db_item = existing_res_map[ident_key]
                    db_item.status = dto.status
                    db_item.specs_json = dto.specs_json
                    db_item.name = dto.name or dto.native_id
                    if dto.arn:
                        db_item.resource_arn = dto.arn
                    resources_updated_count += 1
                    persisted_res_by_native_id[dto.native_id] = db_item
                else:
                    new_item = AWSModelMapper.to_cloud_resource(dto, cloud_account.id, reg_id)
                    session.add(new_item)
                    resources_created_count += 1
                    persisted_res_by_native_id[dto.native_id] = new_item

            await session.commit()

            # Refresh mapped resources to ensure IDs are loaded
            refreshed_res_q = await session.execute(
                select(CloudResource).where(CloudResource.account_id == cloud_account.id)
            )
            for r in refreshed_res_q.scalars().all():
                persisted_res_by_native_id[r.native_id] = r

            # 8. Upsert Tags (Key-Value pairs)
            existing_tags_q = await session.execute(
                select(Tag).join(CloudResource, Tag.resource_id == CloudResource.id).where(
                    CloudResource.account_id == cloud_account.id
                )
            )
            existing_tags_map = {
                f"{t.resource_id}::{t.key}": t
                for t in existing_tags_q.scalars().all()
            }

            for t_dto in all_discovered_tags:
                parent_res = persisted_res_by_native_id.get(t_dto.resource_native_id)
                if not parent_res:
                    continue

                tag_key = f"{parent_res.id}::{t_dto.key}"
                if tag_key in existing_tags_map:
                    existing_tags_map[tag_key].value = t_dto.value
                else:
                    new_tag = AWSModelMapper.to_tag(t_dto, parent_res.id)
                    session.add(new_tag)
                    existing_tags_map[tag_key] = new_tag

            await session.commit()

            # 9. Authoritative-Only Disappearance Semantics (Correction 8)
            # A resource transitions to TERMINATED only if its service inventory pass succeeded completely.
            for ident_key, db_item in existing_res_map.items():
                service_scope_key = f"{db_item.service_name}_{db_item.resource_type}"
                if (
                    service_scope_key in authoritative_successful_services
                    and ident_key not in discovered_identity_keys
                    and db_item.status not in ("TERMINATED", "DELETED")
                ):
                    db_item.status = "TERMINATED"
                    logger.info("Marked disappeared resource as TERMINATED: %s (%s)", db_item.name, ident_key)

            await session.commit()

            # 10. Ingest Financial Data via Cost Explorer
            ce_adapter = AWSCostExplorerAdapter(factory)
            last_sync_date = integration.last_sync_at.date() if integration.last_sync_at else None
            start_date, end_date, is_initial = SyncWindowCalculator.compute_sync_window(
                last_sync_date=last_sync_date,
                target_end_date=target_end_date,
            )

            # 10a. Aggregated 90-day spend
            try:
                aggregated_cost_records = ce_adapter.get_aggregated_costs(
                    account_id=account_id_native,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception as e:
                adapter_failures["CostExplorer_Aggregated"] = str(e)
                aggregated_cost_records = []

            # 10b. Recent window resource-level spend (14-day limit)
            resource_cost_records: List[DiscoveredCostRecord] = []
            res_ce_available = False
            try:
                resource_cost_records, res_ce_available, res_ce_err = ce_adapter.get_resource_costs(
                    account_id=account_id_native,
                    start_date=start_date,
                    end_date=end_date,
                )
                if res_ce_err and not res_ce_available:
                    adapter_failures["CostExplorer_ResourceLevel"] = res_ce_err
            except Exception as e:
                adapter_failures["CostExplorer_ResourceLevel"] = str(e)

            # Combine and deduplicate cost records
            all_cost_dtos = aggregated_cost_records + resource_cost_records
            cost_records_processed_count = len(all_cost_dtos)

            # Fetch existing CostRecords in sync date window
            existing_cr_q = await session.execute(
                select(CostRecord).where(
                    CostRecord.account_id == cloud_account.id,
                    CostRecord.usage_date >= start_date,
                    CostRecord.usage_date <= end_date,
                )
            )
            # Map by natural key (account_id, usage_date, service_name, resource_id, usage_unit)
            existing_cost_map: Dict[Tuple, CostRecord] = {}
            for cr in existing_cr_q.scalars().all():
                key = (cr.account_id, cr.usage_date, cr.service_name, cr.resource_id, cr.usage_unit)
                existing_cost_map[key] = cr

            for c_dto in all_cost_dtos:
                # Map to canonical resource ID if available
                res_id = None
                if c_dto.resource_native_id and c_dto.resource_native_id in persisted_res_by_native_id:
                    res_id = persisted_res_by_native_id[c_dto.resource_native_id].id

                natural_key = (
                    cloud_account.id,
                    c_dto.usage_date,
                    c_dto.service_name,
                    res_id,
                    c_dto.usage_unit or "Hrs",
                )

                if natural_key in existing_cost_map:
                    # Update existing
                    existing_cr = existing_cost_map[natural_key]
                    existing_cr.unblended_cost = c_dto.unblended_cost
                    existing_cr.amortized_cost = c_dto.amortized_cost
                    if c_dto.usage_quantity is not None:
                        existing_cr.usage_quantity = c_dto.usage_quantity
                    cost_records_updated_count += 1
                else:
                    new_cr = AWSModelMapper.to_cost_record(c_dto, cloud_account.id, res_id)
                    session.add(new_cr)
                    existing_cost_map[natural_key] = new_cr
                    cost_records_created_count += 1

            await session.commit()

            # 11. Ingest Operational Telemetry via CloudWatch
            telemetry_report = TelemetryExecutionReport()
            telemetry_status = "NOT_CONFIGURED"
            try:
                target_dt_end = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
                target_dt_start = target_dt_end - timedelta(days=DEFAULT_TELEMETRY_WINDOW_DAYS)

                # Active compute, storage, and database resources for this account
                active_res_list = [
                    r for r in persisted_res_by_native_id.values()
                    if r.status in ("ACTIVE", "RUNNING", "available", "in-use")
                ]

                if active_res_list:
                    # Build regional resource id map: (region_code, native_id) -> db_resource_id
                    res_id_map: Dict[Tuple[str, str], str] = {}
                    reg_id_to_code = {v: k for k, v in region_db_map.items()}
                    for r in active_res_list:
                        reg_code = reg_id_to_code.get(r.region_id, factory.region_name)
                        res_id_map[(reg_code, r.native_id)] = r.id

                    telemetry_plan = TelemetryQueryPlanner.plan_queries(
                        resources=active_res_list,
                        start_time=target_dt_start,
                        end_time=target_dt_end,
                        default_region=factory.region_name,
                    )

                    telemetry_adapter = AWSTelemetryAdapter(factory)
                    all_raw_metric_results: List[Dict[str, Any]] = []
                    metadata_by_query_id: Dict[str, Any] = {}

                    for batch in telemetry_plan.batches:
                        batch_results = telemetry_adapter.execute_batch(
                            batch=batch,
                            start_time=target_dt_start,
                            end_time=target_dt_end,
                            report=telemetry_report,
                        )
                        all_raw_metric_results.extend(batch_results)
                        metadata_by_query_id.update(batch.metadata_by_query_id)

                    mapped_observations = TelemetryModelMapper.map_metric_data_results(
                        metric_results=all_raw_metric_results,
                        metadata_by_query_id=metadata_by_query_id,
                        org_id=org_id,
                        cloud_account_id=cloud_account.id,
                        account_id_native=account_id_native,
                        sync_job_id=sync_job.id,
                        retrieved_at=now,
                        resource_id_map=res_id_map,
                    )

                    if mapped_observations:
                        incoming_obs_keys = [o.source_observation_key for o in mapped_observations]
                        existing_obs_q = await session.execute(
                            select(ResourceMetricObservation).where(
                                ResourceMetricObservation.source_observation_key.in_(incoming_obs_keys)
                            )
                        )
                        existing_obs_map = {
                            obs.source_observation_key: obs
                            for obs in existing_obs_q.scalars().all()
                        }

                        unique_resources_with_telemetry = set()
                        for obs in mapped_observations:
                            unique_resources_with_telemetry.add(obs.resource_id)
                            if obs.source_observation_key in existing_obs_map:
                                existing_item = existing_obs_map[obs.source_observation_key]
                                existing_item.value = obs.value
                                existing_item.retrieved_at = obs.retrieved_at
                                telemetry_observations_updated_count += 1
                            else:
                                session.add(obs)
                                existing_obs_map[obs.source_observation_key] = obs
                                telemetry_observations_created_count += 1

                        resources_with_telemetry_count = len(unique_resources_with_telemetry)
                        await session.commit()

                    if telemetry_report.errors:
                        adapter_failures.update(telemetry_report.errors)
                        telemetry_status = "PARTIAL"
                    else:
                        telemetry_status = "SUCCESS" if mapped_observations else "NO_DATA"
            except Exception as e:
                logger.warning("Telemetry ingestion failure: %s", str(e))
                adapter_failures["CloudWatch"] = str(e)
                telemetry_status = "ERROR"

            # 12. Finalize SyncJob & Integration Status
            final_status = "COMPLETED"
            if adapter_failures:
                if len(adapter_failures) >= 5:  # Majority failed
                    final_status = "ERROR"
                else:
                    final_status = "PARTIAL"

            error_summary = (
                "; ".join([f"{k}: {v}" for k, v in adapter_failures.items()])
                if adapter_failures
                else None
            )

            total_synced = (
                resources_created_count
                + resources_updated_count
                + cost_records_created_count
                + cost_records_updated_count
                + telemetry_observations_created_count
                + telemetry_observations_updated_count
            )
            sync_job.status = final_status
            sync_job.completed_at = datetime.now(timezone.utc)
            sync_job.records_synced = total_synced
            sync_job.error_message = error_summary
            sync_job.details_json = {
                "resources_discovered": resources_discovered_count,
                "resources_created": resources_created_count,
                "cost_records_created": cost_records_created_count,
                "telemetry_status": telemetry_status,
                "telemetry_observations_created": telemetry_observations_created_count,
                "telemetry_observations_updated": telemetry_observations_updated_count,
                "resources_with_telemetry": resources_with_telemetry_count,
                "queries_requested": telemetry_report.queries_requested,
                "queries_executed": telemetry_report.queries_executed,
                "data_points_received": telemetry_report.data_points_received,
                "pages_fetched": telemetry_report.pages_fetched,
            }

            integration.status = "SYNCED" if final_status == "COMPLETED" else final_status
            integration.last_sync_at = sync_job.completed_at

            # 13. Record Audit Log
            audit_entry = AuditLog(
                org_id=org_id,
                actor_id="system:aws-sync",
                action="AWS_READONLY_SYNC",
                entity_type="Integration",
                entity_id=integration.id,
                metadata_json={
                    "status": final_status,
                    "account_id": account_id_native,
                    "sync_window": f"{start_date.isoformat()} to {end_date.isoformat()}",
                    "resources_discovered": resources_discovered_count,
                    "resources_created": resources_created_count,
                    "resources_updated": resources_updated_count,
                    "cost_records_processed": cost_records_processed_count,
                    "cost_records_created": cost_records_created_count,
                    "cost_records_updated": cost_records_updated_count,
                    "telemetry_status": telemetry_status,
                    "telemetry_observations_created": telemetry_observations_created_count,
                    "resources_with_telemetry": resources_with_telemetry_count,
                    "data_points_received": telemetry_report.data_points_received,
                    "failures": adapter_failures,
                },
            )
            session.add(audit_entry)
            await session.commit()

            return {
                "sync_job_id": sync_job.id,
                "status": final_status,
                "account_id": account_id_native,
                "started_at": sync_job.started_at.isoformat() if sync_job.started_at else None,
                "completed_at": sync_job.completed_at.isoformat() if sync_job.completed_at else None,
                "resources_discovered": resources_discovered_count,
                "resources_created": resources_created_count,
                "resources_updated": resources_updated_count,
                "cost_records_processed": cost_records_processed_count,
                "cost_records_created": cost_records_created_count,
                "cost_records_updated": cost_records_updated_count,
                "telemetry_observations_created": telemetry_observations_created_count,
                "telemetry_observations_updated": telemetry_observations_updated_count,
                "resources_with_telemetry": resources_with_telemetry_count,
                "telemetry_status": telemetry_status,
                "warnings": [f"{k}: {v}" for k, v in adapter_failures.items()],
            }

        except Exception as e:
            logger.exception("Fatal failure during sync coordination: %s", str(e))
            sync_job.status = "ERROR"
            sync_job.completed_at = datetime.now(timezone.utc)
            sync_job.error_message = str(e)
            integration.status = "ERROR"
            await session.commit()
            return {
                "sync_job_id": sync_job.id,
                "status": "ERROR",
                "error_message": str(e),
            }

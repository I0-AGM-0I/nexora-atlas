# Database Implementation Report - NEXORA ATLAS (Phase 2)

## 1. Final Entity Relationship Model

The ATLAS persistence layer is modeled around 16 first-class domain entities partitioning tenancy, inventory, cost records, statistical anomalies, explainable waste, actionable recommendations, forward forecasting, and scenarios.

```
Organization (Root Tenant)
├── CloudAccount (AWS, Azure, GCP)
│   ├── CloudResource (Inventory: EC2, RDS, S3, EKS...)
│   │   ├── Tag (Key-Value metadata with unique key per resource)
│   │   ├── CostRecord (Granular line item, unblended & amortized)
│   │   ├── OptimizationOpportunity (Detected inefficiency)
│   │   │   └── Recommendation (Actionable proposal with ₹ savings)
│   │   └── ScenarioChange (Simulated delta configuration)
│   ├── CostRecord (Direct line item, e.g. Data Transfer / Tax)
│   ├── CostSnapshot (Daily / Monthly rollups for dashboard)
│   ├── Anomaly (Observed spend spike vs Inferred root cause)
│   ├── OptimizationOpportunity (Unattached / idle resources)
│   ├── Forecast (Statistical trajectory with upper/lower bounds)
│   └── SyncJob (Historical sync execution audit)
├── Integration (Provider credentials & auth method)
│   └── SyncJob (Synchronization executions)
├── Scenario (Hypothetical topology changes & trade-offs)
│   └── ScenarioChange (Discrete resource alterations)
└── AuditLog (Immutable governance log)
```

---

## 2. Final Schema Specification

1. **`organizations`**: Multi-tenant anchor (`id`, `name`, `slug`, `currency`, `timezone`, `is_demo`, timestamps).
2. **`cloud_accounts`**: Provider accounts (`id`, `org_id`, `provider_type`, `account_id`, `name`, `status`, timestamps).
3. **`cloud_regions`**: Normalized geographic regions (`id`, `provider_type`, `region_code`, `display_name`, timestamps).
4. **`cloud_resources`**: Asset inventory (`id`, `account_id`, `region_id`, `service_name`, `resource_type`, `resource_arn`, `native_id`, `name`, `status`, `specs_json`, timestamps).
5. **`tags`**: Resource metadata (`id`, `resource_id`, `key`, `value`, timestamps).
6. **`cost_records`**: Granular financial lines (`id`, `account_id`, `resource_id`, `service_name`, `usage_date`, `unblended_cost`, `amortized_cost`, `usage_quantity`, `usage_unit`, `currency`, timestamps).
7. **`cost_snapshots`**: Period aggregates (`id`, `account_id`, `period_start`, `period_end`, `period_type`, `total_cost`, `breakdown_json`, timestamps).
8. **`anomalies`**: Spend anomalies (`id`, `account_id`, `resource_id`, `service_name`, `observed_cost`, `baseline_cost`, `percentage_change`, `detected_at`, `detection_rule`, `observed_metrics_json`, `severity`, `status`, `inferred_cause`, `confidence_pct`, `inference_details_json`, timestamps).
9. **`optimization_opportunities`**: Waste detections (`id`, `account_id`, `resource_id`, `category`, `waste_type`, `severity`, `status`, `estimated_waste_monthly`, `evidence_json`, timestamps).
10. **`recommendations`**: Actionable proposals (`id`, `opportunity_id`, `resource_id`, `category`, `title`, `current_configuration`, `recommended_configuration`, `estimated_monthly_savings`, `estimated_annual_savings`, `confidence_pct`, `risk_level`, `reasoning`, `evidence_json`, `status`, timestamps).
11. **`scenarios`**: Simulated change workbench (`id`, `org_id`, `name`, `description`, `baseline_monthly_cost`, `projected_monthly_cost`, `monthly_savings`, `percentage_savings`, `performance_risk`, `reliability_risk`, `complexity_level`, `assumptions_json`, timestamps).
12. **`scenario_changes`**: Discrete scenario steps (`id`, `scenario_id`, `resource_id`, `change_type`, `current_spec`, `proposed_spec`, `delta_cost`, timestamps).
13. **`forecasts`**: Statistical forward spend (`id`, `account_id`, `forecast_month`, `projected_cost`, `lower_bound`, `upper_bound`, `confidence_pct`, `cost_drivers_json`, `algorithm`, timestamps).
14. **`integrations`**: Connection metadata (`id`, `org_id`, `provider_type`, `status`, `auth_method`, `config_json`, `last_sync_at`, timestamps).
15. **`sync_jobs`**: Ingest audit records (`id`, `integration_id`, `account_id`, `job_type`, `status`, `started_at`, `completed_at`, `records_synced`, `error_message`, timestamps).
16. **`audit_logs`**: Append-only log (`id`, `org_id`, `actor_id`, `action`, `entity_type`, `entity_id`, `metadata_json`, `timestamp`).

---

## 3. Foreign Key & Tenant Isolation Strategy

- **Cascading Deletes**: 
  - `organizations -> cloud_accounts`, `integrations`, `scenarios`, `audit_logs` enforce `ondelete="CASCADE"`.
  - `cloud_accounts -> cloud_resources`, `cost_records`, `cost_snapshots`, `anomalies`, `optimization_opportunities`, `forecasts` enforce `ondelete="CASCADE"`.
- **Set Null Protection**:
  - `cost_records.resource_id`, `anomalies.resource_id`, `recommendations.resource_id`, `scenario_changes.resource_id` use `ondelete="SET NULL"`. If an inventory resource is purged or terminated, financial history and historical recommendations are preserved.
- **Tenant Isolation**: Every query in the repository layer scopes through `organization_id` or `account_id`.

---

## 4. Indexing Strategy & Rationale

Indexes were constructed exclusively to accelerate high-frequency query patterns:
1. `ix_organizations_slug`: Unique tenant resolution by subdomain or URL slug.
2. `ix_cloud_accounts_org_status`: Filtering active cloud accounts per tenant.
3. `ix_cloud_resources_account_service_type`: Multidimensional filtering on `/resources` and Spend drill-down.
4. `ix_cloud_resources_resource_arn`: Direct O(1) lookup during AWS synchronization.
5. `ix_tags_resource_id` & `ix_tags_key_value`: Tag search and filtering.
6. `ix_cost_records_account_date_service`: Date range filtering for spend time-series and service breakdowns.
7. `ix_cost_records_resource_date`: Resource-level cost attribution over time.
8. `ix_cost_snapshots_account_period`: Instant retrieval of pre-aggregated monthly dashboard metrics.
9. `ix_anomalies_account_severity_status`: High-priority alert counts on Overview Dashboard and Anomaly Center.
10. `ix_recommendations_opp_status`: Active recommendation retrieval for Optimization Center.
11. `ix_forecasts_account_month`: Time-series forecast lookup.
12. `ix_audit_logs_org_timestamp`: Chronological tenant activity stream.

---

## 5. Monetary Precision Strategy

- **Type**: `Numeric(18, 4)` / Python `decimal.Decimal`.
- **Rationale**: Cloud billing line items often involve fractions of a cent (e.g., AWS Lambda request charges, per-second EC2 pricing). Using `FLOAT` or `DOUBLE` introduces cumulative rounding errors that are unacceptable in financial B2B SaaS software.
- **Scope**: Applied to `unblended_cost`, `amortized_cost`, `total_cost`, `observed_cost`, `baseline_cost`, `estimated_waste_monthly`, `estimated_monthly_savings`, `estimated_annual_savings`, `baseline_monthly_cost`, `projected_monthly_cost`, `monthly_savings`, and `delta_cost`.

---

## 6. Observed vs. Inference Separation in Anomaly Detection

To prevent speculative AI or heuristic guesses from corrupting empirical telemetry, `Anomaly` cleanly divides:
- **Observed (Factual)**: `observed_cost`, `baseline_cost`, `percentage_change`, `detected_at`, `detection_rule`, `observed_metrics_json`.
- **Inference (Hypothesized)**: `severity`, `status`, `inferred_cause`, `confidence_pct`, `inference_details_json`.

---

## 7. Opportunity vs. Recommendation Separation

- **`OptimizationOpportunity`**: Identifies the inefficiency (e.g., an underutilized `m5.4xlarge` EC2 instance).
- **`Recommendation`**: Represents a concrete proposed remediation (e.g., Option 1: Right-size to `m5.large`; Option 2: Migrate to Graviton `c7g.large`).
- One opportunity can have multiple distinct recommendations with different risk/savings profiles.

---

## 8. UUID, Timestamp, and Enum Strategies

- **UUID Strategy**: Portable 36-character standard string UUIDs (`uuid.uuid4()`). Avoids database dialect collisions between PostgreSQL `UUID` and SQLite `TEXT`.
- **Timestamp Strategy**: Timezone-aware UTC datetimes (`DateTime(timezone=True)`). The database stores all events in UTC.
- **Enum Strategy**: Portable string-backed enums (`String(20)` to `String(50)`), validated strictly via Pydantic schemas and application repositories.

---

## 9. Repository Layer Architecture

Clean separation of data access from route handlers and business engines:
- `BaseRepository[ModelType]`: Generic async CRUD operations (`get_by_id`, `list_all`, `count`, `create`, `bulk_create`, `update`, `delete_by_id`).
- `OrganizationRepository`: Tenant lookups by slug.
- `CloudAccountRepository`: Multi-account tenant querying.
- `CloudResourceRepository`: Discovered inventory lookup with eager tag loading.
- `CostRepository`: Aggregations, date range filtering, and snapshot management.
- `AnomalyRepository`: Severity/status filtering and alert counting.
- `OptimizationOpportunityRepository` & `RecommendationRepository`: Eager-loaded opportunity-recommendation hierarchies and potential savings calculations.
- `ScenarioRepository`: Scenario retrieval with associated change lists.
- `ForecastRepository`: Forward trajectory queries.
- `AuditLogRepository`: Immutable append-only log preventing updates or deletions.

---

## 10. Verification & Test Results

- **Alembic Migration**:
  - `initial_schema.py` auto-generated from model metadata.
  - Successfully verified lifecycle: `upgrade head` -> `downgrade base` -> `upgrade head`.
- **Pytest Suite (`pytest apps/api/tests -v`)**:
  - 19 of 19 automated tests passed (100% pass rate in 2.31s).
  - Validates model creation, foreign key cascading, unique constraints, monetary precision, relationships, and repository methods.
- **Offline Integrity**: Zero AWS SDK calls, zero AWS network calls, and zero external cloud credentials used.

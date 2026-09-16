# Data Model Specification - NEXORA ATLAS

NEXORA ATLAS uses an expressive relational domain model built with SQLAlchemy 2.0. The schema is designed for multi-account cloud inventory tracking, high-velocity cost line items, statistical anomalies, explainable waste detection, actionable recommendations, forward forecasting, and scenario simulations.

## 1. Core Entities

### Multi-Tenancy & Account Topology
- **Organization**: Top-level tenant (`id`, `name`, `slug`, `currency`, `timezone`, `is_demo`, `created_at`).
- **CloudAccount**: Connected provider accounts (`id`, `org_id`, `provider_type`, `account_id`, `name`, `status`, `created_at`).
- **CloudRegion**: Normalized geographic cloud regions (`id`, `provider_type`, `region_code`, `display_name`).
- **CloudResource**: Discovered inventory item (`id`, `account_id`, `region_id`, `service_name`, `resource_type`, `resource_arn`, `native_id`, `name`, `status`, `specs_json`, `created_at`).
- **Tag**: Key-value pairs attached to cloud resources (`id`, `resource_id`, `key`, `value`).

### Financial Cost Telemetry
- **CostRecord**: Granular cost time series records (`id`, `account_id`, `resource_id`, `service_name`, `usage_date`, `unblended_cost`, `amortized_cost`, `usage_quantity`, `usage_unit`, `currency`).
- **CostSnapshot**: Aggregated rollups for performance (daily/monthly snapshots per service/account).

### Intelligence & Detection
- **Anomaly**: Detected spending anomalies (`id`, `account_id`, `service_name`, `resource_id`, `severity`, `status`, `observed_cost`, `baseline_cost`, `pct_change`, `detection_rule`, `evidence_json`, `inference_json`, `detected_at`).
- **OptimizationOpportunity**: Detected hardware/storage waste (`id`, `account_id`, `resource_id`, `category`, `waste_type`, `severity`, `metrics_evidence_json`).
- **Recommendation**: Concrete optimization proposals (`id`, `opportunity_id`, `resource_id`, `category`, `title`, `current_configuration`, `recommended_configuration`, `estimated_monthly_savings`, `estimated_annual_savings`, `confidence_pct`, `risk_level`, `reasoning`, `evidence_json`, `status`).

### Strategic Planning & Ingestion
- **Scenario**: Infrastructure change simulation (`id`, `org_id`, `name`, `description`, `baseline_monthly_cost`, `projected_monthly_cost`, `monthly_savings`, `pct_savings`, `performance_risk`, `reliability_risk`, `complexity_level`, `assumptions_json`).
- **ScenarioChange**: Specific alterations in a scenario (`id`, `scenario_id`, `resource_id`, `change_type`, `current_spec`, `proposed_spec`, `delta_cost`).
- **Forecast**: Projected future monthly expenditure (`id`, `account_id`, `forecast_month`, `projected_cost`, `lower_bound`, `upper_bound`, `confidence_pct`, `cost_drivers_json`, `algorithm`).
- **Integration**: Cloud credentials and provider configs (`id`, `org_id`, `provider_type`, `status`, `auth_method`, `config_json`, `last_sync_at`).
- **SyncJob**: Ingestion job tracking (`id`, `integration_id`, `account_id`, `job_type`, `status`, `started_at`, `completed_at`, `records_synced`, `error_message`).
- **AuditLog**: Governance and operational history (`id`, `org_id`, `actor_id`, `action`, `entity_type`, `entity_id`, `metadata_json`, `timestamp`).

## 2. Portability Guarantees
- Primary keys utilize UUID4 strings, avoiding dialect-dependent native UUID issues between PostgreSQL and SQLite.
- Timestamps explicitly specify timezone awareness (`DateTime(timezone=True)`).
- JSON payloads store unstructured telemetry evidence cleanly across both engines.

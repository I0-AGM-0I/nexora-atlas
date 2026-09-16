# Telemetry Separation: Financial Cost vs. Operational Telemetry

A foundational architectural principle of NEXORA ATLAS is the strict separation between **Financial Cost Data** and **Operational Resource Telemetry**.

## 1. Why the Separation Matters

Many cloud systems conflate cost data with performance metrics. In AWS and modern cloud architectures:
- **Cost Explorer / CUR (Cost & Usage Report)**: Provides purely financial data (unblended costs, amortized costs, credit deductions, usage quantities like running hours, GB-months). It **does not** supply CPU utilization, memory pressure, disk I/O, or network packet drops.
- **CloudWatch / Monitoring Agents (Datadog, Prometheus)**: Provides fine-grained operational metrics (CPUUtilization %, memory_used_percent, IOPS, network ingress/egress bytes). It **does not** supply billing rates, discounts, or reservation allocations.

Attempting to infer resource utilization from billing lines or vice-versa leads to fragile integrations and incorrect optimization recommendations.

## 2. Ingestion Decoupling Architecture

```
Financial Billing Providers                     Operational Telemetry Providers
  (AWS Cost Explorer / CUR)                      (AWS CloudWatch / Datadog / Agent)
            │                                                    │
            ▼                                                    ▼
   [ Cost Ingestion Service ]                         [ Telemetry Ingestion Service ]
            │                                                    │
            ▼                                                    ▼
   [ CostRecord / CostSnapshot ]                      [ ResourceMetricRecord ]
   - unblended_cost                                   - metric_name (CPU, Mem)
   - amortized_cost                                   - p50, p95, max utilization
   - usage_quantity (hours, GB)                       - sample_window_days
            │                                                    │
            └─────────────────────────┬──────────────────────────┘
                                      ▼
                        [ Optimization Engine ]
                    Correlates Financial Cost with
                      Measured Hardware Capacity
                                      │
                                      ▼
                             [ Recommendation ]
                    "EC2 instance m5.4xlarge costs
                     ₹34,200/mo but has p95 CPU < 11%"
```

## 3. Extensibility Guardrails
1. **Provider Isolation**: Ingesting AWS Cost Explorer does not require or imply CloudWatch connectivity.
2. **Flexible Telemetry Sources**: Organizations may use AWS Cost Explorer for billing while streaming utilization metrics from Datadog, Prometheus, or internal agents.
3. **Deterministic Correlation**: The Waste and Optimization engines ingest explicit snapshots of observed utilization alongside cost records, keeping assumptions auditable and transparent.

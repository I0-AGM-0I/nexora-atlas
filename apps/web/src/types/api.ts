/**
 * NEXORA ATLAS - Shared Frontend API Response Types
 * Strongly typed contracts matching backend Pydantic models.
 */

export interface DemoEvent {
  id: string;
  occurred_at: string;
  title: string;
  description: string;
  category: string;
  impact_service: string;
  related_resource_native_id?: string | null;
}

export interface DashboardSummary {
  organization_name: string;
  total_spend: string;
  monthly_run_rate: string;
  previous_30d_spend: string;
  run_rate_change_pct?: string | number | null;
  potential_monthly_savings: string;
  potential_annual_savings: string;
  active_anomalies: number;
  total_resources: number;
  total_accounts: number;
  currency: string;
  max_date: string;
  min_date: string;
  is_demo: boolean;
}

export interface SpendTrendPoint {
  date: string;
  spend: string | number;
  cumulative_spend: string | number;
  events: DemoEvent[];
}

export interface SpendTrendResponse {
  points: SpendTrendPoint[];
  total_spend: string | number;
  period_days: number;
  currency: string;
}

export interface ServiceBreakdownItem {
  service_name: string;
  total_spend: string | number;
  percentage: string | number;
}

export interface ServiceBreakdownResponse {
  items: ServiceBreakdownItem[];
  total_spend: string | number;
  currency: string;
}

export interface AccountBreakdownItem {
  account_id: string;
  account_name: string;
  provider_account_id: string;
  total_spend: string | number;
  percentage: string | number;
}

export interface AccountBreakdownResponse {
  items: AccountBreakdownItem[];
  total_spend: string | number;
  currency: string;
}

export interface RecentActivityItem {
  id: string;
  timestamp: string;
  action: string;
  entity_type: string;
  actor_id: string;
  metadata_json?: Record<string, any> | null;
}

export interface RecentActivityResponse {
  items: RecentActivityItem[];
}

export interface ResourceSpendItem {
  resource_id: string;
  native_id: string;
  resource_name: string;
  service_name: string;
  resource_type: string;
  account_name: string;
  region: string;
  spend: string | number;
  percentage_of_total: string | number;
}

export interface SpendExplorerResponse {
  period_days: number;
  start_date: string;
  end_date: string;
  total_spend: string | number;
  previous_period_spend?: string | number | null;
  period_change_pct?: string | number | null;
  currency: string;
  trend: SpendTrendPoint[];
  service_breakdown: ServiceBreakdownItem[];
  account_breakdown: AccountBreakdownItem[];
  resource_items: ResourceSpendItem[];
  total_resources: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AnomalyObservedFacts {
  observed_cost: string | number;
  baseline_cost: string | number;
  percentage_change: string | number;
  detected_at: string;
  detection_rule: string;
  observed_metrics_json?: Record<string, any> | null;
}

export interface AnomalyInferredAnalysis {
  severity: string;
  status: string;
  inferred_cause?: string | null;
  confidence_pct: string | number;
  inference_details_json?: Record<string, any> | null;
}

export interface AnomalyItem {
  id: string;
  account_id: string;
  account_name: string;
  resource_id?: string | null;
  resource_name?: string | null;
  resource_native_id?: string | null;
  service_name: string;
  observed: AnomalyObservedFacts;
  inference: AnomalyInferredAnalysis;
}

export interface AnomalyListResponse {
  items: AnomalyItem[];
  total_count: number;
  open_count: number;
}

export interface RecommendationItem {
  id: string;
  opportunity_id: string;
  title: string;
  category: string;
  current_configuration: string;
  recommended_configuration: string;
  estimated_monthly_savings: string | number;
  estimated_annual_savings: string | number;
  confidence_pct: string | number;
  risk_level: string;
  reasoning: string;
}

export interface OpportunityItem {
  id: string;
  account_id: string;
  account_name: string;
  resource_id?: string | null;
  resource_name?: string | null;
  resource_native_id?: string | null;
  category: string;
  waste_type: string;
  severity: string;
  status: string;
  estimated_waste_monthly: string | number;
  estimated_waste_annual: string | number;
  evidence_json: Record<string, any>;
  recommendations: RecommendationItem[];
}

export interface OptimizationOverviewResponse {
  potential_monthly_savings: string | number;
  potential_annual_savings: string | number;
  opportunity_count: number;
  recommendation_count: number;
  opportunities: OpportunityItem[];
}

export interface ResourceListItem {
  id: string;
  account_id: string;
  account_name: string;
  region_code: string;
  native_id: string;
  name: string;
  service_name: string;
  resource_type: string;
  status: string;
  tags: Record<string, string>;
  cost_30d?: string | number | null;
}

export interface ResourceListResponse {
  items: ResourceListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ScenarioChangeItem {
  id: string;
  scenario_id: string;
  resource_id?: string | null;
  change_type: string;
  current_spec: string;
  proposed_spec: string;
  delta_cost: string | number;
}

export interface ScenarioItem {
  id: string;
  name: string;
  description?: string | null;
  baseline_monthly_cost: string | number;
  projected_monthly_cost: string | number;
  monthly_savings: string | number;
  percentage_savings: string | number;
  performance_risk: string;
  reliability_risk: string;
  complexity_level: string;
  assumptions_json?: Record<string, any> | null;
  changes: ScenarioChangeItem[];
}

export interface ScenarioListResponse {
  scenarios: ScenarioItem[];
}

export interface ForecastItem {
  id: string;
  account_id: string;
  account_name: string;
  forecast_month: string;
  projected_cost: string | number;
  lower_bound: string | number;
  upper_bound: string | number;
  confidence_pct: string | number;
  algorithm: string;
  is_synthetic: boolean;
}

export interface ForecastResponse {
  disclaimer: string;
  forecasts: ForecastItem[];
}

export interface RuleEvaluationItem {
  rule_id: string;
  rule_type: string;
  status: string;
  skip_reason?: string | null;
  findings_count: number;
}

export interface IntelligenceRunResponse {
  run_id: string;
  organization_id: string;
  ruleset_version: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  anomalies_detected: number;
  opportunities_found: number;
  recommendations_generated: number;
  potential_monthly_savings: string | number;
  potential_annual_savings: string | number;
  rule_evaluations: RuleEvaluationItem[];
}

export interface IntelligenceStatusResponse {
  ruleset_version: string;
  status: string;
  last_run_at?: string | null;
  last_run_id?: string | null;
  active_anomalies_count: number;
  active_opportunities_count: number;
  addressable_monthly_savings: string | number;
  addressable_annual_savings: string | number;
  is_offline_mode: boolean;
  aws_network_disabled: boolean;
}

// ==========================================
// Phase 6 — Advanced Analytics & Modeling Types
// ==========================================

export interface AnalyticalExplanation {
  observations: Record<string, any>;
  derived_metrics: Record<string, any>;
  classification?: string | null;
  evidence: string[];
  method: string;
  parameters: Record<string, any>;
  assumptions: Record<string, any>;
  version: string;
}

export interface DailyTrendPoint {
  date: string;
  observed_cost: string | number;
  rolling_mean_7d?: string | number | null;
  rolling_mean_14d?: string | number | null;
  rolling_mean_30d?: string | number | null;
  regime: 'SPIKE' | 'RECOVERY' | 'ELEVATED' | 'NORMAL';
}

export interface TrendAnalysisResult {
  sufficiency_status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
  trend_direction: 'INCREASING' | 'DECREASING' | 'STABLE' | 'VOLATILE';
  current_regime: 'SPIKE' | 'RECOVERY' | 'ELEVATED' | 'NORMAL';
  mean_daily_spend: string | number;
  stddev_daily_spend: string | number;
  coefficient_of_variation: string | number;
  max_daily_deviation: string | number;
  period_over_period_delta: string | number;
  period_over_period_pct: string | number;
  daily_series: DailyTrendPoint[];
  explanation: AnalyticalExplanation;
}

export interface CostDriverItem {
  dimension: 'SERVICE' | 'ACCOUNT' | 'RESOURCE' | 'REGION';
  identifier: string;
  name: string;
  current_period_cost: string | number;
  previous_period_cost: string | number;
  cost_delta: string | number;
  absolute_contribution_pct: string | number;
  net_change_contribution_pct?: string | number | null;
  direction: string;
  rank: number;
  classification: 'USAGE' | 'LIKELY_USAGE_DRIVEN' | 'PRICE_CONFIG' | 'MIX_SHIFT' | 'NEW_RESOURCE' | 'REMOVED_RESOURCE' | 'NOT_AVAILABLE';
  explanation: AnalyticalExplanation;
}

export interface DriverDecompositionResult {
  sufficiency_status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
  comparison_window_days: number;
  current_period_cost: string | number;
  previous_period_cost: string | number;
  net_change: string | number;
  net_change_pct: string | number;
  service_drivers: CostDriverItem[];
  account_drivers: CostDriverItem[];
  resource_drivers: CostDriverItem[];
  region_drivers: CostDriverItem[];
  reconciled: boolean;
  explanation: AnalyticalExplanation;
}

export interface ConcentrationMetrics {
  sufficiency_status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
  top_1_service_share_pct: string | number;
  top_3_service_share_pct: string | number;
  top_5_resource_share_pct: string | number;
  top_account_share_pct: string | number;
  spend_concentration_index: string | number;
  hhi_interpretation: string;
  explanation: AnalyticalExplanation;
}

export interface HeadroomItem {
  resource_id: string;
  resource_name: string;
  service_name: string;
  instance_type?: string | null;
  p95_utilization_cpu?: string | number | null;
  p95_utilization_memory?: string | number | null;
  observed_utilization_headroom_cpu?: string | number | null;
  observed_utilization_headroom_memory?: string | number | null;
  sufficiency_status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
}

export interface UnitEconomicsContract {
  metric_name: string;
  unit_name: string;
  status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
  cost_per_unit?: string | number | null;
  explanation: string;
}

export interface EfficiencyReport {
  sufficiency_status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
  headroom_items: HeadroomItem[];
  idle_resources_count: number;
  idle_resources_cost: string | number;
  estimated_addressable_waste: string | number;
  unit_economics: UnitEconomicsContract[];
  explanation: AnalyticalExplanation;
}

export interface PortfolioRiskProfile {
  highest_risk: string;
  count_low: number;
  count_medium: number;
  count_high: number;
}

export interface RecommendationConflict {
  resource_id: string;
  resource_name?: string | null;
  recommendation_ids: string[];
  titles: string[];
  reason: string;
}

export interface RecommendationDependency {
  dependent_recommendation_id: string;
  prerequisite_recommendation_id: string;
  dependency_type: 'REQUIRED_DEPENDENCY' | 'RECOMMENDED_PRECAUTION';
  reason: string;
}

export interface PortfolioAnalysisResult {
  total_opportunities_count: number;
  total_recommendations_count: number;
  conflicts: RecommendationConflict[];
  dependencies: RecommendationDependency[];
  compatible_recommendations_count: number;
  total_compatible_monthly_savings: string | number;
  total_compatible_annual_savings: string | number;
  risk_profile: PortfolioRiskProfile;
  complexity_breakdown: Record<string, number>;
  reversibility_breakdown: Record<string, number>;
  explanation: AnalyticalExplanation;
}

export interface ScenarioConstraintViolation {
  rule_name: string;
  resource_id?: string | null;
  reason: string;
  severity: string;
}

export interface ScenarioChangeCalculation {
  resource_id?: string | null;
  resource_name?: string | null;
  change_type: string;
  current_spec: string;
  proposed_spec: string;
  current_monthly_cost: string | number;
  projected_monthly_cost: string | number;
  delta_cost: string | number;
  risk_level: string;
  complexity_level: string;
  assumptions: Record<string, any>;
}

export interface ScenarioSimulationResult {
  scenario_id?: string | null;
  name: string;
  scenario_type: 'CONSERVATIVE' | 'AGGRESSIVE' | 'MODERNIZATION' | 'CUSTOM';
  description?: string | null;
  baseline_monthly_cost: string | number;
  projected_monthly_cost: string | number;
  monthly_savings: string | number;
  annual_savings: string | number;
  percentage_savings: string | number;
  performance_risk: string;
  reliability_risk: string;
  complexity_level: string;
  assumptions: Record<string, any>;
  changes: ScenarioChangeCalculation[];
  violations: ScenarioConstraintViolation[];
  is_valid: boolean;
  explanation: AnalyticalExplanation;
}

export interface AnalyticsTrendsResponse {
  trends: TrendAnalysisResult;
}

export interface AnalyticsDriversResponse {
  drivers: DriverDecompositionResult;
}

export interface AnalyticsConcentrationResponse {
  concentration: ConcentrationMetrics;
}

export interface AnalyticsEfficiencyResponse {
  efficiency: EfficiencyReport;
}

export interface AnalyticsPortfolioResponse {
  portfolio: PortfolioAnalysisResult;
}

export interface AnalyticsSummaryResponse {
  trends: TrendAnalysisResult;
  drivers: DriverDecompositionResult;
  concentration: ConcentrationMetrics;
  efficiency: EfficiencyReport;
  portfolio: PortfolioAnalysisResult;
  scenarios: ScenarioSimulationResult[];
  chain_summary: Record<string, any>;
}

// ==========================================
// Phase 7 — AWS Integration & Sync Types
// ==========================================

export type PermissionStatus = 'AVAILABLE' | 'DENIED' | 'NOT_CONFIGURED';

export interface AWSServicePermissions {
  cost_aggregated: PermissionStatus;
  cost_resource_level: PermissionStatus;
  ec2_inventory: PermissionStatus;
  ebs_inventory: PermissionStatus;
  rds_inventory: PermissionStatus;
  s3_inventory: PermissionStatus;
  eks_inventory: PermissionStatus;
  cloudwatch_telemetry?: PermissionStatus;
}

export interface IntegrationItemResponse {
  id: string;
  provider_type: string;
  status: 'NOT_CONFIGURED' | 'CONFIGURED' | 'VALIDATING' | 'CONNECTED' | 'SYNCING' | 'SYNCED' | 'PARTIAL' | 'ERROR' | 'DISCONNECTED';
  auth_method: string;
  role_arn_masked?: string | null;
  regions: string[];
  account_name?: string | null;
  last_sync_at?: string | null;
  created_at: string;
}

export interface AWSValidationResponse {
  is_valid: boolean;
  account_id?: string | null;
  region?: string | null;
  role_arn_masked?: string | null;
  permissions: AWSServicePermissions;
  error_message?: string | null;
}

export interface SyncJobItemResponse {
  id: string;
  integration_id: string;
  account_id?: string | null;
  job_type: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL' | 'ERROR';
  started_at?: string | null;
  completed_at?: string | null;
  records_synced: number;
  error_message?: string | null;
}

export interface IntegrationStatusResponse {
  integration: IntegrationItemResponse;
  permissions: AWSServicePermissions;
  last_sync_job?: SyncJobItemResponse | null;
  is_fresh: boolean;
  freshness_description: string;
}

export interface SyncTriggerResponse {
  sync_job_id: string;
  status: string;
  account_id?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  resources_discovered: number;
  resources_created: number;
  resources_updated: number;
  cost_records_processed: number;
  cost_records_created: number;
  cost_records_updated: number;
  warnings: string[];
  error_message?: string | null;
}

export interface AWSConfigureRequest {
  role_arn: string;
  external_id?: string | null;
  regions: string[];
  account_name?: string | null;
}

export interface AWSValidateRequest {
  role_arn?: string | null;
  external_id?: string | null;
  region?: string | null;
}

// ==========================================
// Phase 8 — Operational Telemetry & Data Quality
// ==========================================

export interface TelemetryObservationItem {
  id: string;
  timestamp: string;
  metric_name: string;
  namespace: string;
  source_statistic: string;
  value: string | number;
  unit?: string | null;
  period: number;
  dimensions_json: Record<string, any>;
}

export interface TelemetryMetricSummary {
  metric_name: string;
  namespace: string;
  unit?: string | null;
  source_statistic: string;
  observation_count: number;
  p95?: string | number | null;
  median?: string | number | null;
  mean?: string | number | null;
  min_value?: string | number | null;
  max_value?: string | number | null;
  latest_value?: string | number | null;
  latest_timestamp?: string | null;
  coverage_ratio: string | number;
  freshness_age_seconds?: number | null;
  sufficiency_status: 'AVAILABLE' | 'INSUFFICIENT_DATA' | 'NOT_CONFIGURED' | 'NOT_APPLICABLE';
}

export interface ResourceTelemetryResponse {
  resource_id: string;
  resource_name?: string | null;
  native_id?: string | null;
  service_name: string;
  resource_type: string;
  window_days: number;
  metrics: Record<string, TelemetryMetricSummary>;
  recent_observations: TelemetryObservationItem[];
}

export interface IntegrationTelemetryStatusResponse {
  integration_id: string;
  cloudwatch_permission_status: string;
  telemetry_enabled: boolean;
  total_resources_tracked: number;
  resources_with_telemetry: number;
  overall_coverage_pct: string | number;
  last_telemetry_sync?: string | null;
  supported_namespaces: string[];
}

export interface AccountDataQualityItem {
  account_id: string;
  account_name: string;
  total_resources: number;
  resources_with_telemetry: number;
  telemetry_coverage_pct: string | number;
  total_observations: number;
}

export interface DataQualityReportResponse {
  organization_id: string;
  generated_at: string;
  total_accounts: number;
  total_resources: number;
  resources_with_telemetry: number;
  telemetry_coverage_pct: string | number;
  total_observations: number;
  accounts_quality: AccountDataQualityItem[];
  metrics_breakdown: Record<string, number>;
  data_trustworthiness_status: 'TRUSTED' | 'LIMITED_TELEMETRY' | 'NO_OPERATIONAL_DATA';
  epistemic_guarantee: string;
}

// ==========================================
// PHASE 9 - AI EXPLANATION ENGINE TYPES
// ==========================================

export type EpistemicClass =
  | 'OBSERVED'
  | 'DERIVED'
  | 'INFERRED'
  | 'ASSUMED'
  | 'PROJECTED'
  | 'NOT_AVAILABLE';

export type QuestionCategory =
  | 'SPEND_OVERVIEW'
  | 'SPEND_CHANGE'
  | 'COST_DRIVER'
  | 'ANOMALY'
  | 'OPTIMIZATION'
  | 'RESOURCE'
  | 'TELEMETRY'
  | 'SCENARIO'
  | 'FORECAST'
  | 'ACCOUNT'
  | 'SERVICE'
  | 'GENERAL_ATLAS'
  | 'UNSUPPORTED';

export type ScopeType =
  | 'DASHBOARD'
  | 'SERVICE'
  | 'ACCOUNT'
  | 'RESOURCE'
  | 'RECOMMENDATION'
  | 'SCENARIO';

export type AIResponseStatus =
  | 'COMPLETED'
  | 'VALIDATION_FAILED'
  | 'PROVIDER_ERROR'
  | 'DISABLED'
  | 'RATE_LIMITED';

export interface NumericClaim {
  value: number;
  unit: string;
  evidence_id: string;
  description?: string | null;
}

export interface AIConclusion {
  statement: string;
  epistemic_class: EpistemicClass;
  evidence_ids: string[];
  numeric_claims: NumericClaim[];
}

export interface AICitation {
  id: string;
  title: string;
  entity_type: 'RESOURCE' | 'RECOMMENDATION' | 'COST' | 'ANOMALY' | 'SCENARIO';
  entity_id: string;
  link_path: string;
  description?: string | null;
}

export interface DataFreshness {
  cloudwatch_retrieved_at?: string | null;
  cost_data_through?: string | null;
  resource_inventory_synced_at?: string | null;
  status: 'FRESH' | 'STALE' | 'UNKNOWN';
  freshness_summary: string;
}

export interface AIAnswer {
  summary: string;
  answer: string;
  conclusions: AIConclusion[];
  limitations: string[];
  recommended_next_steps: string[];
  cited_entities: AICitation[];
  epistemic_notes: string[];
  freshness_note?: string | null;
}

export interface AIAskRequest {
  question: string;
  scope_type?: ScopeType;
  scope_id?: string | null;
  session_id?: string | null;
}

export interface AIAskResponse {
  interaction_id: string;
  session_id: string;
  status: AIResponseStatus;
  question: string;
  scope_type: ScopeType;
  scope_id?: string | null;
  answer?: AIAnswer | null;
  evidence_hash: string;
  evidence_count: number;
  evidence_ids: string[];
  data_freshness: DataFreshness;
  latency_ms: number;
  token_count: number;
  estimated_cost_usd: number | string;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface AIStatusResponse {
  ai_enabled: boolean;
  provider: string;
  model: string;
  max_context_tokens: number;
  max_output_tokens: number;
  rate_limit_per_minute: number;
  system_version: string;
  prompt_version: string;
  is_offline_capable: boolean;
}

export interface AIInteractionDetailResponse {
  id: string;
  organization_id: string;
  session_id: string;
  question: string;
  question_category: string;
  scope_type: string;
  scope_id?: string | null;
  provider: string;
  model: string;
  prompt_version: string;
  context_version: string;
  evidence_hash: string;
  evidence_ids: string[];
  response_status: string;
  answer_json?: any;
  sanitized_evidence_preview?: {
    scope_type?: string;
    scope_id?: string | null;
    evidence_count?: number;
    items_sample?: Array<{
      id: string;
      type: string;
      epistemic_class: EpistemicClass;
      statement: string;
      value?: number | null;
      unit?: string | null;
      source: string;
      source_entity_id?: string | null;
      confidence?: number | null;
      period_or_timestamp?: string | null;
      metadata?: Record<string, any>;
    }>;
    note?: string;
  } | null;
  latency_ms: number;
  input_token_count: number;
  output_token_count: number;
  estimated_cost_usd: number | string;
  evidence_count: number;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
}



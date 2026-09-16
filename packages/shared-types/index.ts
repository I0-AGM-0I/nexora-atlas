/**
 * NEXORA ATLAS - Shared Cross-Tier Type Definitions
 */

export type ProviderType = 'AWS' | 'AZURE' | 'GCP';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type RecommendationStatus = 'OPEN' | 'IN_REVIEW' | 'SIMULATED' | 'DISMISSED';

export interface MetaResponse {
  api_version: string;
  environment: string;
  demo_mode: boolean;
  service_name: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  database: 'connected' | 'disconnected';
  database_type: 'postgresql' | 'sqlite';
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  };
}

export interface DateRangeFilter {
  start_date: string;
  end_date: string;
}

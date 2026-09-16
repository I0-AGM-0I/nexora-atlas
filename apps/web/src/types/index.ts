export type ProviderType = 'AWS' | 'AZURE' | 'GCP';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

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

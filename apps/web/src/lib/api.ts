/**
 * NEXORA ATLAS - Typed API Client
 * Provides typed asynchronous requests to the FastAPI backend.
 */

import {
  DashboardSummary,
  SpendTrendResponse,
  ServiceBreakdownResponse,
  AccountBreakdownResponse,
  RecentActivityResponse,
  SpendExplorerResponse,
  AnomalyListResponse,
  AnomalyItem,
  OptimizationOverviewResponse,
  OpportunityItem,
  ResourceListResponse,
  ResourceListItem,
  ScenarioListResponse,
  ForecastResponse,
  IntelligenceStatusResponse,
  IntelligenceRunResponse,
} from '../types/api';

function getApiBase(): string {
  if (typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null' && !window.location.origin.startsWith('blob:') && !window.location.origin.startsWith('about:')) {
    return `${window.location.origin}/api/v1`;
  }
  return 'http://127.0.0.1:8000/api/v1';
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${getApiBase()}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson?.detail) {
          errDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        } else if (errorJson?.error?.message) {
          errDetail = errorJson.error.message;
        }
      } catch {
        // Fallback to status text
      }
      throw new Error(errDetail);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    console.error(`API request error on ${url}:`, err);
    throw err;
  }
}

export const api = {
  // Dashboard
  getDashboardSummary: (orgSlug?: string): Promise<DashboardSummary> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<DashboardSummary>(`/dashboard/summary${q}`);
  },

  getSpendTrend: (days: number = 90, orgSlug?: string): Promise<SpendTrendResponse> => {
    const params = new URLSearchParams({ days: days.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<SpendTrendResponse>(`/dashboard/spend-trend?${params.toString()}`);
  },

  getServiceBreakdown: (days: number = 30, orgSlug?: string): Promise<ServiceBreakdownResponse> => {
    const params = new URLSearchParams({ days: days.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<ServiceBreakdownResponse>(`/dashboard/service-breakdown?${params.toString()}`);
  },

  getAccountBreakdown: (days: number = 30, orgSlug?: string): Promise<AccountBreakdownResponse> => {
    const params = new URLSearchParams({ days: days.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<AccountBreakdownResponse>(`/dashboard/account-breakdown?${params.toString()}`);
  },

  getRecentActivity: (limit: number = 8, orgSlug?: string): Promise<RecentActivityResponse> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<RecentActivityResponse>(`/dashboard/recent-activity?${params.toString()}`);
  },

  // Spend Explorer
  getSpendExplorer: (params?: {
    period_days?: number;
    account_id?: string;
    service_name?: string;
    page?: number;
    page_size?: number;
    org_slug?: string;
  }): Promise<SpendExplorerResponse> => {
    const query = new URLSearchParams();
    if (params?.period_days) query.set('period_days', params.period_days.toString());
    if (params?.account_id) query.set('account_id', params.account_id);
    if (params?.service_name) query.set('service_name', params.service_name);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.page_size) query.set('page_size', params.page_size.toString());
    if (params?.org_slug) query.set('org_slug', params.org_slug);

    const qs = query.toString();
    return request<SpendExplorerResponse>(`/spend${qs ? `?${qs}` : ''}`);
  },

  // Anomalies
  getAnomalies: (params?: {
    severity?: string;
    status?: string;
    org_slug?: string;
  }): Promise<AnomalyListResponse> => {
    const query = new URLSearchParams();
    if (params?.severity) query.set('severity', params.severity);
    if (params?.status) query.set('status', params.status);
    if (params?.org_slug) query.set('org_slug', params.org_slug);

    const qs = query.toString();
    return request<AnomalyListResponse>(`/anomalies${qs ? `?${qs}` : ''}`);
  },

  getAnomalyDetail: (id: string, orgSlug?: string): Promise<AnomalyItem> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<AnomalyItem>(`/anomalies/${id}${q}`);
  },

  // Optimization
  getOptimization: (params?: {
    category?: string;
    severity?: string;
    status?: string;
    org_slug?: string;
  }): Promise<OptimizationOverviewResponse> => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.severity) query.set('severity', params.severity);
    if (params?.status) query.set('status', params.status);
    if (params?.org_slug) query.set('org_slug', params.org_slug);

    const qs = query.toString();
    return request<OptimizationOverviewResponse>(`/optimization${qs ? `?${qs}` : ''}`);
  },

  getOpportunityDetail: (id: string, orgSlug?: string): Promise<OpportunityItem> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<OpportunityItem>(`/optimization/${id}${q}`);
  },

  // Resources
  getResources: (params?: {
    search?: string;
    account_id?: string;
    region?: string;
    service_name?: string;
    status?: string;
    page?: number;
    page_size?: number;
    org_slug?: string;
  }): Promise<ResourceListResponse> => {
    const query = new URLSearchParams();
    if (params?.search) query.set('search', params.search);
    if (params?.account_id) query.set('account_id', params.account_id);
    if (params?.region) query.set('region', params.region);
    if (params?.service_name) query.set('service_name', params.service_name);
    if (params?.status) query.set('status', params.status);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.page_size) query.set('page_size', params.page_size.toString());
    if (params?.org_slug) query.set('org_slug', params.org_slug);

    const qs = query.toString();
    return request<ResourceListResponse>(`/resources${qs ? `?${qs}` : ''}`);
  },

  getResourceDetail: (id: string, orgSlug?: string): Promise<ResourceListItem> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<ResourceListItem>(`/resources/${id}${q}`);
  },

  // Scenarios
  getScenarios: (orgSlug?: string): Promise<ScenarioListResponse> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<ScenarioListResponse>(`/scenarios${q}`);
  },

  // Forecast
  getForecast: (orgSlug?: string): Promise<ForecastResponse> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<ForecastResponse>(`/forecast${q}`);
  },

  // Intelligence Engine
  getIntelligenceStatus: (orgSlug?: string): Promise<IntelligenceStatusResponse> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<IntelligenceStatusResponse>(`/intelligence/status${q}`);
  },

  runIntelligenceAnalysis: (orgSlug?: string): Promise<IntelligenceRunResponse> => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<IntelligenceRunResponse>(`/intelligence/run${q}`, { method: 'POST' });
  },

  // Phase 6 — Advanced Analytics & Optimization Modeling
  getAnalyticsTrends: (window: number = 30, orgSlug?: string) => {
    const params = new URLSearchParams({ window: window.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').AnalyticsTrendsResponse>(`/analytics/trends?${params.toString()}`);
  },

  getAnalyticsDrivers: (window: number = 30, orgSlug?: string) => {
    const params = new URLSearchParams({ window: window.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').AnalyticsDriversResponse>(`/analytics/drivers?${params.toString()}`);
  },

  getAnalyticsConcentration: (window: number = 30, orgSlug?: string) => {
    const params = new URLSearchParams({ window: window.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').AnalyticsConcentrationResponse>(`/analytics/concentration?${params.toString()}`);
  },

  getAnalyticsEfficiency: (orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').AnalyticsEfficiencyResponse>(`/analytics/efficiency${q}`);
  },

  getAnalyticsPortfolio: (orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').AnalyticsPortfolioResponse>(`/analytics/portfolio${q}`);
  },

  getAnalyticsSummary: (window: number = 30, orgSlug?: string) => {
    const params = new URLSearchParams({ window: window.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').AnalyticsSummaryResponse>(`/analytics/summary?${params.toString()}`);
  },

  simulateScenario: (payload: {
    name: string;
    scenario_type?: string;
    description?: string;
    baseline_monthly_cost?: number;
    proposed_changes: any[];
    custom_assumptions?: Record<string, any>;
    orgSlug?: string;
  }) => {
    const q = payload.orgSlug ? `?org_slug=${encodeURIComponent(payload.orgSlug)}` : '';
    return request<import('../types/api').ScenarioSimulationResult>(`/scenarios/simulate${q}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Phase 7 — Cloud Integrations
  getIntegrations: (orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').IntegrationItemResponse[]>(`/integrations${q}`);
  },

  getIntegration: (integrationId: string, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').IntegrationItemResponse>(`/integrations/${encodeURIComponent(integrationId)}${q}`);
  },

  configureAWSIntegration: (payload: import('../types/api').AWSConfigureRequest, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').IntegrationItemResponse>(`/integrations/aws/configure${q}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  validateAWSConnection: (payload: import('../types/api').AWSValidateRequest, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').AWSValidationResponse>(`/integrations/aws/validate${q}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  triggerAWSSync: (integrationId: string, orgSlug?: string) => {
    const params = new URLSearchParams({ integration_id: integrationId });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').SyncTriggerResponse>(`/integrations/aws/sync?${params.toString()}`, {
      method: 'POST',
    });
  },

  getSyncJobs: (integrationId: string, limit: number = 20, orgSlug?: string) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').SyncJobItemResponse[]>(`/integrations/${encodeURIComponent(integrationId)}/sync-jobs?${params.toString()}`);
  },

  getIntegrationStatus: (integrationId: string, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').IntegrationStatusResponse>(`/integrations/${encodeURIComponent(integrationId)}/status${q}`);
  },

  // Phase 8 — Operational Telemetry & Data Quality
  getResourceTelemetry: (resourceId: string, days: number = 30, orgSlug?: string) => {
    const params = new URLSearchParams({ days: days.toString() });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').ResourceTelemetryResponse>(`/resources/${encodeURIComponent(resourceId)}/telemetry?${params.toString()}`);
  },

  getIntegrationTelemetryStatus: (integrationId: string, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').IntegrationTelemetryStatusResponse>(`/integrations/${encodeURIComponent(integrationId)}/telemetry/status${q}`);
  },

  triggerTelemetrySync: (integrationId: string, orgSlug?: string) => {
    const params = new URLSearchParams({ integration_id: integrationId });
    if (orgSlug) params.set('org_slug', orgSlug);
    return request<import('../types/api').SyncTriggerResponse>(`/integrations/aws/telemetry-sync?${params.toString()}`, {
      method: 'POST',
    });
  },

  getDataQualityReport: (orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').DataQualityReportResponse>(`/analytics/data-quality${q}`);
  },

  // Phase 9 — AI Explanation & Natural Language Intelligence
  askAtlas: (req: import('../types/api').AIAskRequest, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').AIAskResponse>(`/ai/ask${q}`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  getAIStatus: () => {
    return request<import('../types/api').AIStatusResponse>('/ai/status');
  },

  getAIInteraction: (interactionId: string, orgSlug?: string) => {
    const q = orgSlug ? `?org_slug=${encodeURIComponent(orgSlug)}` : '';
    return request<import('../types/api').AIInteractionDetailResponse>(`/ai/interactions/${encodeURIComponent(interactionId)}${q}`);
  },
};




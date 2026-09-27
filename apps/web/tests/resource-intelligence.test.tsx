import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ResourceDetailPage } from '../src/pages/ResourceDetailPage';
import { InvestigationProvider } from '../src/lib/InvestigationContext';
import { AskAtlasProvider } from '../src/lib/AskAtlasContext';
import type {
  ResourceListItem,
  ResourceTelemetryResponse,
  OptimizationOverviewResponse,
  AnomalyListResponse,
} from '../src/types/api';

vi.mock('../src/lib/api', () => ({
  api: {
    getResourceDetail: vi.fn(),
    getResourceTelemetry: vi.fn(),
    getOptimization: vi.fn(),
    getAnomalies: vi.fn(),
    getAnomalyDetail: vi.fn(),
    getSpendTrend: vi.fn(),
    getServiceBreakdown: vi.fn(),
    getAccountBreakdown: vi.fn(),
    getRecentActivity: vi.fn(),
    getDashboardSummary: vi.fn(),
  },
}));

import { api } from '../src/lib/api';

const mockResourceFull: ResourceListItem = {
  id: 'res-eks-worker-001',
  account_id: '111222333444',
  account_name: 'Production AWS Account',
  region_code: 'ap-south-1',
  native_id: 'i-0eks-node-m5-4x-01',
  name: 'analytics-eks-worker-pool-01',
  service_name: 'AmazonEC2',
  resource_type: 'm5.4xlarge',
  status: 'RUNNING',
  tags: {
    Cluster: 'analytics-eks-cluster',
    Workload: 'batch-analytics',
    Environment: 'production',
    AvailabilityZone: 'ap-south-1a',
  },
  cost_30d: '142000.00',
};

const mockTelemetryFull: ResourceTelemetryResponse = {
  resource_id: 'res-eks-worker-001',
  service_name: 'AmazonEC2',
  resource_type: 'm5.4xlarge',
  window_days: 30,
  metrics: {
    CPUUtilization: {
      metric_name: 'CPUUtilization',
      namespace: 'AWS/EC2',
      source_statistic: 'Average',
      observation_count: 8640,
      p95: 11.2,
      mean: 8.5,
      coverage_ratio: 0.95,
      sufficiency_status: 'AVAILABLE',
    },
  },
  recent_observations: [],
};

const mockOptimizationMultiRec: OptimizationOverviewResponse = {
  potential_monthly_savings: '307000.00',
  potential_annual_savings: '3684000.00',
  opportunity_count: 1,
  recommendation_count: 2,
  opportunities: [
    {
      id: 'opp-eks-oversized-01',
      account_id: '111222333444',
      account_name: 'Production AWS Account',
      resource_id: 'res-eks-worker-001',
      category: 'COMPUTE',
      waste_type: 'OVERSIZED_INSTANCE',
      severity: 'HIGH',
      status: 'OPEN',
      estimated_waste_monthly: '142000.00',
      estimated_waste_annual: '1704000.00',
      evidence_json: {},
      recommendations: [
        {
          id: 'rec-downsize-m5l',
          opportunity_id: 'opp-eks-oversized-01',
          title: 'Downsize EKS Node Group to m5.large',
          category: 'COMPUTE',
          current_configuration: '6x m5.4xlarge (16 vCPU, 64 GB RAM)',
          recommended_configuration: '6x m5.large (2 vCPU, 8 GB RAM)',
          estimated_monthly_savings: '142000.00',
          estimated_annual_savings: '1704000.00',
          confidence_pct: '94.00',
          risk_level: 'LOW',
          reasoning: 'Cluster metrics show sustained 30-day peak demand under 12 vCPU aggregate across all nodes.',
        },
        {
          id: 'rec-migrate-arm',
          opportunity_id: 'opp-eks-oversized-01',
          title: 'Migrate Node Group to Graviton c7g.xlarge',
          category: 'COMPUTE',
          current_configuration: '6x m5.4xlarge (16 vCPU, 64 GB RAM, x86)',
          recommended_configuration: '6x c7g.xlarge (4 vCPU, 8 GB RAM, ARM64)',
          estimated_monthly_savings: '165000.00',
          estimated_annual_savings: '1980000.00',
          confidence_pct: '82.00',
          risk_level: 'MEDIUM',
          reasoning: 'ARM64 Graviton instances offer superior price/performance.',
        },
      ],
    },
  ],
};

const mockAnomalies: AnomalyListResponse = {
  items: [
    {
      id: 'anom-eks-surge',
      account_id: '111222333444',
      account_name: 'Production AWS Account',
      resource_id: 'res-eks-worker-001',
      resource_native_id: 'i-0eks-node-m5-4x-01',
      service_name: 'AmazonEC2',
      observed: {
        observed_cost: '142000.00',
        baseline_cost: '95000.00',
        percentage_change: '49.47',
        detected_at: '2026-09-14T08:30:00Z',
        detection_rule: 'ROLLING_ZSCORE_EXCEEDED',
        observed_metrics_json: {},
      },
      inference: {
        severity: 'HIGH',
        status: 'OPEN',
        inferred_cause: 'Node count expansion due to unindexed query retry queue backpressure.',
        confidence_pct: '90.00',
        inference_details_json: {},
      },
    },
  ],
  total_count: 1,
  open_count: 1,
};

describe('Resource Intelligence Diagnostic Surface (ResourceDetailPage)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getResourceDetail as any).mockResolvedValue(mockResourceFull);
    (api.getResourceTelemetry as any).mockResolvedValue(mockTelemetryFull);
    (api.getOptimization as any).mockResolvedValue(mockOptimizationMultiRec);
    (api.getAnomalies as any).mockResolvedValue(mockAnomalies);
  });

  it('renders authoritative resource header and state strip with evidence-backed cells', async () => {
    render(
      <MemoryRouter initialEntries={['/resources/res-eks-worker-001']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/resources/:id" element={<ResourceDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Wait for resource to load
    await waitFor(() => {
      expect(screen.getAllByText('analytics-eks-worker-pool-01').length).toBeGreaterThanOrEqual(1);
    });

    // 1. Authoritative Header elements
    expect(screen.getByText('PROVIDER: AWS')).toBeInTheDocument();
    expect(screen.getByText('RUNNING')).toBeInTheDocument();
    expect(screen.getAllByText(/i-0eks-node-m5-4x-01/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/m5\.4xlarge/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/ap-south-1/i).length).toBeGreaterThanOrEqual(1);

    // 2. Resource State Strip
    expect(screen.getByText('COST')).toBeInTheDocument();
    expect(screen.getByText('ACTIVITY')).toBeInTheDocument();
    expect(screen.getByText('LOW UTILIZATION')).toBeInTheDocument();
    expect(screen.getByText('95% COVERAGE')).toBeInTheDocument();
    expect(screen.getByText('OPPORTUNITY')).toBeInTheDocument();

    // 3. What It Is Section
    expect(screen.getByText(/01 · WHAT IT IS · AUTHORITATIVE CONFIGURATION/i)).toBeInTheDocument();
    expect(screen.getByText(/Cluster:/i)).toBeInTheDocument();
    expect(screen.getByText('analytics-eks-cluster')).toBeInTheDocument();

    // 4. What It Costs Section
    expect(screen.getByText(/02 · WHAT IT COSTS · FINANCIAL DECOMPOSITION/i)).toBeInTheDocument();
    expect(screen.getByText(/DAILY RUN RATE/i)).toBeInTheDocument();
    expect(screen.getByText('MONTHLY RUN RATE')).toBeInTheDocument();
    expect(screen.getByText(/ANNUALIZED PROJECTION/i)).toBeInTheDocument();

    // 5. How It Behaves Section
    expect(screen.getByText(/03 · HOW IT BEHAVES · OPERATIONAL TELEMETRY/i)).toBeInTheDocument();
    expect(screen.getByText(/CPU UTILIZATION \(P95\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/11\.2%/i).length).toBeGreaterThanOrEqual(1);

    // 6. Telemetry Sufficiency explanation (guest memory missing on EC2)
    expect(screen.getByText(/MEMORY TELEMETRY · NOT CONFIGURED/i)).toBeInTheDocument();
    expect(screen.getByText(/CloudWatch Agent installation is required/i)).toBeInTheDocument();

    // 7. Atlas Observes Evidence Layer
    expect(screen.getByText(/04 · ATLAS OBSERVES · EMPIRICAL EVIDENCE & CALCULATED HEADROOM/i)).toBeInTheDocument();
    expect(screen.getByText(/88\.8% Headroom/i)).toBeInTheDocument();

    // 8. Atlas Assessment with epistemic ordering
    expect(screen.getByText(/05 · ATLAS ASSESSMENT · DETERMINISTIC INTERPRETATION/i)).toBeInTheDocument();
    expect(screen.getByText(/1\. \[OBSERVED\]/i)).toBeInTheDocument();
    expect(screen.getByText(/2\. \[DERIVED\]/i)).toBeInTheDocument();
    expect(screen.getByText(/3\. \[INFERRED\]/i)).toBeInTheDocument();

    // Verify Read-Only boundary: NO mutation controls present
    expect(screen.queryByRole('button', { name: /^APPLY$/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /^EXECUTE$/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /^SCALE$/i })).toBeNull();
  });

  it('renders multiple candidate recommendations as alternatives and allows switching', async () => {
    render(
      <MemoryRouter initialEntries={['/resources/res-eks-worker-001']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/resources/:id" element={<ResourceDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/EXPLORE CANDIDATE ALTERNATIVES \(2 OPTIONS EVALUATED\)/i)).toBeInTheDocument();
    });

    // Both candidate recommendations should be visible as selectable alternatives
    expect(screen.getAllByText('Downsize EKS Node Group to m5.large').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Migrate Node Group to Graviton c7g.xlarge')).toBeInTheDocument();
    expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM RISK')).toBeInTheDocument();

    // Initially option 1 is selected
    expect(screen.getByText('6x m5.large (2 vCPU, 8 GB RAM)')).toBeInTheDocument();

    // Click option 2
    fireEvent.click(screen.getByText('Migrate Node Group to Graviton c7g.xlarge'));

    // Option 2 recommended configuration should now be active
    await waitFor(() => {
      expect(screen.getByText('6x c7g.xlarge (4 vCPU, 8 GB RAM, ARM64)')).toBeInTheDocument();
    });

    // Decision handoff button exists
    expect(screen.getByRole('button', { name: /VIEW OPTIMIZATION DECISION/i })).toBeInTheDocument();
  });

  it('renders graceful fallback when resource is not found', async () => {
    (api.getResourceDetail as any).mockRejectedValue(new Error('Resource res-unknown does not exist'));

    render(
      <MemoryRouter initialEntries={['/resources/res-unknown']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/resources/:id" element={<ResourceDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/RESOURCE NOT FOUND/i)).toBeInTheDocument();
    });
  });

  it('renders graceful fallback when no optimization opportunity exists', async () => {
    (api.getOptimization as any).mockResolvedValue({ opportunities: [] });

    render(
      <MemoryRouter initialEntries={['/resources/res-eks-worker-001']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/resources/:id" element={<ResourceDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/NO CURRENT OPTIMIZATION OPPORTUNITY/i)).toBeInTheDocument();
    });
  });

  it('renders Trace Back button and navigates to investigation when anomaly is correlated', async () => {
    render(
      <MemoryRouter initialEntries={['/resources/res-eks-worker-001']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/resources/:id" element={<ResourceDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/INVESTIGATION CONTEXT ACTIVE/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /WHY IS ATLAS SHOWING THIS\? ← TRACE BACK/i })).toBeInTheDocument();
    });
  });
});

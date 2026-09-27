import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { InvestigationTrace } from '../src/components/investigation/InvestigationTrace';
import { ChangesPage } from '../src/pages/ChangesPage';
import { InvestigationProvider } from '../src/lib/InvestigationContext';
import { AskAtlasProvider } from '../src/lib/AskAtlasContext';
import type { AnomalyItem } from '../src/types/api';

// Mock API module
vi.mock('../src/lib/api', () => ({
  api: {
    getAnomalies: vi.fn(),
    getAnomalyDetail: vi.fn(),
    getResourceDetail: vi.fn(),
    getOptimization: vi.fn(),
    getOpportunityDetail: vi.fn(),
    getSpendTrend: vi.fn(),
    getServiceBreakdown: vi.fn(),
    getAccountBreakdown: vi.fn(),
    getRecentActivity: vi.fn(),
    getDashboardSummary: vi.fn(),
  },
}));

import { api } from '../src/lib/api';

const mockAnomalyFull: AnomalyItem = {
  id: 'anom-ec2-surge-001',
  account_id: 'acc-prod-111',
  account_name: 'Production AWS',
  service_name: 'AmazonEC2',
  resource_id: 'res-ec2-001',
  resource_name: 'api-gateway-core-pool',
  resource_native_id: 'i-0a1b2c3d4e5f0001',
  observed: {
    observed_cost: '470000.00',
    baseline_cost: '340000.00',
    percentage_change: '38.24',
    detected_at: '2026-09-15T08:30:00Z',
    detection_rule: 'ROLLING_ZSCORE_EXCEEDED',
    observed_metrics_json: {
      observed_compute_hours: 2880,
      baseline_compute_hours: 2080,
      scaling_trigger: 'alb_request_count_per_target',
      sample_window_days: 14,
    },
  },
  inference: {
    severity: 'HIGH',
    status: 'OPEN',
    inferred_cause: 'Increased compute hours correlated with unindexed database query retry storms in production API tier.',
    confidence_pct: '91.50',
    inference_details_json: {
      correlated_service: 'AmazonRDS',
      affected_instance_types: ['m5.2xlarge'],
      algorithm: 'IQR_DEVIATION_DETECTOR',
      recommendation_link: 'opp-eks-oversized',
    },
  },
};

const mockAnomalyMinimal: AnomalyItem = {
  id: 'anom-minimal-002',
  account_id: 'acc-prod-111',
  account_name: 'Production AWS',
  service_name: 'AmazonRDS',
  resource_id: null,
  resource_name: null,
  resource_native_id: null,
  observed: {
    observed_cost: '50000.00',
    baseline_cost: '30000.00',
    percentage_change: '66.67',
    detected_at: '2026-09-14T10:00:00Z',
    detection_rule: 'THRESHOLD_MULTIPLIER_2X',
    observed_metrics_json: null,
  },
  inference: {
    severity: 'MEDIUM',
    status: 'OPEN',
    inferred_cause: null,
    confidence_pct: '80.00',
    inference_details_json: null,
  },
};

describe('InvestigationTrace Component & 5-Stage Causal Chain', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getResourceDetail as any).mockResolvedValue({
      id: 'res-ec2-001',
      native_id: 'i-0a1b2c3d4e5f0001',
      name: 'api-gateway-core-pool',
      resource_type: 'm5.2xlarge',
      service_name: 'AmazonEC2',
      account_name: 'Production AWS',
      region_code: 'ap-south-1',
      status: 'RUNNING',
      cost_30d: '470000.00',
      tags: { Workload: 'api-gateway' },
    });
    (api.getOptimization as any).mockResolvedValue({
      opportunities: [
        {
          id: 'opp-eks-oversized',
          account_id: 'acc-prod-111',
          account_name: 'Production AWS',
          resource_id: 'res-ec2-001',
          category: 'COMPUTE',
          waste_type: 'OVERSIZED_INSTANCE',
          severity: 'HIGH',
          status: 'OPEN',
          estimated_waste_monthly: '142000.00',
          estimated_waste_annual: '1704000.00',
          evidence_json: {},
          recommendations: [
            {
              id: 'rec-001',
              opportunity_id: 'opp-eks-oversized',
              title: 'Downsize API Gateway Worker Pool to m5.xlarge',
              category: 'COMPUTE',
              current_configuration: '6x m5.2xlarge (8 vCPU, 32 GB RAM)',
              recommended_configuration: '6x m5.xlarge (4 vCPU, 16 GB RAM)',
              estimated_monthly_savings: '142000.00',
              estimated_annual_savings: '1704000.00',
              confidence_pct: '94.00',
              risk_level: 'LOW',
              reasoning: 'Sustained peak utilization remains under 45% during peak hours.',
            },
          ],
        },
      ],
      opportunity_count: 1,
      recommendation_count: 1,
      potential_monthly_savings: '142000.00',
      potential_annual_savings: '1704000.00',
    });
  });

  it('renders all 5 causal stages with populated evidence and epistemic badges', async () => {
    const handleClose = vi.fn();

    render(
      <MemoryRouter>
        <InvestigationProvider>
          <AskAtlasProvider>
            <InvestigationTrace anomaly={mockAnomalyFull} onClose={handleClose} />
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Stage 01: Cost Change
    expect(screen.getByText(/STAGE 01 · COST CHANGE/i)).toBeInTheDocument();
    expect(screen.getByText(/\+38\.2% vs baseline/i)).toBeInTheDocument();
    expect(screen.getAllByText(/ROLLING_ZSCORE_EXCEEDED/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/91\.5%/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole('button', { name: /VIEW IN SPEND EXPLORER/i })).toBeInTheDocument();

    // Stage 02: Cost Driver
    expect(screen.getByText(/STAGE 02 · COST DRIVER/i)).toBeInTheDocument();
    expect(screen.getByText(/Auto-Scaling Expansion \(alb_request_count_per_target\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/2880 hrs/i).length).toBeGreaterThanOrEqual(1);

    // Stage 03: Resources
    expect(screen.getByText(/STAGE 03 · PROVISIONED RESOURCES/i)).toBeInTheDocument();
    expect(screen.getByText(/i-0a1b2c3d4e5f0001/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /VIEW RESOURCE INTELLIGENCE/i })).toBeInTheDocument();

    // Stage 04: Telemetry Evidence Layer
    expect(screen.getByText(/STAGE 04 · OPERATIONAL TELEMETRY & CLOUDWATCH EVIDENCE/i)).toBeInTheDocument();
    expect(screen.getByText(/Telemetric Signals & Statistical Basis/i)).toBeInTheDocument();

    // Stage 05: Recommendation & Decision
    await waitFor(() => {
      expect(screen.getByText(/STAGE 05 · ACTIONABLE RECOMMENDATION & DECISION/i)).toBeInTheDocument();
      expect(screen.getByText(/Downsize API Gateway Worker Pool to m5.xlarge/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /VIEW OPTIMIZATION DECISION/i })).toBeInTheDocument();
    });

    // Verify Read-Only boundary: NO execution controls present
    expect(screen.queryByRole('button', { name: /^APPLY$/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /^EXECUTE$/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /^SCALE$/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /^DELETE$/i })).toBeNull();
  });

  it('renders graceful epistemic fallbacks when driver and recommendation are absent', async () => {
    (api.getOptimization as any).mockResolvedValue({
      opportunities: [],
      opportunity_count: 0,
      recommendation_count: 0,
      potential_monthly_savings: '0',
      potential_annual_savings: '0',
    });

    render(
      <MemoryRouter>
        <InvestigationProvider>
          <AskAtlasProvider>
            <InvestigationTrace anomaly={mockAnomalyMinimal} />
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Stage 02: Driver Not Established
    expect(screen.getByText(/DRIVER NOT ESTABLISHED · INSUFFICIENT EVIDENCE/i)).toBeInTheDocument();

    // Stage 03: Resource Unresolved
    expect(screen.getByText(/RESOURCE ATTRIBUTION UNRESOLVED · CLOUD METRIC ONLY/i)).toBeInTheDocument();

    // Stage 05: Recommendation Pending
    await waitFor(() => {
      expect(screen.getByText(/RECOMMENDATION PENDING FURTHER OBSERVATION · INSUFFICIENT EVIDENCE/i)).toBeInTheDocument();
    });
  });

  it('handles Escape key to trigger onClose', () => {
    const handleClose = vi.fn();

    render(
      <MemoryRouter>
        <InvestigationProvider>
          <AskAtlasProvider>
            <InvestigationTrace anomaly={mockAnomalyFull} onClose={handleClose} />
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});

describe('ChangesPage Integration & Deep-Linking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getAnomalies as any).mockResolvedValue({
      items: [mockAnomalyFull, mockAnomalyMinimal],
      total_count: 2,
      open_count: 2,
    });
    (api.getAnomalyDetail as any).mockImplementation((id: string) => {
      if (id === mockAnomalyFull.id) return Promise.resolve(mockAnomalyFull);
      if (id === mockAnomalyMinimal.id) return Promise.resolve(mockAnomalyMinimal);
      return Promise.reject(new Error('Not found'));
    });
    (api.getOptimization as any).mockResolvedValue({
      opportunities: [],
      opportunity_count: 0,
      recommendation_count: 0,
      potential_monthly_savings: '0',
      potential_annual_savings: '0',
    });
  });

  it('renders changes list and transitions into 5-stage trace upon OPEN INVESTIGATION click', async () => {
    render(
      <MemoryRouter initialEntries={['/changes']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <ChangesPage />
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Wait for list to load
    await waitFor(() => {
      expect(screen.getByText('api-gateway-core-pool')).toBeInTheDocument();
    });

    // Check dual action buttons on cards
    const openInvestigationButtons = screen.getAllByRole('button', { name: /OPEN INVESTIGATION/i });
    expect(openInvestigationButtons.length).toBeGreaterThanOrEqual(1);

    const traceTopologyButtons = screen.getAllByRole('button', { name: /TRACE IN TOPOLOGY/i });
    expect(traceTopologyButtons.length).toBeGreaterThanOrEqual(1);

    // Click OPEN INVESTIGATION on first item
    fireEvent.click(openInvestigationButtons[0]);

    // Should now display the 5-Stage Investigation Trace
    await waitFor(() => {
      expect(screen.getByText(/5-STAGE EVIDENCE & DRIVER TRACE/i)).toBeInTheDocument();
      expect(screen.getByText(/STAGE 01 · COST CHANGE/i)).toBeInTheDocument();
      expect(screen.getByText(/RETURN TO CHANGES/i)).toBeInTheDocument();
    });

    // Click RETURN TO CHANGES to step back
    const returnBtn = screen.getByRole('button', { name: /RETURN TO CHANGES/i });
    fireEvent.click(returnBtn);

    // Should return back to the list
    await waitFor(() => {
      expect(screen.getByText('api-gateway-core-pool')).toBeInTheDocument();
      expect(screen.queryByText(/5-STAGE EVIDENCE & DRIVER TRACE/i)).toBeNull();
    });
  });

  it('supports direct deep-linking via query parameter ?investigationId=...', async () => {
    render(
      <MemoryRouter initialEntries={[`/changes?investigationId=${mockAnomalyFull.id}`]}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <ChangesPage />
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Should immediately mount into InvestigationTrace mode
    await waitFor(() => {
      expect(screen.getByText(/5-STAGE EVIDENCE & DRIVER TRACE/i)).toBeInTheDocument();
      expect(screen.getByText(/STAGE 01 · COST CHANGE/i)).toBeInTheDocument();
    });
  });
});

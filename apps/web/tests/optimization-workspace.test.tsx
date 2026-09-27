import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { OptimizationPage } from '../src/pages/OptimizationPage';
import { RecommendationDetailPage } from '../src/pages/RecommendationDetailPage';
import { InvestigationProvider } from '../src/lib/InvestigationContext';
import { AskAtlasProvider } from '../src/lib/AskAtlasContext';
import type {
  OptimizationOverviewResponse,
  OpportunityItem,
  AnalyticsPortfolioResponse,
  AnalyticsConcentrationResponse,
} from '../src/types/api';

vi.mock('../src/lib/api', () => ({
  api: {
    getOptimization: vi.fn(),
    getOpportunityDetail: vi.fn(),
    getAnalyticsPortfolio: vi.fn(),
    getAnalyticsConcentration: vi.fn(),
    getDashboardSummary: vi.fn(),
    getSpendTrend: vi.fn(),
    getServiceBreakdown: vi.fn(),
    getAccountBreakdown: vi.fn(),
    getRecentActivity: vi.fn(),
    getAnomalies: vi.fn(),
    getResourceDetail: vi.fn(),
    getResourceTelemetry: vi.fn(),
  },
}));

import { api } from '../src/lib/api';

const mockOpportunityMulti: OpportunityItem = {
  id: 'opp-eks-oversized-01',
  account_id: '111222333444',
  account_name: 'Production AWS Account',
  resource_id: 'res-eks-worker-001',
  resource_name: 'analytics-eks-cluster-nodes',
  resource_native_id: 'i-0eks-node-m5-4x-01',
  category: 'COMPUTE',
  waste_type: 'OVERSIZED_INSTANCE',
  severity: 'HIGH',
  status: 'OPEN',
  estimated_waste_monthly: '142000.00',
  estimated_waste_annual: '1704000.00',
  evidence_json: {
    p95_cpu: 11.2,
    p95_memory: 18.4,
  },
  recommendations: [
    {
      id: 'rec-downsize-m5-large',
      opportunity_id: 'opp-eks-oversized-01',
      title: 'Downsize Analytics EKS Node Group to m5.large',
      category: 'COMPUTE',
      current_configuration: '6x m5.4xlarge (16 vCPU, 64 GB RAM)',
      recommended_configuration: '6x m5.large (2 vCPU, 8 GB RAM)',
      estimated_monthly_savings: '142000.00',
      estimated_annual_savings: '1704000.00',
      confidence_pct: '94.00',
      risk_level: 'LOW',
      reasoning: 'Workload memory and CPU profiles demonstrate sustained 88.8% idle headroom under peak demand.',
    },
    {
      id: 'rec-modernize-c7g-xlarge',
      opportunity_id: 'opp-eks-oversized-01',
      title: 'Migrate Analytics EKS Node Group to Graviton c7g.xlarge',
      category: 'COMPUTE',
      current_configuration: '6x m5.4xlarge (16 vCPU, 64 GB RAM, x86)',
      recommended_configuration: '6x c7g.xlarge (4 vCPU, 8 GB RAM, ARM64)',
      estimated_monthly_savings: '165000.00',
      estimated_annual_savings: '1980000.00',
      confidence_pct: '82.00',
      risk_level: 'MEDIUM',
      reasoning: 'ARM64 architecture provides superior price/performance; requires multi-arch verification.',
    },
  ],
};

const mockOptimizationOverview: OptimizationOverviewResponse = {
  potential_monthly_savings: '460000.00',
  potential_annual_savings: '5520000.00',
  opportunity_count: 7,
  recommendation_count: 8,
  opportunities: [mockOpportunityMulti],
};

const mockPortfolioResponse: AnalyticsPortfolioResponse = {
  portfolio: {
    total_opportunities_count: 7,
    total_recommendations_count: 8,
    conflicts: [
      {
        resource_id: 'res-eks-worker-001',
        resource_name: 'analytics-eks-cluster-nodes',
        recommendation_ids: ['rec-downsize-m5-large', 'rec-modernize-c7g-xlarge'],
        titles: [
          'Downsize Analytics EKS Node Group to m5.large',
          'Migrate Analytics EKS Node Group to Graviton c7g.xlarge',
        ],
        reason: 'Mutually exclusive recommendations targeting the same infrastructure resource.',
      },
    ],
    dependencies: [
      {
        dependent_recommendation_id: 'rec-dev-rds-snapshot',
        prerequisite_recommendation_id: 'rec-dev-rds-stop',
        dependency_type: 'REQUIRED_DEPENDENCY',
        reason: 'Final automated snapshot required prior to database stop.',
      },
    ],
    compatible_recommendations_count: 6,
    total_compatible_monthly_savings: '460000.00',
    total_compatible_annual_savings: '5520000.00',
    risk_profile: {
      highest_risk: 'MEDIUM',
      count_low: 5,
      count_medium: 2,
      count_high: 0,
    },
    complexity_breakdown: { LOW: 6, MEDIUM: 2, HIGH: 0 },
    reversibility_breakdown: { HIGH: 6, MEDIUM: 2, LOW: 0 },
    explanation: {
      observations: {},
      derived_metrics: {},
      evidence: ['Portfolio evaluation detects 1 mutually exclusive alternative pair on analytics-eks-cluster-nodes.'],
      method: 'PORTFOLIO_GRAPH_EVALUATION',
      parameters: {},
      assumptions: {},
      version: '1.0',
    },
  },
};

const mockConcentrationResponse: AnalyticsConcentrationResponse = {
  concentration: {
    sufficiency_status: 'AVAILABLE',
    top_1_service_share_pct: 87.2,
    top_3_service_share_pct: 98.1,
    top_5_resource_share_pct: 100.0,
    top_account_share_pct: 92.0,
    spend_concentration_index: 0.76,
    hhi_interpretation: 'HIGH',
    explanation: {
      observations: {},
      derived_metrics: {},
      evidence: ['High concentration in AmazonEC2 compute services.'],
      method: 'HERFINDAHL_HIRSCHMAN_INDEX',
      parameters: {},
      assumptions: {},
      version: '1.0',
    },
  },
};

describe('Milestone 6: Optimization Decision Workspace & Categorical Decision Factors', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getOptimization as any).mockResolvedValue(mockOptimizationOverview);
    (api.getOpportunityDetail as any).mockResolvedValue(mockOpportunityMulti);
    (api.getAnalyticsPortfolio as any).mockResolvedValue(mockPortfolioResponse);
    (api.getAnalyticsConcentration as any).mockResolvedValue(mockConcentrationResponse);
  });

  it('renders OptimizationPage with macro portfolio hero strip and opportunity cards', async () => {
    render(
      <MemoryRouter initialEntries={['/optimization']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/optimization" element={<OptimizationPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('OPTIMIZATION WORKSPACE')).toBeInTheDocument();
    });

    // Check Portfolio strip
    expect(screen.getByText('Collective Optimization Portfolio')).toBeInTheDocument();
    expect(screen.getByText('ZERO DOUBLE-COUNTING ENFORCED')).toBeInTheDocument();

    // Check Opportunity Card
    expect(screen.getByText('Downsize Analytics EKS Node Group to m5.large')).toBeInTheDocument();
    expect(screen.getByText(/2 CANDIDATE PATHS AVAILABLE/i)).toBeInTheDocument();

    // Check Decision Room Trigger
    expect(screen.getByRole('button', { name: /Enter Decision Room/i })).toBeInTheDocument();
  });

  it('renders Decision Room (RecommendationDetailPage) with authoritative delta comparison and epistemic badges', async () => {
    render(
      <MemoryRouter initialEntries={['/optimization/opp-eks-oversized-01']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/optimization/:id" element={<RecommendationDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('DECISION WORKSPACE')).toBeInTheDocument();
    });

    // Verify delta comparison
    expect(screen.getByText('01 · Configuration Delta & Projected Impact')).toBeInTheDocument();
    expect(screen.getAllByText(/6x m5.4xlarge/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/6x m5.large/i).length).toBeGreaterThan(0);
    expect(screen.getByText('PROJECTED SAVINGS')).toBeInTheDocument();

    // Verify Epistemic classifications
    expect(screen.getAllByText('OBSERVED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('PROJECTED').length).toBeGreaterThan(0);
  });

  it('renders Categorical Decision Factors with discrete meters and EVIDENCE STRENGTH', async () => {
    render(
      <MemoryRouter initialEntries={['/optimization/opp-eks-oversized-01']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/optimization/:id" element={<RecommendationDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Categorical Decision Factors')).toBeInTheDocument();
    });

    expect(screen.getByText('RISK')).toBeInTheDocument();
    expect(screen.getByText('COMPLEXITY')).toBeInTheDocument();
    expect(screen.getByText('REVERSIBILITY')).toBeInTheDocument();
    expect(screen.getByText('EVIDENCE STRENGTH')).toBeInTheDocument();

    // Confirm NO "Confidence" or "Optimization Score"
    expect(screen.queryByText(/Optimization Score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/AI Confidence/i)).not.toBeInTheDocument();
  });

  it('switches between candidate recommendation alternatives updating savings and risk dynamically', async () => {
    render(
      <MemoryRouter initialEntries={['/optimization/opp-eks-oversized-01']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/optimization/:id" element={<RecommendationDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('02 · Candidate Alternatives (Mutually Exclusive Paths)')).toBeInTheDocument();
    });

    // Initially Option 1 (m5.large) is active
    expect(screen.getByText(/ACTIVE SELECTION/i)).toBeInTheDocument();
    expect(screen.getAllByText(/6x m5.large/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/LOW/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/94.0%/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Workload memory and CPU profiles demonstrate sustained 88.8% idle headroom/i).length).toBeGreaterThan(0);

    // Find and click the Graviton alternative card button
    const gravitonCard = screen.getByTestId('candidate-option-1');
    fireEvent.click(gravitonCard);

    // Verify ALL dependent state updated to Graviton
    await waitFor(() => {
      // 1. Proposed configuration
      expect(screen.getAllByText(/6x c7g.xlarge/i).length).toBeGreaterThan(0);
      // 2. Updated savings (₹1,65,000 / mo)
      expect(screen.getAllByText(/1,65,000/i).length).toBeGreaterThan(0);
      // 3. Updated risk (MEDIUM)
      expect(screen.getAllByText(/MEDIUM/i).length).toBeGreaterThan(0);
      // 4. Updated evidence strength (82.0%)
      expect(screen.getByText(/82.0%/i)).toBeInTheDocument();
      // 5. Updated epistemic explanation
      expect(screen.getAllByText(/ARM64 architecture provides superior price\/performance/i).length).toBeGreaterThan(0);
      // 6. Updated implementation considerations showing target specification
      expect(screen.getAllByText(/to 6x c7g.xlarge/i).length).toBeGreaterThan(0);
    });
  });

  it('renders PortfolioImpactCard with human-readable compatibility explanation and descriptive risk distribution', async () => {
    render(
      <MemoryRouter initialEntries={['/optimization/opp-eks-oversized-01']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/optimization/:id" element={<RecommendationDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Portfolio Context & Compatibility')).toBeInTheDocument();
    });

    expect(screen.getByText(/MUTUALLY EXCLUSIVE ALTERNATIVE DETECTED/i)).toBeInTheDocument();
    expect(screen.getByText(/Shares target resource/i)).toBeInTheDocument();
    expect(screen.getByText(/PORTFOLIO RISK DISTRIBUTION:/i)).toBeInTheDocument();
    expect(screen.getByText(/5 LOW/i)).toBeInTheDocument();
  });

  it('renders Implementation Considerations and verifies strict read-only boundary (ZERO mutation controls)', async () => {
    render(
      <MemoryRouter initialEntries={['/optimization/opp-eks-oversized-01']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/optimization/:id" element={<RecommendationDetailPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Implementation Considerations')).toBeInTheDocument();
    });

    // Check phases
    expect(screen.getByText('PRE-CHANGE')).toBeInTheDocument();
    expect(screen.getByText('CHANGE')).toBeInTheDocument();
    expect(screen.getByText('POST-CHANGE')).toBeInTheDocument();
    expect(screen.getByText('ROLLBACK')).toBeInTheDocument();

    // Check exploration handoffs
    expect(screen.getByRole('button', { name: /Explore in Scenarios →/i })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /Focus in Topology/i }).length).toBeGreaterThan(0);

    // CRITICAL INVARIANT: Assert NO execution buttons exist anywhere
    expect(screen.queryByRole('button', { name: /Apply/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Execute/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Modify/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Scale/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Delete/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Stop/i })).not.toBeInTheDocument();
  });
});

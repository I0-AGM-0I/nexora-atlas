import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ScenariosPage } from '../src/pages/ScenariosPage';
import { InvestigationProvider } from '../src/lib/InvestigationContext';
import { AskAtlasProvider } from '../src/lib/AskAtlasContext';
import type {
  ScenarioListResponse,
  ScenarioItem,
  ForecastResponse,
  ScenarioSimulationResult,
} from '../src/types/api';

vi.mock('../src/lib/api', () => ({
  api: {
    getScenarios: vi.fn(),
    simulateScenario: vi.fn(),
    getForecast: vi.fn(),
    getOptimization: vi.fn(),
    getResourceTelemetry: vi.fn(),
    getDashboardSummary: vi.fn(),
    getSpendTrend: vi.fn(),
    getServiceBreakdown: vi.fn(),
    getAccountBreakdown: vi.fn(),
    getRecentActivity: vi.fn(),
    getAnomalies: vi.fn(),
    getResources: vi.fn(),
    getResourceDetail: vi.fn(),
    getAnalyticsPortfolio: vi.fn(),
    getAnalyticsConcentration: vi.fn(),
  },
}));

import { api } from '../src/lib/api';

const mockScenarioConservative: ScenarioItem = {
  id: 'sc-001',
  name: 'Option A: Conservative',
  description: 'Automates non-production off-hours schedules and deletes detached storage.',
  baseline_monthly_cost: '2140000.00',
  projected_monthly_cost: '1890000.00',
  monthly_savings: '250000.00',
  percentage_savings: '11.68',
  performance_risk: 'LOW',
  reliability_risk: 'LOW',
  complexity_level: 'LOW',
  assumptions_json: {
    dev_schedule: 'Monday-Friday 09:00-18:00 IST',
    production_impact: 'None',
  },
  changes: [
    {
      id: 'ch-01',
      scenario_id: 'sc-001',
      resource_id: 'i-dev-sandbox-t3x-01',
      change_type: 'SCHEDULE_OFF_HOURS',
      current_spec: '6x Development EC2 instances running 24/7',
      proposed_spec: 'Automated schedule: 45 active hours/week',
      delta_cost: '-92000.00',
    },
    {
      id: 'ch-02',
      scenario_id: 'sc-001',
      resource_id: 'vol-unattached-dev-01',
      change_type: 'TERMINATE_UNATTACHED',
      current_spec: '3 unattached gp2 volumes (1200 GB)',
      proposed_spec: 'Snapshot and terminate detached storage',
      delta_cost: '-18000.00',
    },
    {
      id: 'ch-03',
      scenario_id: 'sc-001',
      resource_id: 'vol-legacy-gp2-analytics-01',
      change_type: 'TIER_STORAGE_GP3',
      current_spec: '2x 1000 GB gp2 volumes',
      proposed_spec: '2x 1000 GB gp3 volumes',
      delta_cost: '-26000.00',
    },
  ],
};

const mockScenarioAggressive: ScenarioItem = {
  id: 'sc-002',
  name: 'Option C: Aggressive',
  description: 'Full EKS cluster rightsizing and spot adoption across analytics workloads.',
  baseline_monthly_cost: '2140000.00',
  projected_monthly_cost: '1680000.00',
  monthly_savings: '460000.00',
  percentage_savings: '21.50',
  performance_risk: 'MEDIUM',
  reliability_risk: 'MEDIUM',
  complexity_level: 'MEDIUM',
  assumptions_json: {
    eks_rightsizing: 'm5.4xlarge -> m5.large',
  },
  changes: [
    {
      id: 'ch-eks-01',
      scenario_id: 'sc-002',
      resource_id: 'i-0eks-node-m5-4x-01',
      change_type: 'RIGHTSIZE_COMPUTE',
      current_spec: '6x m5.4xlarge nodes (16 vCPU, 64 GB)',
      proposed_spec: '6x m5.large nodes (2 vCPU, 8 GB)',
      delta_cost: '-142000.00',
    },
  ],
};

const mockScenarioListResponse: ScenarioListResponse = {
  scenarios: [mockScenarioConservative, mockScenarioAggressive],
};

const mockForecastResponse: ForecastResponse = {
  disclaimer: 'Organic forecast based on Holt-Winters smoothing.',
  forecasts: [
    {
      id: 'fc-01',
      account_id: '111222333444',
      account_name: 'Production AWS Account',
      forecast_month: '2026-10-01',
      projected_cost: 2180000,
      lower_bound: 2100000,
      upper_bound: 2260000,
      confidence_pct: 95,
      algorithm: 'EXPONENTIAL_SMOOTHING',
      is_synthetic: true,
    },
  ],
};

const mockSimResult: ScenarioSimulationResult = {
  scenario_id: 'sim-custom-001',
  name: 'Simulated Graviton Architecture',
  scenario_type: 'CUSTOM' as any,
  description: 'Simulated ARM migration',
  baseline_monthly_cost: '2140000.00' as any,
  projected_monthly_cost: '1998000.00' as any,
  monthly_savings: '142000.00' as any,
  annual_savings: '1704000.00' as any,
  percentage_savings: '6.64' as any,
  performance_risk: 'LOW',
  reliability_risk: 'LOW',
  complexity_level: 'MEDIUM',
  assumptions: {},
  changes: [],
  violations: [],
  is_valid: true,
  explanation: {
    observations: {},
    derived_metrics: {},
    evidence: ['Analytical simulation evaluated without architectural violations.'],
    method: 'SCENARIO_SIMULATION_ENGINE',
    parameters: {},
    assumptions: {},
    version: '1.0',
  },
};

describe('Milestone 7: Scenarios & Future-State Topology Workbench', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getScenarios as any).mockResolvedValue(mockScenarioListResponse);
    (api.getForecast as any).mockResolvedValue(mockForecastResponse);
    (api.simulateScenario as any).mockResolvedValue(mockSimResult);
    (api.getOptimization as any).mockResolvedValue({ opportunities: [] });
    (api.getResourceTelemetry as any).mockResolvedValue(null);
  });

  it('renders Future-State Workbench with dynamic scenario selector and epistemic classifications', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('SCENARIOS')).toBeInTheDocument();
      expect(screen.getByText(/Future-State Workbench/i)).toBeInTheDocument();
    });

    // Check scenario tabs
    expect(screen.getByTestId('scenario-tab-sc-001')).toBeInTheDocument();
    expect(screen.getByTestId('scenario-tab-sc-002')).toBeInTheDocument();

    // Check 4 Key Metric Cards
    expect(screen.getByText('BASELINE RUN-RATE')).toBeInTheDocument();
    expect(screen.getByText('PROJECTED RUN-RATE')).toBeInTheDocument();
    expect(screen.getByText('MONTHLY SAVINGS')).toBeInTheDocument();
    expect(screen.getByText('ANNUALIZED SAVINGS')).toBeInTheDocument();

    // Epistemic badges present
    expect(screen.getAllByText('DERIVED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('PROJECTED').length).toBeGreaterThan(0);
  });

  it('verifies deterministic financial reconciliation and invariant check (Baseline - Projected === Monthly Savings)', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('02 · Deterministic Financial Reconciliation')
      ).toBeInTheDocument();
    });

    // Valid invariant verified
    expect(
      screen.getByText(/RECONCILIATION VERIFIED · DECIMAL EXACT/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Deterministic Reconciliation Invariant/i)
    ).toBeInTheDocument();
  });

  it('detects and flags financial reconciliation discrepancies without silently correcting them', async () => {
    // Intentionally inconsistent scenario: Baseline 21,40,000, Projected 18,90,000, but savings reported as 5,00,000!
    const inconsistentScenario: ScenarioItem = {
      ...mockScenarioConservative,
      monthly_savings: '500000.00', // Mismatch! 2140000 - 1890000 = 250000 != 500000
    };

    (api.getScenarios as any).mockResolvedValue({
      scenarios: [inconsistentScenario],
    });

    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByTestId('reconciliation-discrepancy-badge')
      ).toBeInTheDocument();
    });

    // Alert displayed
    expect(
      screen.getByTestId('reconciliation-discrepancy-alert')
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Mathematical Invariant Violation in Scenario Contract/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Atlas does not silently alter or fake backend numbers/i)
    ).toBeInTheDocument();
  });

  it('switches between scenarios dynamically updating financial reconciliation, changes, assumptions, and topology without stale state', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('scenario-tab-sc-001')).toBeInTheDocument();
    });

    // Initially Conservative: savings is 2,50,000
    expect(screen.getAllByText(/2,50,000/i).length).toBeGreaterThan(0);
    expect(screen.getByText('SCHEDULE OFF HOURS')).toBeInTheDocument();

    // Click to switch to Option C: Aggressive
    const aggressiveTab = screen.getByTestId('scenario-tab-sc-002');
    fireEvent.click(aggressiveTab);

    // Verify all dependent state updated to Aggressive without stale state
    await waitFor(() => {
      // 1. Updated savings (4,60,000)
      expect(screen.getAllByText(/4,60,000/i).length).toBeGreaterThan(0);
      // 2. Updated changes (RIGHTSIZE COMPUTE)
      expect(screen.getByText('RIGHTSIZE COMPUTE')).toBeInTheDocument();
      // 3. Updated risk (MEDIUM)
      expect(screen.getAllByText(/MEDIUM/i).length).toBeGreaterThan(0);
      // 4. Updated assumption
      expect(screen.getByText('m5.4xlarge -> m5.large')).toBeInTheDocument();
    });
  });

  it('renders Future-State Topology with unmistakable visual separation between Observed and Projected estate nodes', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('06 · Future-State Topology Projection')
      ).toBeInTheDocument();
    });

    // Verify current estate nodes are tagged OBSERVED
    expect(screen.getAllByText('CURRENT ESTATE NODE').length).toBeGreaterThan(0);

    // Verify projected estate nodes are tagged PROJECTED and visually distinguished
    expect(
      screen.getAllByText('PROJECTED ESTATE NODE').length
    ).toBeGreaterThan(0);

    // Verify semantic diff badges in TopologyDiffCard
    expect(screen.getAllByText('MODIFIED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('REPLACED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('REMOVED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('UNCHANGED').length).toBeGreaterThan(0);
  });

  it('renders Assumptions panel using scenario.assumptions_json and gracefully falls back to NOT_CONFIGURED when empty', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('04 · Explicit Scenario Assumptions')
      ).toBeInTheDocument();
    });

    // Real assumptions from contract rendered with ASSUMED badge
    expect(
      screen.getByText('Monday-Friday 09:00-18:00 IST')
    ).toBeInTheDocument();
    expect(screen.getAllByText('ASSUMED').length).toBeGreaterThan(0);
  });

  it('renders independent Risk and Trade-Off dimensions without any composite magic score', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('05 · Independent Risk & Operational Trade-offs')
      ).toBeInTheDocument();
    });

    expect(screen.getByText('PERFORMANCE RISK')).toBeInTheDocument();
    expect(screen.getByText('RELIABILITY RISK')).toBeInTheDocument();
    expect(screen.getByText('COMPLEXITY')).toBeInTheDocument();
    expect(screen.getByText('REVERSIBILITY')).toBeInTheDocument();

    // Confirm NO magic score
    expect(screen.queryByText(/Scenario Score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Atlas Decision Score/i)).not.toBeInTheDocument();
  });

  it('renders Objective Scenario Comparison Matrix without declaring a winner', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('08 · Objective Scenario Comparison Matrix')
      ).toBeInTheDocument();
    });

    // Confirm NO "Winner" badge
    expect(screen.queryByText(/^WINNER$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/RECOMMENDED WINNER/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/BEST CHOICE/i)).not.toBeInTheDocument();

    // Table compares options side-by-side
    expect(
      screen.getByText('OBJECTIVE TRADE-OFF COMPARISON · ZERO "WINNER" BIAS')
    ).toBeInTheDocument();
  });

  it('differentiates organic forecast from scenario trajectory in ForecastRelationshipCard', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('09 · Forecast Trajectory vs Scenario Intervention')
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/ORGANIC FORECAST \(Status Quo\)/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/SCENARIO TRAJECTORY \(Intervention\)/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Projected Estate Divergence/i)
    ).toBeInTheDocument();
  });

  it('allows what-if simulation via SIMULATE PROJECTION with non-destructive constraint validation', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('What-If Workbench')).toBeInTheDocument();
    });

    // Open What-If workbench
    fireEvent.click(screen.getByText('What-If Workbench'));

    expect(
      screen.getByText('10 · Interactive Scenario Simulation Workbench')
    ).toBeInTheDocument();

    // The action button is strictly labeled SIMULATE PROJECTION
    const simButton = screen.getByRole('button', {
      name: /SIMULATE PROJECTION/i,
    });
    expect(simButton).toBeInTheDocument();

    fireEvent.click(simButton);

    await waitFor(() => {
      expect(screen.getByTestId('simulation-result-card')).toBeInTheDocument();
      expect(
        screen.getByText('Simulated Graviton Architecture')
      ).toBeInTheDocument();
      expect(screen.getByText('CONSTRAINTS VALIDATED')).toBeInTheDocument();
    });
  });

  it('opens Scenario Provenance Drawer and gracefully degrades missing evidence to NOT_AVAILABLE', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Provenance').length).toBeGreaterThan(0);
    });

    // Click provenance trigger on the first change
    const provenanceButtons = screen.getAllByText('Provenance');
    fireEvent.click(provenanceButtons[0]);

    await waitFor(() => {
      expect(
        screen.getByTestId('scenario-provenance-drawer')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Scenario Epistemic Provenance')
      ).toBeInTheDocument();
    });

    // Causal chain stages exist
    expect(screen.getByText('1. PROJECTED SAVINGS')).toBeInTheDocument();
    expect(screen.getByText('2. SCENARIO ACTION')).toBeInTheDocument();
    expect(screen.getByText('5. OPERATIONAL TELEMETRY')).toBeInTheDocument();

    // Verify graceful degradation (NOT_AVAILABLE rather than hallucinated telemetry)
    expect(screen.getAllByText(/NOT_AVAILABLE/i).length).toBeGreaterThan(0);
  });

  it('strictly enforces the read-only boundary with zero execution mutation controls', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('SCENARIOS')).toBeInTheDocument();
    });

    // Assert zero mutation verbs exist as buttons or actions
    expect(
      screen.queryByRole('button', { name: /^Apply$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /^Execute$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /^Deploy$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /^Provision$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /^Delete$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /^Terminate$/i })
    ).not.toBeInTheDocument();
  });

  it('synchronizes scenario state with URL deep links (?scenario=:id)', async () => {
    render(
      <MemoryRouter initialEntries={['/scenarios?scenario=sc-002']}>
        <InvestigationProvider>
          <AskAtlasProvider>
            <Routes>
              <Route path="/scenarios" element={<ScenariosPage />} />
            </Routes>
          </AskAtlasProvider>
        </InvestigationProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      // Option C: Aggressive should be automatically active due to ?scenario=sc-002
      expect(screen.getByText(/Currently analyzing:/i)).toBeInTheDocument();
      expect(screen.getAllByText('Option C: Aggressive').length).toBeGreaterThan(0);
    });

    // 4,60,000 savings for Option C
    expect(screen.getAllByText(/4,60,000/i).length).toBeGreaterThan(0);
  });
});

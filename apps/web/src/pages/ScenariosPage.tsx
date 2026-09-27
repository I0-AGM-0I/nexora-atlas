import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Sparkles, Sliders } from 'lucide-react';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { Button } from '../components/ui/Button';

import { ScenarioOverviewHero } from '../components/scenarios/ScenarioOverviewHero';
import { FinancialReconciliationCard } from '../components/scenarios/FinancialReconciliationCard';
import { ScenarioChangesTable } from '../components/scenarios/ScenarioChangesTable';
import { ScenarioAssumptionsPanel } from '../components/scenarios/ScenarioAssumptionsPanel';
import { ScenarioTradeOffsPanel } from '../components/scenarios/ScenarioTradeOffsPanel';
import { FutureStateTopology } from '../components/scenarios/FutureStateTopology';
import { ScenarioComparisonMatrix } from '../components/scenarios/ScenarioComparisonMatrix';
import { ForecastRelationshipCard } from '../components/scenarios/ForecastRelationshipCard';
import { ScenarioSimulationWorkbench } from '../components/scenarios/ScenarioSimulationWorkbench';
import { ScenarioProvenanceDrawer } from '../components/scenarios/ScenarioProvenanceDrawer';

import { useAskAtlas } from '../lib/AskAtlasContext';
import { useInvestigation } from '../lib/InvestigationContext';
import { api } from '../lib/api';
import type { ScenarioListResponse, ScenarioChangeItem } from '../types/api';

export const ScenariosPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { openAskAtlas } = useAskAtlas();
  const { startFocus } = useInvestigation();

  const [data, setData] = useState<ScenarioListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Provenance drawer state
  const [inspectingChange, setInspectingChange] = useState<ScenarioChangeItem | null>(null);
  const [isProvenanceOpen, setIsProvenanceOpen] = useState(false);

  // Interactive Workbench toggle
  const [showSimWorkbench, setShowSimWorkbench] = useState(false);

  const scenarioQueryParam = searchParams.get('scenario');
  const opportunityQueryParam = searchParams.get('opportunityId');

  const loadScenarios = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getScenarios();
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadScenarios();
  }, [loadScenarios]);

  const scenarios = useMemo(() => data?.scenarios || [], [data]);

  // Determine active scenario from URL query param, matching opportunity, or first scenario
  const activeScenario = useMemo(() => {
    if (scenarios.length === 0) return null;

    if (scenarioQueryParam) {
      const matched = scenarios.find((s) => s.id === scenarioQueryParam);
      if (matched) return matched;
    }

    if (opportunityQueryParam) {
      // Find scenario that references this opportunity or has relevant changes
      const matchedByOpp = scenarios.find(
        (s) =>
          s.changes.some((c) => c.resource_id?.includes(opportunityQueryParam)) ||
          s.name.toLowerCase().includes(opportunityQueryParam.toLowerCase())
      );
      if (matchedByOpp) return matchedByOpp;
    }

    return scenarios[0];
  }, [scenarios, scenarioQueryParam, opportunityQueryParam]);

  // Handle scenario switching with URL state synchronization
  const handleSelectScenario = useCallback(
    (id: string) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set('scenario', id);
      setSearchParams(newParams);
    },
    [searchParams, setSearchParams]
  );

  // Open provenance drawer for a specific change
  const handleInspectProvenance = useCallback((change: ScenarioChangeItem) => {
    setInspectingChange(change);
    setIsProvenanceOpen(true);
  }, []);

  // Spatial FOCUS handoff
  const handleFocusResource = useCallback(
    (resourceId: string) => {
      startFocus({
        entityId: resourceId,
        entityNativeId: resourceId,
        entityType: 'RESOURCE',
        entityName: resourceId,
        origin: `Future-State Topology · ${activeScenario?.name || 'Scenario'}`,
        costDelta: activeScenario ? Number(activeScenario.monthly_savings) : undefined,
      });
      navigate(`/spend?focus=${encodeURIComponent(resourceId)}&trace=true`);
    },
    [startFocus, activeScenario, navigate]
  );

  if (loading) {
    return (
      <div className="space-y-6 select-none">
        <div className="h-8 w-48 bg-[#141B27] animate-pulse rounded" />
        <CardSkeleton rows={3} />
        <CardSkeleton rows={5} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Unable to Load Scenarios"
        message={error || 'Failed to retrieve scenario models.'}
        onRetry={loadScenarios}
      />
    );
  }

  if (scenarios.length === 0 || !activeScenario) {
    return (
      <EmptyState
        title="No Scenarios Available"
        message="No what-if scenario models are currently configured for this estate."
      />
    );
  }

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* 01 · Scenario Overview Hero & Scenario Selector */}
      <ScenarioOverviewHero
        scenarios={scenarios}
        activeScenario={activeScenario}
        onSelectScenario={handleSelectScenario}
      />

      {/* Global Action Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-[#0F141C] border border-[#1E2638]">
        <div className="text-xs font-mono text-slate-300">
          Currently analyzing:{' '}
          <strong className="text-sky-300 font-semibold">{activeScenario.name}</strong>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() =>
              openAskAtlas({
                scopeType: 'SCENARIO',
                scenarioId: activeScenario.id,
                scopeLabel: `Scenario: ${activeScenario.name}`,
                initialQuestion: `Explain the financial rationale, operational assumptions, and performance risk of the "${activeScenario.name}" scenario.`,
              })
            }
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-colors font-mono"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas About Scenario</span>
          </button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSimWorkbench((prev) => !prev)}
            icon={<Sliders className="w-3.5 h-3.5" />}
          >
            {showSimWorkbench ? 'Close Workbench' : 'What-If Workbench'}
          </Button>
        </div>
      </div>

      {/* 10 · Interactive Simulation Workbench (Collapsible or in-flow) */}
      {showSimWorkbench && (
        <ScenarioSimulationWorkbench
          baselineMonthlyCost={activeScenario.baseline_monthly_cost}
        />
      )}

      {/* 02 · Financial Reconciliation Invariant Card */}
      <FinancialReconciliationCard scenario={activeScenario} />

      {/* 03 · Scenario Changes Table */}
      <ScenarioChangesTable
        changes={activeScenario.changes}
        onInspectProvenance={handleInspectProvenance}
      />

      {/* 04 · Explicit Assumptions & 05 · Independent Trade-Offs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <ScenarioAssumptionsPanel
            assumptionsJson={activeScenario.assumptions_json}
          />
        </div>
        <div className="lg:col-span-6">
          <ScenarioTradeOffsPanel
            monthlySavings={activeScenario.monthly_savings}
            performanceRisk={activeScenario.performance_risk}
            reliabilityRisk={activeScenario.reliability_risk}
            complexityLevel={activeScenario.complexity_level}
          />
        </div>
      </div>

      {/* 06 & 07 · Future-State Topology & Semantic Diff */}
      <FutureStateTopology
        scenarioName={activeScenario.name}
        changes={activeScenario.changes}
        onFocusResource={handleFocusResource}
      />

      {/* 08 · Objective Scenario Comparison Matrix */}
      <ScenarioComparisonMatrix
        scenarios={scenarios}
        activeScenarioId={activeScenario.id}
        onSelectScenario={handleSelectScenario}
      />

      {/* 09 · Forecast Relationship Card */}
      <ForecastRelationshipCard activeScenario={activeScenario} />

      {/* Epistemic Provenance Drawer */}
      <ScenarioProvenanceDrawer
        change={inspectingChange}
        isOpen={isProvenanceOpen}
        onClose={() => {
          setIsProvenanceOpen(false);
          setInspectingChange(null);
        }}
      />
    </div>
  );
};

import React, { useState } from 'react';
import { Sliders, Sparkles, ShieldCheck, AlertTriangle } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency } from '../../lib/format';
import { api } from '../../lib/api';
import type { ScenarioSimulationResult } from '../../types/api';

interface ScenarioSimulationWorkbenchProps {
  baselineMonthlyCost: number | string;
}

export const ScenarioSimulationWorkbench: React.FC<ScenarioSimulationWorkbenchProps> = ({
  baselineMonthlyCost,
}) => {
  const [simName, setSimName] = useState('Custom Architecture What-If');
  const [changeType, setChangeType] = useState('CONSERVATIVE_RIGHTSIZE');
  const [currentSpec, setCurrentSpec] = useState('6x m5.4xlarge');
  const [proposedSpec, setProposedSpec] = useState('6x m5.large');
  const [monthlyDelta, setMonthlyDelta] = useState('142000');
  const [pricingBasis, setPricingBasis] = useState('ON_DEMAND');

  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<ScenarioSimulationResult | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    setSimError(null);

    const deltaVal = Number(monthlyDelta) || 0;
    const baseCost = Number(baselineMonthlyCost) || 2140000;

    try {
      const result = await api.simulateScenario({
        name: simName,
        scenario_type: 'CUSTOM',
        description: `Simulated modification: ${currentSpec} -> ${proposedSpec}`,
        baseline_monthly_cost: baseCost,
        custom_assumptions: {
          pricing_basis: pricingBasis,
          simulation_engine: 'Phase 6 Scenario Simulation Engine',
        },
        proposed_changes: [
          {
            change_type: changeType,
            current_spec: currentSpec,
            proposed_spec: proposedSpec,
            current_monthly_cost: deltaVal * 2,
            projected_monthly_cost: Math.max(0, deltaVal),
            delta_cost: -deltaVal,
            risk_level: 'LOW',
            complexity_level: 'LOW',
          },
        ],
      });
      setSimResult(result);
    } catch (err: any) {
      setSimError(err?.message || 'Failed to simulate scenario projection');
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-sky-400" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            10 · Interactive Scenario Simulation Workbench
          </h4>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="text-slate-400">NON-DESTRUCTIVE:</span>
          <EpistemicBadge classification="PROJECTED" size="xs" />
        </div>
      </div>

      <p className="text-xs text-atlas-muted font-mono leading-relaxed">
        Model speculative architectural changes using the backend constraint engine. Projections are computed strictly in analytical isolation with zero infrastructure mutations.
      </p>

      {/* Simulation Form */}
      <form onSubmit={handleSimulate} className="space-y-4 text-xs font-mono">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">SCENARIO TITLE</label>
            <input
              type="text"
              value={simName}
              onChange={(e) => setSimName(e.target.value)}
              className="w-full bg-[#141B27] border border-[#1E2638] rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:border-sky-400 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">CHANGE TYPE</label>
            <select
              value={changeType}
              onChange={(e) => setChangeType(e.target.value)}
              className="w-full bg-[#141B27] border border-[#1E2638] rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:border-sky-400 focus:outline-none"
            >
              <option value="CONSERVATIVE_RIGHTSIZE">In-Family Right-Size</option>
              <option value="ARM_MIGRATION">ARM Graviton Migration</option>
              <option value="STORAGE_TIER_MODERNIZATION">gp2 → gp3 Modernization</option>
              <option value="SCHEDULE_OFF_HOURS">Off-Hours Automation</option>
              <option value="TERMINATE_UNATTACHED_STORAGE">Delete Unattached EBS</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">PRICING BASIS</label>
            <select
              value={pricingBasis}
              onChange={(e) => setPricingBasis(e.target.value)}
              className="w-full bg-[#141B27] border border-[#1E2638] rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:border-sky-400 focus:outline-none"
            >
              <option value="ON_DEMAND">On-Demand Rates</option>
              <option value="SAVINGS_PLANS_COMMITTED">1-Yr Compute Savings Plan</option>
              <option value="SPOT_HYBRID">Spot Workload Mix</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">CURRENT SPEC (OBSERVED)</label>
            <input
              type="text"
              value={currentSpec}
              onChange={(e) => setCurrentSpec(e.target.value)}
              className="w-full bg-[#141B27] border border-[#1E2638] rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:border-sky-400 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">PROPOSED SPEC (PROJECTED)</label>
            <input
              type="text"
              value={proposedSpec}
              onChange={(e) => setProposedSpec(e.target.value)}
              className="w-full bg-[#141B27] border border-[#1E2638] rounded px-3 py-1.5 text-xs text-emerald-300 font-mono focus:border-emerald-400 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">MONTHLY REDUCTION DELTA (INR)</label>
            <input
              type="number"
              value={monthlyDelta}
              onChange={(e) => setMonthlyDelta(e.target.value)}
              className="w-full bg-[#141B27] border border-[#1E2638] rounded px-3 py-1.5 text-xs text-emerald-400 font-mono focus:border-emerald-400 focus:outline-none"
              required
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-[#1E2638]">
          <span className="text-[10px] text-slate-500 font-mono">
            Pure What-If calculation. No infrastructure state will be altered.
          </span>

          <button
            type="submit"
            disabled={simulating}
            className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-slate-950 font-bold font-mono text-xs transition-colors flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{simulating ? 'SIMULATING PROJECTION...' : 'SIMULATE PROJECTION'}</span>
          </button>
        </div>
      </form>

      {/* Error state */}
      {simError && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/40 text-rose-300 rounded text-xs font-mono">
          {simError}
        </div>
      )}

      {/* Simulation Result Output */}
      {simResult && (
        <div
          data-testid="simulation-result-card"
          className="mt-4 p-4 rounded-lg bg-sky-500/5 border-2 border-dashed border-sky-400/50 space-y-3 font-mono"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-sky-200">{simResult.name}</span>
              <EpistemicBadge classification="PROJECTED" size="xs" />
              {simResult.is_valid ? (
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  <span>CONSTRAINTS VALIDATED</span>
                </span>
              ) : (
                <span className="text-[10px] text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
                  VIOLATIONS DETECTED
                </span>
              )}
            </div>

            <span className="text-xs font-bold text-emerald-400">
              Savings: -{formatCurrency(simResult.monthly_savings)} / mo ({simResult.percentage_savings}%)
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
            <div className="p-2.5 rounded bg-[#141B27] border border-[#1E2638]">
              <span className="text-[10px] text-slate-500 block">Baseline Monthly</span>
              <span className="font-bold text-slate-200">
                {formatCurrency(simResult.baseline_monthly_cost)}
              </span>
            </div>

            <div className="p-2.5 rounded bg-sky-500/10 border border-sky-500/30">
              <span className="text-[10px] text-sky-400 block">Projected Monthly</span>
              <span className="font-bold text-sky-200">
                {formatCurrency(simResult.projected_monthly_cost)}
              </span>
            </div>

            <div className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/30">
              <span className="text-[10px] text-emerald-400 block">Annual Savings</span>
              <span className="font-bold text-emerald-300">
                {formatCurrency(simResult.annual_savings)}
              </span>
            </div>

            <div className="p-2.5 rounded bg-[#141B27] border border-[#1E2638]">
              <span className="text-[10px] text-slate-500 block">Risk / Complexity</span>
              <span className="font-bold text-slate-200">
                {simResult.performance_risk} / {simResult.complexity_level}
              </span>
            </div>
          </div>

          {simResult.violations && simResult.violations.length > 0 && (
            <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Architecture Violations:</span>
              </div>
              {simResult.violations.map((v, i) => (
                <div key={i} className="text-[11px] pl-5">• {v.reason}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

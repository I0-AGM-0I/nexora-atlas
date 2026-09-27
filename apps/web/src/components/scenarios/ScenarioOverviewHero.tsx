import React from 'react';
import { GitFork, ArrowRight, ShieldCheck } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency, formatPercent } from '../../lib/format';
import type { ScenarioItem } from '../../types/api';

interface ScenarioOverviewHeroProps {
  scenarios: ScenarioItem[];
  activeScenario: ScenarioItem;
  onSelectScenario: (id: string) => void;
  lastModeled?: string;
}

export const ScenarioOverviewHero: React.FC<ScenarioOverviewHeroProps> = ({
  scenarios,
  activeScenario,
  onSelectScenario,
  lastModeled = 'ACTIVE INGESTION',
}) => {
  const annualSavings = (Number(activeScenario.monthly_savings || 0) * 12).toFixed(2);

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1E2638] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <GitFork className="w-4 h-4 text-sky-400" />
            <h1 className="text-xl font-bold tracking-tight text-atlas-text font-mono">
              SCENARIOS
            </h1>
            <span className="text-slate-600 font-mono">/</span>
            <span className="text-xs font-mono text-slate-300 font-semibold uppercase tracking-wider">
              Future-State Workbench
            </span>
          </div>
          <p className="text-xs text-atlas-muted font-mono flex items-center gap-2">
            <span>Model a possible future state for your technology estate.</span>
            <span className="text-slate-500 font-mono">[ CURRENT ESTATE ] → [ FUTURE STATE ]</span>
          </p>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="px-2 py-1 rounded bg-[#141B27] border border-[#1E2638] text-slate-300">
            {scenarios.length} SCENARIOS AVAILABLE
          </span>
          <span className="px-2 py-1 rounded bg-sky-500/10 border border-sky-500/30 text-sky-400">
            LAST MODELED: {lastModeled}
          </span>
        </div>
      </div>

      {/* Scenario Selector Tabs */}
      <div className="flex flex-wrap gap-2 pt-1" data-testid="scenario-selector-tabs">
        {scenarios.map((s) => {
          const isSelected = s.id === activeScenario.id;
          return (
            <button
              key={s.id}
              type="button"
              data-testid={`scenario-tab-${s.id}`}
              onClick={() => onSelectScenario(s.id)}
              className={`px-3.5 py-2 rounded border text-left transition-all font-mono ${
                isSelected
                  ? 'bg-sky-500/10 border-sky-400 text-sky-200 ring-1 ring-sky-400/40 shadow-sm'
                  : 'bg-[#141B27]/60 border-[#1E2638] text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isSelected ? 'bg-sky-400 shadow-[0_0_6px_#38bdf8]' : 'bg-slate-600'
                  }`}
                />
                <span className="text-xs font-bold tracking-tight">{s.name}</span>
              </div>
              <div className="text-[10px] text-emerald-400 font-semibold mt-0.5 ml-3.5">
                -{formatPercent(s.percentage_savings)} spend reduction
              </div>
            </button>
          );
        })}
      </div>

      {/* 01 · 4 Metric Hero Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Baseline Monthly Cost */}
        <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-atlas-muted uppercase">BASELINE RUN-RATE</span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-200">
            {formatCurrency(activeScenario.baseline_monthly_cost)}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            Baseline measured monthly spend before modifications
          </div>
        </div>

        {/* Projected Monthly Cost */}
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-sky-400 uppercase">PROJECTED RUN-RATE</span>
            <EpistemicBadge classification="PROJECTED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-sky-300">
            {formatCurrency(activeScenario.projected_monthly_cost)}
          </div>
          <div className="text-[10px] font-mono text-sky-400/80">
            Target steady-state monthly expenditure under scenario
          </div>
        </div>

        {/* Monthly Savings */}
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-emerald-400 uppercase">MONTHLY SAVINGS</span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            -{formatCurrency(activeScenario.monthly_savings)}
          </div>
          <div className="text-[10px] font-mono text-emerald-300/80 flex items-center gap-1">
            <ArrowRight className="w-3 h-3" />
            <span>-{formatPercent(activeScenario.percentage_savings)} reduction</span>
          </div>
        </div>

        {/* Annualized Savings */}
        <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-atlas-muted uppercase">ANNUALIZED SAVINGS</span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {formatCurrency(annualSavings)}
          </div>
          <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>Monthly savings × 12 (deterministic arithmetic)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

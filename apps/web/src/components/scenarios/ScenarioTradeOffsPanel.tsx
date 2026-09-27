import React from 'react';
import { Sliders, Shield, Zap, RefreshCw, Layers } from 'lucide-react';
import { formatCurrency } from '../../lib/format';

interface ScenarioTradeOffsPanelProps {
  monthlySavings?: number | string | null;
  performanceRisk?: string | null;
  reliabilityRisk?: string | null;
  complexityLevel?: string | null;
  reversibility?: string | null;
}

export const ScenarioTradeOffsPanel: React.FC<ScenarioTradeOffsPanelProps> = ({
  monthlySavings,
  performanceRisk,
  reliabilityRisk,
  complexityLevel,
  reversibility = 'HIGH',
}) => {
  const getStepValue = (level?: string | null): number => {
    if (!level) return 0;
    const l = level.toUpperCase();
    if (l === 'NONE') return 0;
    if (l === 'LOW') return 1;
    if (l === 'MEDIUM' || l === 'MODERATE') return 2;
    if (l === 'HIGH' || l === 'CRITICAL') return 3;
    return 1;
  };

  const renderMeter = (step: number, colorClass: string) => {
    return (
      <div className="flex items-center gap-1 mt-1.5">
        {[1, 2, 3].map((idx) => (
          <div
            key={idx}
            className={`h-1.5 flex-1 rounded-sm transition-all ${
              idx <= step ? colorClass : 'bg-[#1E2638]'
            }`}
          />
        ))}
      </div>
    );
  };

  const perfStep = getStepValue(performanceRisk);
  const relStep = getStepValue(reliabilityRisk);
  const compStep = getStepValue(complexityLevel);
  const revStep = getStepValue(reversibility);

  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            05 · Independent Risk & Operational Trade-offs
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-400 bg-[#141B27] px-2 py-0.5 rounded border border-[#1E2638]">
          DECOUPLED DIMENSIONS · ZERO SYNTHETIC SCORE
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* 1. Financial Impact */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-atlas-muted uppercase">
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            <span>FINANCIAL IMPACT</span>
          </div>
          <div className="text-lg font-bold font-mono text-emerald-400">
            {monthlySavings ? `-${formatCurrency(monthlySavings)}` : 'NOT_AVAILABLE'}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            Net monthly run-rate reduction
          </div>
        </div>

        {/* 2. Performance Risk */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center gap-1.5 text-atlas-muted uppercase">
              <Shield className="w-3.5 h-3.5 text-sky-400" />
              <span>PERFORMANCE RISK</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {performanceRisk ? `${perfStep}/3` : '—'}
            </span>
          </div>
          <div
            className={`text-lg font-bold font-mono ${
              perfStep <= 1
                ? 'text-emerald-400'
                : perfStep === 2
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}
          >
            {performanceRisk ? performanceRisk.toUpperCase() : 'NOT_AVAILABLE'}
          </div>
          {performanceRisk ? (
            renderMeter(
              perfStep,
              perfStep <= 1 ? 'bg-emerald-400' : perfStep === 2 ? 'bg-amber-400' : 'bg-rose-400'
            )
          ) : (
            <div className="text-[10px] font-mono text-slate-500">Unspecified in contract</div>
          )}
        </div>

        {/* 3. Reliability Risk */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center gap-1.5 text-atlas-muted uppercase">
              <Shield className="w-3.5 h-3.5 text-indigo-400" />
              <span>RELIABILITY RISK</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {reliabilityRisk ? `${relStep}/3` : '—'}
            </span>
          </div>
          <div
            className={`text-lg font-bold font-mono ${
              relStep <= 1
                ? 'text-emerald-400'
                : relStep === 2
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}
          >
            {reliabilityRisk ? reliabilityRisk.toUpperCase() : 'NOT_AVAILABLE'}
          </div>
          {reliabilityRisk ? (
            renderMeter(
              relStep,
              relStep <= 1 ? 'bg-emerald-400' : relStep === 2 ? 'bg-amber-400' : 'bg-rose-400'
            )
          ) : (
            <div className="text-[10px] font-mono text-slate-500">Unspecified in contract</div>
          )}
        </div>

        {/* 4. Implementation Complexity */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center gap-1.5 text-atlas-muted uppercase">
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              <span>COMPLEXITY</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {complexityLevel ? `${compStep}/3` : '—'}
            </span>
          </div>
          <div
            className={`text-lg font-bold font-mono ${
              compStep <= 1
                ? 'text-emerald-400'
                : compStep === 2
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}
          >
            {complexityLevel ? complexityLevel.toUpperCase() : 'NOT_AVAILABLE'}
          </div>
          {complexityLevel ? (
            renderMeter(
              compStep,
              compStep <= 1 ? 'bg-emerald-400' : compStep === 2 ? 'bg-amber-400' : 'bg-rose-400'
            )
          ) : (
            <div className="text-[10px] font-mono text-slate-500">Unspecified in contract</div>
          )}
        </div>

        {/* 5. Reversibility */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center gap-1.5 text-atlas-muted uppercase">
              <RefreshCw className="w-3.5 h-3.5 text-emerald-400" />
              <span>REVERSIBILITY</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {reversibility ? `${revStep}/3` : '—'}
            </span>
          </div>
          <div
            className={`text-lg font-bold font-mono ${
              revStep >= 3
                ? 'text-emerald-400'
                : revStep === 2
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}
          >
            {reversibility ? reversibility.toUpperCase() : 'NOT_AVAILABLE'}
          </div>
          {reversibility ? (
            renderMeter(
              revStep,
              revStep >= 3 ? 'bg-emerald-400' : revStep === 2 ? 'bg-amber-400' : 'bg-rose-400'
            )
          ) : (
            <div className="text-[10px] font-mono text-slate-500">Unspecified in contract</div>
          )}
        </div>
      </div>
    </div>
  );
};

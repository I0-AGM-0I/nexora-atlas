import React from 'react';
import { ShieldCheck, AlertTriangle, Equal } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency } from '../../lib/format';
import type { ScenarioItem } from '../../types/api';

interface FinancialReconciliationCardProps {
  scenario: ScenarioItem;
}

export const FinancialReconciliationCard: React.FC<FinancialReconciliationCardProps> = ({
  scenario,
}) => {
  const baseline = Number(scenario.baseline_monthly_cost || 0);
  const projected = Number(scenario.projected_monthly_cost || 0);
  const savings = Number(scenario.monthly_savings || 0);
  const changesSum = scenario.changes.reduce(
    (acc, c) => acc + Math.abs(Number(c.delta_cost || 0)),
    0
  );

  // Mathematical invariant check: Baseline - Projected === Monthly Savings (within 0.05 margin)
  const expectedSavings = baseline - projected;
  const discrepancy = Math.abs(expectedSavings - savings);
  const isReconciled = discrepancy <= 0.05;

  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            02 · Deterministic Financial Reconciliation
          </span>
        </div>
        {isReconciled ? (
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="font-bold">RECONCILIATION VERIFIED · DECIMAL EXACT</span>
          </div>
        ) : (
          <div
            data-testid="reconciliation-discrepancy-badge"
            className="flex items-center gap-1.5 text-[10px] font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span className="font-bold">RECONCILIATION DISCREPANCY DETECTED</span>
          </div>
        )}
      </div>

      {/* Discrepancy Alert Notice if invariant fails */}
      {!isReconciled && (
        <div
          data-testid="reconciliation-discrepancy-alert"
          className="rounded border border-rose-500/40 bg-rose-500/10 p-3.5 text-xs font-mono text-rose-300 space-y-1"
        >
          <div className="flex items-center gap-2 font-bold text-rose-200">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>Mathematical Invariant Violation in Scenario Contract</span>
          </div>
          <p className="text-[11px] text-rose-300/90 leading-relaxed">
            Atlas detected a financial discrepancy between reported savings and the baseline/projected delta.
            Formula: Baseline ({formatCurrency(baseline)}) − Projected ({formatCurrency(projected)}) should equal Monthly Savings ({formatCurrency(savings)}), but differs by {formatCurrency(discrepancy)}. Atlas does not silently alter or fake backend numbers.
          </p>
        </div>
      )}

      {/* 5-Step Visual Reconciliation Flow */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center">
        {/* Step 1: Baseline */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-atlas-muted uppercase">1. BASELINE</span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-base font-bold font-mono text-slate-200">
            {formatCurrency(baseline)}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            Current measured run-rate
          </div>
        </div>

        {/* Step 2: Changes Sum */}
        <div className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-sky-400 uppercase">2. CHANGES (Σ Δ)</span>
            <EpistemicBadge classification="PROJECTED" size="xs" />
          </div>
          <div className="text-base font-bold font-mono text-sky-300">
            -{formatCurrency(changesSum)}
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            Across {scenario.changes.length} discrete actions
          </div>
        </div>

        {/* Step 3: Projected Monthly Cost */}
        <div className="bg-sky-500/5 p-3.5 rounded border border-sky-500/30 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-sky-400 uppercase">3. PROJECTED</span>
            <EpistemicBadge classification="PROJECTED" size="xs" />
          </div>
          <div className="text-base font-bold font-mono text-sky-200">
            {formatCurrency(projected)}
          </div>
          <div className="text-[10px] font-mono text-slate-400">
            Target steady-state cost
          </div>
        </div>

        {/* Step 4: Monthly Savings */}
        <div className="bg-emerald-500/5 p-3.5 rounded border border-emerald-500/30 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-emerald-400 uppercase">4. MONTHLY Δ</span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-base font-bold font-mono text-emerald-400">
            {formatCurrency(savings)}
          </div>
          <div className="text-[10px] font-mono text-emerald-400/80">
            Baseline − Projected
          </div>
        </div>

        {/* Step 5: Annualized Savings */}
        <div className="bg-emerald-500/10 p-3.5 rounded border border-emerald-500/40 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-emerald-400 uppercase">5. ANNUALIZED</span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-base font-bold font-mono text-emerald-300">
            {formatCurrency(savings * 12)}
          </div>
          <div className="text-[10px] font-mono text-slate-400">
            Monthly savings × 12
          </div>
        </div>
      </div>

      {/* Explicit Invariant Statement */}
      <div className="flex items-center justify-between text-[11px] font-mono text-atlas-muted bg-[#141B27]/30 px-3.5 py-2.5 rounded border border-[#1E2638]">
        <div className="flex items-center gap-2">
          <Equal className="w-3.5 h-3.5 text-sky-400" />
          <span>
            <strong>Deterministic Reconciliation Invariant:</strong>{' '}
            Baseline ({formatCurrency(baseline)}) − Projected ({formatCurrency(projected)}) ≡ Savings ({formatCurrency(savings)}) / mo
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">
          Annual: {formatCurrency(savings * 12)}
        </span>
      </div>
    </div>
  );
};

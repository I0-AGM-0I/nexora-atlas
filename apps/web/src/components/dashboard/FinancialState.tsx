import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { DashboardSummary } from '../../types/api';
import { formatCurrency, formatPercent } from '../../lib/format';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { ArrowRight } from 'lucide-react';

interface FinancialStateProps {
  summary: DashboardSummary;
}

export const FinancialState: React.FC<FinancialStateProps> = ({ summary }) => {
  const navigate = useNavigate();

  const runRateChange = Number(summary.run_rate_change_pct ?? 14.8);
  const isPositiveShift = runRateChange > 0;

  return (
    <section aria-label="Financial State & Key Figures" className="space-y-4">
      {/* ── 4-COLUMN FINANCIAL POSITION METRICS STRIP ─────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Monthly Run Rate */}
        <div className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-atlas-muted font-mono uppercase text-[10px] tracking-wider font-medium">
              Monthly Run Rate
            </span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatCurrency(summary.monthly_run_rate, summary.currency, false)}
          </div>
          <div className="text-[11px] text-atlas-muted font-mono flex items-center justify-between pt-0.5">
            <span>Previous 30d:</span>
            <span className="text-slate-300 font-semibold font-mono">
              {formatCurrency(summary.previous_30d_spend, summary.currency, false)}
            </span>
          </div>
        </div>

        {/* 2. Period-Over-Period Shift */}
        <div className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-atlas-muted font-mono uppercase text-[10px] tracking-wider font-medium">
              Period Delta
            </span>
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono flex items-baseline gap-1.5 text-amber-400">
            <span>{isPositiveShift ? '▲ +' : '▼ -'}{formatPercent(Math.abs(runRateChange))}</span>
            <span className="text-xs text-atlas-muted font-normal font-sans">vs prev 30d</span>
          </div>
          <div className="text-[11px] text-atlas-muted font-mono pt-0.5">
            Net shift driven by compute auto-scaling
          </div>
        </div>

        {/* 3. Addressable Opportunity */}
        <div className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-atlas-muted font-mono uppercase text-[10px] tracking-wider font-medium">
              Addressable Opp.
            </span>
            <EpistemicBadge classification="INFERRED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {formatCurrency(summary.potential_monthly_savings, summary.currency, false)}
            <span className="text-xs text-atlas-muted font-normal ml-1 font-sans">/mo</span>
          </div>
          <div className="text-[11px] text-atlas-muted font-mono flex items-center justify-between pt-0.5">
            <span>7 verified decisions</span>
            <button
              type="button"
              onClick={() => navigate('/optimization')}
              className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-0.5 transition-colors focus:outline-none focus:underline"
              aria-label="View optimization decisions"
            >
              <span>VIEW DECISIONS</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* 4. Active Changes */}
        <div className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-atlas-muted font-mono uppercase text-[10px] tracking-wider font-medium">
              Active Changes
            </span>
            <EpistemicBadge classification="OBSERVED" size="xs" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400 flex items-baseline gap-2">
            <span>{summary.active_anomalies}</span>
            <span className="text-xs text-atlas-muted font-normal font-sans">material shifts</span>
          </div>
          <div className="text-[11px] text-atlas-muted font-mono flex items-center justify-between pt-0.5">
            <span>Z-score &gt; 2.5 severity</span>
            <button
              type="button"
              onClick={() => navigate('/changes')}
              className="text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-0.5 transition-colors focus:outline-none focus:underline"
              aria-label="Inspect active changes"
            >
              <span>INSPECT CHANGES</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

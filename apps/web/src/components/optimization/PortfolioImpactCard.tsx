import React from 'react';
import { PieChart, CheckCircle2, AlertTriangle, XCircle, Info, ShieldAlert } from 'lucide-react';
import { formatCurrency } from '../../lib/format';
import { EpistemicBadge } from '../ui/EpistemicBadge';

export interface PortfolioImpactCardProps {
  totalAddressableMonthly: number | string;
  selectedDecisionMonthly: number | string;
  remainingCompatibleMonthly: number | string;
  isMutuallyExclusive?: boolean;
  alternativeTitle?: string;
  targetResourceName?: string;
  compatibleCount?: number;
  dependencyCount?: number;
  conflictCount?: number;
  riskProfile?: {
    countLow: number;
    countMedium: number;
    countHigh: number;
    highestRisk: string;
  };
  explanation?: string;
  className?: string;
}

export const PortfolioImpactCard: React.FC<PortfolioImpactCardProps> = ({
  totalAddressableMonthly = 460000,
  selectedDecisionMonthly = 142000,
  remainingCompatibleMonthly = 318000,
  isMutuallyExclusive = false,
  alternativeTitle,
  targetResourceName,
  compatibleCount = 5,
  dependencyCount = 1,
  conflictCount = 1,
  riskProfile = { countLow: 4, countMedium: 2, countHigh: 0, highestRisk: 'MEDIUM' },
  explanation,
  className = '',
}) => {
  const total = Number(totalAddressableMonthly) || 460000;
  const decision = Number(selectedDecisionMonthly) || 0;
  const remaining = Number(remainingCompatibleMonthly) || Math.max(0, total - decision);

  const decisionPct = Math.min(100, Math.round((decision / total) * 100));
  const remainingPct = Math.min(100 - decisionPct, Math.round((remaining / total) * 100));

  return (
    <div className={`rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-4 select-none ${className}`}>
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <PieChart className="w-4 h-4 text-sky-400" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            Portfolio Context & Compatibility
          </h4>
          <EpistemicBadge classification="DERIVED" size="xs" />
        </div>
        <span className="text-[10px] font-mono text-slate-400 bg-[#141B27] px-2 py-0.5 rounded border border-[#1E2638]">
          PHASE 6 PORTFOLIO ENGINE
        </span>
      </div>

      {/* ── ADDRESSABLE SAVINGS SPLIT METRICS ────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
          <div className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider">
            Total Addressable Portfolio
          </div>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            {formatCurrency(total)}
            <span className="text-xs font-normal text-slate-400"> / mo</span>
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">
            Macro optimization potential
          </div>
        </div>

        <div className="bg-[#141B27]/80 p-3 rounded border border-sky-500/30">
          <div className="text-[10px] font-mono text-sky-400 uppercase tracking-wider flex items-center justify-between">
            <span>This Decision</span>
            <span className="text-[10px] bg-sky-500/20 text-sky-300 px-1.5 rounded">{decisionPct}%</span>
          </div>
          <div className="text-xl font-bold font-mono text-sky-300 mt-1">
            {formatCurrency(decision)}
            <span className="text-xs font-normal text-slate-400"> / mo</span>
          </div>
          <div className="text-[10px] font-mono text-slate-400 mt-0.5">
            Quantified candidate contribution
          </div>
        </div>

        <div className="bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
          <div className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider flex items-center justify-between">
            <span>Compatible Remaining</span>
            <span className="text-[10px] text-slate-400">{remainingPct}%</span>
          </div>
          <div className="text-xl font-bold font-mono text-slate-300 mt-1">
            {formatCurrency(remaining)}
            <span className="text-xs font-normal text-slate-400"> / mo</span>
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">
            Non-conflicting addressable pool
          </div>
        </div>
      </div>

      {/* ── PROPORTIONAL ALLOCATION BAR ──────────────────────────────────── */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>PORTFOLIO SAVINGS SHARE</span>
          <span>{decisionPct}% of addressable estate opportunity</span>
        </div>
        <div className="h-2.5 w-full bg-[#141B27] rounded-full overflow-hidden flex border border-[#1E2638]">
          <div
            style={{ width: `${decisionPct}%` }}
            className="bg-sky-400 transition-all duration-300 relative group"
            title={`This decision: ${formatCurrency(decision)}/mo`}
          />
          <div
            style={{ width: `${remainingPct}%` }}
            className="bg-emerald-500/60 transition-all duration-300"
            title={`Remaining compatible: ${formatCurrency(remaining)}/mo`}
          />
        </div>
        <div className="flex items-center gap-4 text-[10px] font-mono text-slate-400 pt-0.5">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-xs bg-sky-400" />
            <span>This Decision ({formatCurrency(decision)}/mo)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-xs bg-emerald-500/60" />
            <span>Remaining Compatible ({formatCurrency(remaining)}/mo)</span>
          </div>
        </div>
      </div>

      {/* ── PORTFOLIO RELATIONSHIPS & WHY COMPATIBLE / CONFLICTING ──────── */}
      <div className="bg-[#141B27]/40 rounded p-3.5 border border-[#1E2638]/70 space-y-3">
        <div className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300">
          Portfolio Relationships & Constraints
        </div>

        {isMutuallyExclusive ? (
          <div className="rounded border border-amber-500/30 bg-amber-500/5 p-3 space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-400">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>MUTUALLY EXCLUSIVE ALTERNATIVE DETECTED</span>
            </div>
            <p className="text-[11px] font-mono text-slate-300 leading-relaxed pl-6">
              Shares target resource <span className="text-amber-300 font-semibold">{targetResourceName || 'this instance'}</span> with{' '}
              <span className="text-amber-300 font-semibold">{alternativeTitle || 'alternate modernization candidate'}</span>.
            </p>
            <p className="text-[10px] font-mono text-slate-400 pl-6">
              Select one candidate. The Phase 6 portfolio engine excludes duplicate savings to prevent double-counting.
            </p>
          </div>
        ) : (
          <div className="rounded border border-emerald-500/30 bg-emerald-500/5 p-3 space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-400">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>COMPATIBLE WITH CURRENT PORTFOLIO</span>
            </div>
            <div className="text-[11px] font-mono text-slate-300 space-y-1 pl-6">
              <p>• No shared resource conflicts with other active opportunities.</p>
              <p>• No prerequisite dependency violations detected.</p>
              <p>• Savings can be combined without double-counting.</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-[11px] font-mono">
          <div className="flex items-center gap-2 p-2 rounded bg-[#0F141C] border border-[#1E2638]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="text-slate-300">{compatibleCount} compatible opportunities</span>
          </div>

          <div className="flex items-center gap-2 p-2 rounded bg-[#0F141C] border border-[#1E2638]">
            <Info className="w-3.5 h-3.5 text-sky-400 shrink-0" />
            <span className="text-slate-300">{dependencyCount} dependent opportunities</span>
          </div>

          <div className="flex items-center gap-2 p-2 rounded bg-[#0F141C] border border-[#1E2638]">
            <XCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="text-slate-300">{conflictCount} candidate alternatives</span>
          </div>
        </div>

        {/* ── DESCRIPTIVE PORTFOLIO RISK (NO MAGIC SCORE) ───────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-t border-[#1E2638]/50 pt-2.5 text-[10px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-slate-400" />
            <span>PORTFOLIO RISK DISTRIBUTION:</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-emerald-400 font-semibold">{riskProfile.countLow} LOW</span>
            <span className="text-slate-600">·</span>
            <span className="text-amber-400 font-semibold">{riskProfile.countMedium} MEDIUM</span>
            <span className="text-slate-600">·</span>
            <span className="text-rose-400 font-semibold">{riskProfile.countHigh} HIGH</span>
            <span className="text-slate-600">·</span>
            <span className="text-slate-300 font-mono">PEAK: {riskProfile.highestRisk}</span>
          </div>
        </div>

        {explanation && (
          <p className="text-[10px] font-mono text-slate-500 italic pt-1 border-t border-[#1E2638]/30">
            {explanation}
          </p>
        )}
      </div>
    </div>
  );
};

import React from 'react';
import { ShieldCheck, Layers, RotateCcw, FileSearch } from 'lucide-react';

export interface DecisionFactorsProps {
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  complexity: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  reversibility: 'HIGH' | 'MEDIUM' | 'LOW' | 'IMMEDIATE' | 'REVERSIBLE' | 'IRREVERSIBLE' | string;
  evidenceStrength: number | string; // e.g. 94 or "HIGH"
  riskNote?: string;
  complexityNote?: string;
  reversibilityNote?: string;
  evidenceNote?: string;
  className?: string;
}

export const CategoricalDecisionFactors: React.FC<DecisionFactorsProps> = ({
  riskLevel = 'LOW',
  complexity = 'LOW',
  reversibility = 'HIGH',
  evidenceStrength = 94,
  riskNote,
  complexityNote,
  reversibilityNote,
  evidenceNote,
  className = '',
}) => {
  // Normalize values to 1, 2, or 3
  const getRiskScore = (r: string) => {
    switch (r.toUpperCase()) {
      case 'HIGH':
        return { score: 3, label: 'HIGH', tone: 'critical' };
      case 'MEDIUM':
        return { score: 2, label: 'MEDIUM', tone: 'warning' };
      default:
        return { score: 1, label: 'LOW', tone: 'positive' };
    }
  };

  const getComplexityScore = (c: string) => {
    switch (c.toUpperCase()) {
      case 'HIGH':
        return { score: 3, label: 'HIGH', tone: 'critical' };
      case 'MEDIUM':
        return { score: 2, label: 'MEDIUM', tone: 'warning' };
      default:
        return { score: 1, label: 'LOW', tone: 'positive' };
    }
  };

  const getReversibilityScore = (rev: string) => {
    switch (rev.toUpperCase()) {
      case 'LOW':
      case 'IRREVERSIBLE':
        return { score: 1, label: 'LOW', tone: 'critical' };
      case 'MEDIUM':
      case 'REVERSIBLE':
        return { score: 2, label: 'MEDIUM', tone: 'warning' };
      default:
        return { score: 3, label: 'HIGH', tone: 'positive' };
    }
  };

  const getEvidenceScore = (ev: number | string) => {
    if (typeof ev === 'number') {
      if (ev >= 85) return { score: 3, label: `HIGH (${ev.toFixed(1)}%)`, tone: 'positive' };
      if (ev >= 60) return { score: 2, label: `MEDIUM (${ev.toFixed(1)}%)`, tone: 'warning' };
      return { score: 1, label: `INSUFFICIENT (${ev.toFixed(1)}%)`, tone: 'critical' };
    }
    const evStr = String(ev).toUpperCase();
    if (evStr === 'HIGH' || evStr === 'STRONG') {
      return { score: 3, label: 'HIGH', tone: 'positive' };
    }
    if (evStr === 'MEDIUM' || evStr === 'MODERATE') {
      return { score: 2, label: 'MEDIUM', tone: 'warning' };
    }
    return { score: 1, label: 'INSUFFICIENT', tone: 'critical' };
  };

  const risk = getRiskScore(riskLevel);
  const comp = getComplexityScore(complexity);
  const rev = getReversibilityScore(reversibility);
  const evid = getEvidenceScore(evidenceStrength);

  const getSegmentClass = (filled: boolean, tone: string) => {
    if (!filled) return 'bg-[#182030] border-[#222E42]';
    if (tone === 'critical') return 'bg-rose-500 border-rose-400';
    if (tone === 'warning') return 'bg-amber-400 border-amber-300';
    return 'bg-emerald-400 border-emerald-300';
  };

  const factors = [
    {
      name: 'RISK',
      icon: <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />,
      ...risk,
      note: riskNote || (risk.score === 1 ? 'Non-disruptive compute rightsizing; preserves workload semantics' : 'Workload architecture modification required'),
    },
    {
      name: 'COMPLEXITY',
      icon: <Layers className="w-3.5 h-3.5 text-slate-400" />,
      ...comp,
      note: complexityNote || (comp.score === 1 ? 'In-place instance change; no cluster migration or storage re-provisioning' : 'Multi-step configuration transition'),
    },
    {
      name: 'REVERSIBILITY',
      icon: <RotateCcw className="w-3.5 h-3.5 text-slate-400" />,
      ...rev,
      note: reversibilityNote || (rev.score === 3 ? 'Immediate restoration to original configuration in < 5 minutes' : 'Multi-step rollback with potential downtime'),
    },
    {
      name: 'EVIDENCE STRENGTH',
      icon: <FileSearch className="w-3.5 h-3.5 text-slate-400" />,
      ...evid,
      note: evidenceNote || 'Grounded in 30 days of continuous CloudWatch telemetry and billing line items',
    },
  ];

  return (
    <div className={`rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-4 select-none ${className}`}>
      <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-2.5">
        <div>
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            Categorical Decision Factors
          </h4>
          <p className="text-[11px] text-atlas-muted font-mono mt-0.5">
            Independent qualitative evaluations across 4 decoupled dimensions · No composite magic score
          </p>
        </div>
        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#141B27] border border-[#1E2638] text-slate-400">
          DECOUPLED EVALUATION
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {factors.map((f, idx) => (
          <div
            key={idx}
            className="bg-[#141B27]/60 p-3 rounded border border-[#1E2638]/70 flex flex-col justify-between space-y-2.5"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-slate-300 font-mono font-medium">
                  {f.icon}
                  <span>{f.name}</span>
                </div>
                <span
                  className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                    f.tone === 'critical'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : f.tone === 'warning'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  }`}
                >
                  {f.label}
                </span>
              </div>

              {/* 3-segment discrete visual meter (1/3, 2/3, 3/3) */}
              <div className="grid grid-cols-3 gap-1.5 mt-2 h-2">
                {[1, 2, 3].map((seg) => (
                  <div
                    key={seg}
                    className={`h-full rounded-xs transition-colors border ${getSegmentClass(
                      seg <= f.score,
                      f.tone
                    )}`}
                  />
                ))}
              </div>
            </div>

            <p className="text-[10px] font-mono text-slate-400 leading-relaxed border-t border-[#1E2638]/50 pt-2">
              {f.note}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

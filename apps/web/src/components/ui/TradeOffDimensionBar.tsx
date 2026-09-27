import React from 'react';

export interface TradeOffDimension {
  name: string;
  level: string; // e.g. "HIGH", "STRONG", "LOW", "MODERATE", "REVERSIBLE"
  score: number; // 1 to 5 (or 1 to 10)
  maxScore?: number;
  description?: string;
  tone?: 'positive' | 'warning' | 'critical' | 'neutral';
}

interface TradeOffDimensionBarProps {
  dimensions: TradeOffDimension[];
  title?: string;
  className?: string;
}

export const TradeOffDimensionBar: React.FC<TradeOffDimensionBarProps> = ({
  dimensions,
  title = 'Multi-Dimensional Trade-Off Evaluation',
  className = '',
}) => {
  return (
    <div className={`rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-4 select-none ${className}`}>
      <div className="border-b border-[#1E2638]/70 pb-2.5">
        <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300">
          {title}
        </h4>
        <p className="text-[11px] text-atlas-muted font-mono mt-0.5">
          Independent evaluations across 5 decoupled operational and risk dimensions (No composite scoring)
        </p>
      </div>

      <div className="space-y-3">
        {dimensions.map((dim, idx) => {
          const max = dim.maxScore || 5;

          const getSegmentColor = (filled: boolean) => {
            if (!filled) return 'bg-[#1A2333] border-[#1E293B]';
            if (dim.tone === 'critical') return 'bg-rose-500 border-rose-400';
            if (dim.tone === 'warning') return 'bg-amber-400 border-amber-300';
            if (dim.tone === 'positive') return 'bg-emerald-400 border-emerald-300';
            return 'bg-sky-400 border-sky-300';
          };

          return (
            <div key={idx} className="space-y-1.5 bg-[#141B27]/40 p-2.5 rounded border border-[#1E2638]/50">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium">{dim.name}</span>
                <span className="font-mono text-[11px] font-semibold text-atlas-text bg-[#1A2234] px-2 py-0.5 rounded border border-[#1E2638]">
                  {dim.level}
                </span>
              </div>

              {/* Segmented Bar (10 mini-segments) */}
              <div className="grid grid-cols-10 gap-1 h-2">
                {Array.from({ length: 10 }).map((_, segIdx) => {
                  const segRatio = (segIdx + 1) / 10;
                  const isFilled = segRatio <= (dim.score / max);
                  return (
                    <div
                      key={segIdx}
                      className={`h-full rounded-xs transition-colors border ${getSegmentColor(isFilled)}`}
                    />
                  );
                })}
              </div>

              {dim.description && (
                <div className="text-[10px] text-atlas-muted font-mono pt-0.5">
                  {dim.description}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

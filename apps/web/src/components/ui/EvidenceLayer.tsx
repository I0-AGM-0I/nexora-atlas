import React from 'react';
import { EpistemicBadge, EpistemicClassification } from './EpistemicBadge';
import { Shield, Clock } from 'lucide-react';

export interface EvidenceItem {
  epistemicClass: EpistemicClassification | string;
  source: string;
  statement: string;
  metricValue?: string;
  timestamp?: string;
}

interface EvidenceLayerProps {
  items: EvidenceItem[];
  title?: string;
  className?: string;
}

export const EvidenceLayer: React.FC<EvidenceLayerProps> = ({
  items,
  title = 'Authoritative Evidence Layer',
  className = '',
}) => {
  if (!items || items.length === 0) return null;

  return (
    <div className={`rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-3 select-none ${className}`}>
      <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-2.5">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-atlas-primary" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300">
            {title}
          </h4>
        </div>
        <span className="text-[10px] font-mono text-atlas-muted">
          {items.length} verified statements
        </span>
      </div>

      <div className="space-y-2.5">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="flex items-start gap-3 text-xs bg-[#141B27]/60 p-2.5 rounded border border-[#1E2638]/60 hover:border-[#1E2638] transition-colors"
          >
            <div className="pt-0.5">
              <EpistemicBadge classification={item.epistemicClass} size="xs" />
            </div>

            <div className="flex-1 min-w-0 space-y-1">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="text-slate-200 font-medium leading-relaxed">{item.statement}</span>
                {item.metricValue && (
                  <span className="font-mono text-sky-400 font-semibold px-1.5 py-0.2 rounded bg-sky-950/40 border border-sky-500/30">
                    {item.metricValue}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 text-[10px] font-mono text-atlas-muted">
                <span>Source: <span className="text-slate-400">{item.source}</span></span>
                {item.timestamp && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{item.timestamp}</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

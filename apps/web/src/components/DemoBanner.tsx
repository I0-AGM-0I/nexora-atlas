import React from 'react';
import { ShieldCheck } from 'lucide-react';

interface DemoBannerProps {
  isDemo?: boolean;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({ isDemo = true }) => {
  if (!isDemo) return null;

  return (
    <div
      role="region"
      aria-label="Demo environment notification"
      className="w-full bg-[#0A0D14] border-b border-[#1E2638] px-4 py-1 flex items-center justify-between text-[11px] font-mono select-none"
    >
      <div className="flex items-center gap-2.5">
        <span className="inline-flex items-center gap-1.5 font-semibold tracking-wider text-[10px] text-amber-400 bg-amber-400/10 px-1.5 py-0.2 rounded border border-amber-400/30">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
          DEMO ENVIRONMENT
        </span>
        <span className="text-atlas-muted hidden sm:inline">
          Synthetic AWS Environment · 3 Accounts · 58 Monitored Resources · 90 Days Daily History
        </span>
      </div>

      <div className="flex items-center gap-3 text-atlas-muted text-[10px]">
        <span className="flex items-center gap-1 text-slate-400">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          <span>Zero Live Mutations</span>
        </span>
      </div>
    </div>
  );
};

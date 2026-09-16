import React from 'react';
import { Database } from 'lucide-react';

interface DemoBannerProps {
  isDemo?: boolean;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({ isDemo = true }) => {
  if (!isDemo) return null;

  return (
    <div
      role="region"
      aria-label="Demo environment notification"
      className="w-full bg-amber-500/10 border-b border-amber-500/25 px-4 py-1.5 flex items-center justify-between text-xs text-amber-300 font-mono select-none"
    >
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
        </span>
        <span className="font-semibold tracking-wider uppercase text-[11px] bg-amber-500/20 px-1.5 py-0.5 rounded border border-amber-500/30">
          DEMO ENVIRONMENT
        </span>
        <span className="text-atlas-secondary hidden md:inline">
          Operating on deterministic synthetic dataset (Nexora Labs) • No live AWS mutation enabled
        </span>
      </div>

      <div className="flex items-center gap-3 text-atlas-muted text-[11px]">
        <span className="hidden sm:inline flex items-center gap-1">
          <Database className="w-3.5 h-3.5 text-amber-400 inline" />
          <span>PostgreSQL / SQLite Compatible</span>
        </span>
      </div>
    </div>
  );
};

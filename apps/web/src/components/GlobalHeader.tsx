import React from 'react';
import { useLocation } from 'react-router-dom';
import { AtlasPulse } from './AtlasPulse';
import { spineCoordinates } from './NavigationSpine';
import { Search, Sparkles, ShieldCheck } from 'lucide-react';

interface GlobalHeaderProps {
  onOpenCommandPalette: () => void;
  onOpenAskAtlas: () => void;
}

export const GlobalHeader: React.FC<GlobalHeaderProps> = ({
  onOpenCommandPalette,
  onOpenAskAtlas,
}) => {
  const location = useLocation();

  // Find active coordinate matching current route
  const currentCoord = spineCoordinates.find((item) => {
    if (location.pathname === item.path) return true;
    if (item.aliasPaths && item.aliasPaths.includes(location.pathname)) return true;
    if (item.path !== '/' && item.path !== '/dashboard' && location.pathname.startsWith(item.path)) {
      return true;
    }
    return false;
  }) || spineCoordinates[0];

  return (
    <header className="h-12 w-full bg-[#080B10] border-b border-[#1E2638] px-4 flex items-center justify-between font-mono text-xs select-none shrink-0 z-20">
      {/* ── LEFT: Atlas Brand + Active Coordinate Context ────────────────────── */}
      <div className="flex items-center gap-3">
        <span className="font-bold tracking-widest text-slate-200 text-[13px]">ATLAS</span>
        <span className="text-[#334155]">/</span>
        <div className="flex items-center gap-1.5 text-slate-300">
          <span className="text-sky-400 font-bold">{currentCoord.coordinate}</span>
          <span className="text-slate-400">/</span>
          <span className="tracking-wider uppercase text-[11px] font-semibold text-slate-200">
            {currentCoord.name}
          </span>
        </div>
      </div>

      {/* ── RIGHT: Environment Scope + Pulse + Shortcuts + Ask Atlas ──────────── */}
      <div className="flex items-center gap-3">
        {/* Environment & Trust Boundary Pills */}
        <div className="hidden md:flex items-center gap-2 text-[10px] text-slate-400">
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            PROD
          </span>
          <span className="text-[#334155]">·</span>
          <span>AP-SOUTH-1</span>
          <span className="text-[#334155]">·</span>
          <span className="text-slate-400 flex items-center gap-1 font-semibold">
            <ShieldCheck className="w-3 h-3 text-slate-400" />
            READ ONLY
          </span>
        </div>

        <span className="hidden md:inline text-[#334155]">|</span>

        {/* Global Operational Inspection Indicator */}
        <AtlasPulse />

        {/* Command Palette Trigger (Ctrl/Cmd + K) */}
        <button
          type="button"
          onClick={onOpenCommandPalette}
          className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#0F141C] border border-[#1E2638] hover:border-slate-500 text-slate-400 hover:text-slate-200 transition-colors text-[11px] focus:outline-none focus:ring-1 focus:ring-sky-500/50"
          title="Search or execute navigation commands (Ctrl+K)"
          aria-label="Open command palette"
        >
          <Search className="w-3 h-3 text-slate-400" />
          <span className="hidden sm:inline">Search</span>
          <kbd className="text-[9px] bg-[#141B27] px-1 py-0.2 rounded border border-[#1E2638] text-slate-400 font-mono">
            Ctrl+K
          </kbd>
        </button>

        {/* Ask Atlas Trigger (Ctrl/Cmd + J) */}
        <button
          type="button"
          onClick={onOpenAskAtlas}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-sky-950/40 border border-sky-500/40 hover:bg-sky-900/40 text-sky-400 hover:text-sky-300 font-semibold transition-colors text-[11px] focus:outline-none focus:ring-1 focus:ring-sky-500"
          title="Ask Atlas Analytical Explanation (Ctrl+J)"
          aria-label="Ask Atlas"
        >
          <Sparkles className="w-3 h-3 text-sky-400" />
          <span>Ask Atlas</span>
          <kbd className="hidden sm:inline text-[9px] bg-sky-900/50 px-1 py-0.2 rounded border border-sky-500/30 text-sky-300 font-mono">
            Ctrl+J
          </kbd>
        </button>
      </div>
    </header>
  );
};

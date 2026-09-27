import React, { useState } from 'react';
import { Search, ChevronDown, Building2, Sparkles } from 'lucide-react';
import { AtlasDataStatusModal } from './AtlasDataStatusModal';

interface TopbarProps {
  onOpenCommandPalette: () => void;
  onOpenAskAtlas: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenCommandPalette, onOpenAskAtlas }) => {
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);

  return (
    <>
      <header className="h-14 border-b border-atlas-border bg-[#0B0F17]/95 backdrop-blur px-5 flex items-center justify-between z-10 select-none">
        {/* Left: Organization & Scope Context */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-atlas-border bg-atlas-elevated/70 text-xs font-medium text-atlas-text hover:border-slate-700 cursor-pointer transition-colors">
            <Building2 className="w-3.5 h-3.5 text-atlas-primary" />
            <span className="font-semibold">Nexora Labs Inc.</span>
            <span className="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1 py-0.2 rounded border border-emerald-400/30">
              PROD
            </span>
            <ChevronDown className="w-3 h-3 text-atlas-muted ml-0.5" />
          </div>

          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded border border-atlas-border/70 bg-atlas-surface/40 text-[11px] font-mono text-atlas-muted">
            <span className="text-slate-300 font-semibold">90 DAYS</span>
            <span>·</span>
            <span>INR (₹)</span>
            <span>·</span>
            <span>Asia/Kolkata</span>
          </div>
        </div>

        {/* Center: Command Palette Trigger */}
        <div className="flex-1 max-w-md mx-4">
          <button
            type="button"
            onClick={onOpenCommandPalette}
            aria-label="Open command palette"
            className="w-full flex items-center justify-between px-3 py-1.5 rounded-md border border-atlas-border bg-[#070A0F] text-xs text-atlas-muted hover:border-atlas-primary/50 hover:text-atlas-secondary transition-all focus:outline-none focus:ring-1 focus:ring-atlas-primary"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-atlas-muted" />
              <span className="truncate">Search resources, drivers, changes...</span>
            </div>
            <div className="flex items-center gap-1 font-mono text-[10px] bg-atlas-elevated px-1.5 py-0.5 rounded border border-atlas-border text-atlas-secondary">
              <kbd className="font-sans">Ctrl</kbd>+<kbd>K</kbd>
            </div>
          </button>
        </div>

        {/* Right: Ask Atlas & Trust Status Pill */}
        <div className="flex items-center gap-3">
          {/* Global Ask Atlas Trigger */}
          <button
            type="button"
            onClick={onOpenAskAtlas}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-atlas-primary/10 hover:bg-atlas-primary/20 text-atlas-primary border border-atlas-primary/30 text-xs font-medium transition-all shadow-sm focus:outline-none focus:ring-1 focus:ring-atlas-primary"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="font-semibold">Ask Atlas</span>
            <span className="hidden sm:inline font-mono text-[10px] text-atlas-primary/70 bg-atlas-primary/10 px-1 py-0.2 rounded">
              Ctrl+J
            </span>
          </button>

          {/* System Trust Status Pill */}
          <button
            type="button"
            onClick={() => setIsStatusModalOpen(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-emerald-500/30 bg-emerald-950/20 text-[11px] font-mono text-emerald-400 hover:bg-emerald-950/40 hover:border-emerald-500/50 transition-colors"
            title="Click to view Atlas Data Status & Trust Boundary"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-semibold">Connected</span>
          </button>
        </div>
      </header>

      {/* Trust Status Flyout Modal */}
      <AtlasDataStatusModal
        isOpen={isStatusModalOpen}
        onClose={() => setIsStatusModalOpen(false)}
      />
    </>
  );
};

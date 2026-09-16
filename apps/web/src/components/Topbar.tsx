import React from 'react';
import { Search, Calendar, Bell, ChevronDown, Building2 } from 'lucide-react';

interface TopbarProps {
  onOpenCommandPalette: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenCommandPalette }) => {
  return (
    <header className="h-14 border-b border-atlas-border bg-atlas-surface/80 backdrop-blur px-5 flex items-center justify-between z-10 select-none">
      {/* Left: Organization Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-atlas-border bg-atlas-elevated/80 text-xs font-medium text-atlas-text hover:border-slate-700 cursor-pointer transition-colors">
          <Building2 className="w-3.5 h-3.5 text-atlas-primary" />
          <span>Nexora Labs</span>
          <span className="text-[10px] text-atlas-muted font-mono bg-black/40 px-1 py-0.2 rounded">
            PROD
          </span>
          <ChevronDown className="w-3 h-3 text-atlas-muted ml-1" />
        </div>

        {/* Date Range Selector Stub */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-atlas-border bg-atlas-surface text-xs text-atlas-secondary hover:text-atlas-text hover:border-slate-700 cursor-pointer transition-colors">
          <Calendar className="w-3.5 h-3.5 text-atlas-muted" />
          <span>Last 30 Days</span>
          <ChevronDown className="w-3 h-3 text-atlas-muted ml-1" />
        </div>
      </div>

      {/* Center: Command Palette Trigger */}
      <div className="flex-1 max-w-md mx-4">
        <button
          type="button"
          onClick={onOpenCommandPalette}
          aria-label="Open command palette"
          className="w-full flex items-center justify-between px-3 py-1.5 rounded-md border border-atlas-border bg-[#0A0E17] text-xs text-atlas-muted hover:border-atlas-primary/50 hover:text-atlas-secondary transition-all focus:outline-none focus:ring-1 focus:ring-atlas-primary"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-atlas-muted" />
            <span>Search resources, recommendations, services...</span>
          </div>
          <div className="flex items-center gap-1 font-mono text-[10px] bg-atlas-elevated px-1.5 py-0.5 rounded border border-atlas-border text-atlas-secondary">
            <kbd className="font-sans">Ctrl</kbd>+<kbd>K</kbd>
          </div>
        </button>
      </div>

      {/* Right: Notifications & User Avatar */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Notifications (3 unread)"
          className="relative p-2 rounded-md text-atlas-secondary hover:text-atlas-text hover:bg-atlas-surface border border-transparent hover:border-atlas-border transition-colors"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-atlas-primary animate-pulse"></span>
        </button>

        <div className="flex items-center gap-2 pl-2 border-l border-atlas-border">
          <div className="w-7 h-7 rounded bg-atlas-elevated border border-atlas-border flex items-center justify-center text-xs font-mono font-semibold text-atlas-primary">
            AK
          </div>
          <span className="hidden md:inline text-xs text-atlas-text font-medium">Principal Architect</span>
        </div>
      </div>
    </header>
  );
};

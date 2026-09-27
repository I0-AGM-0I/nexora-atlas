import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { NavigationSpine } from './NavigationSpine';
import { GlobalHeader } from './GlobalHeader';
import { DemoBanner } from './DemoBanner';
import { CommandPalette } from './CommandPalette';
import { AskAtlasDrawer } from './ai/AskAtlasDrawer';
import { AskAtlasProvider, useAskAtlas } from '../lib/AskAtlasContext';
import { InvestigationProvider } from '../lib/InvestigationContext';

interface AppShellProps {
  isDemo?: boolean;
}

const AppShellContent: React.FC<AppShellProps> = ({ isDemo = true }) => {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const { isAskAtlasOpen, activeContext, openAskAtlas, closeAskAtlas, clearActiveContext } = useAskAtlas();

  // Global Ctrl+K (search) and Ctrl+J (Ask Atlas) listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K / Cmd+K -> Command Palette
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
      // Ctrl+J / Cmd+J -> Ask Atlas Drawer
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'j') {
        e.preventDefault();
        if (isAskAtlasOpen) {
          closeAskAtlas();
        } else {
          openAskAtlas();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAskAtlasOpen, openAskAtlas, closeAskAtlas]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-atlas-bg text-atlas-text">
      {/* Refined Persistent Demo Mode Status Pill Banner */}
      <DemoBanner isDemo={isDemo} />

      {/* Main Workspace Frame */}
      <div className="flex flex-1 overflow-hidden">
        {/* Atlas Navigation Spine (48-60px Coordinate Rail) */}
        <NavigationSpine />

        {/* Content Column */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <GlobalHeader
            onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
            onOpenAskAtlas={() => openAskAtlas()}
          />

          <main className="flex-1 overflow-y-auto p-6 bg-atlas-bg">
            <div className="max-w-7xl mx-auto">
              <Outlet />
            </div>
          </main>

          {/* Operational Deployment & Commit Status Footer */}
          <footer className="h-6 shrink-0 bg-[#0A0D14] border-t border-[#1E2638] px-4 flex items-center justify-between text-[11px] font-mono text-slate-500 select-none z-10">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-slate-400">NEXORA ATLAS</span>
              <span className="text-slate-600">|</span>
              <span className="hidden sm:inline">SYSTEM OPERATIONAL</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span>Commit:</span>
              <span className="text-slate-300 font-bold" title={import.meta.env.VITE_COMMIT_SHA || 'dev'}>
                {(import.meta.env.VITE_COMMIT_SHA || 'dev').length === 40
                  ? (import.meta.env.VITE_COMMIT_SHA as string).substring(0, 7)
                  : (import.meta.env.VITE_COMMIT_SHA || 'dev')}
              </span>
            </div>
          </footer>
        </div>
      </div>

      {/* Global Command Palette Modal */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />

      {/* Global Contextual Ask Atlas Drawer */}
      <AskAtlasDrawer
        isOpen={isAskAtlasOpen}
        onClose={closeAskAtlas}
        context={activeContext}
        onClearContext={clearActiveContext}
      />
    </div>
  );
};

export const AppShell: React.FC<AppShellProps> = (props) => {
  return (
    <InvestigationProvider>
      <AskAtlasProvider>
        <AppShellContent {...props} />
      </AskAtlasProvider>
    </InvestigationProvider>
  );
};

import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { DemoBanner } from './DemoBanner';
import { CommandPalette } from './CommandPalette';

interface AppShellProps {
  isDemo?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({ isDemo = true }) => {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-atlas-bg text-atlas-text">
      {/* Prominent Demo Mode Banner */}
      <DemoBanner isDemo={isDemo} />

      {/* Main Workspace Frame */}
      <div className="flex flex-1 overflow-hidden">
        {/* Persistent Enterprise Sidebar */}
        <Sidebar isDemo={isDemo} />

        {/* Content Column */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <Topbar onOpenCommandPalette={() => setIsCommandPaletteOpen(true)} />

          <main className="flex-1 overflow-y-auto p-6 bg-atlas-bg">
            <div className="max-w-7xl mx-auto">
              <Outlet />
            </div>
          </main>
        </div>
      </div>

      {/* Global Command Palette Modal */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
    </div>
  );
};

import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { AtlasMark } from './ui/AtlasMark';
import {
  ChevronRight,
  X,
} from 'lucide-react';

export interface SpineCoordinate {
  id: string;
  coordinate: string;
  name: string;
  path: string;
  aliasPaths?: string[];
  badgeKey?: 'changes' | 'optimization';
}

export const spineCoordinates: SpineCoordinate[] = [
  { id: 'dashboard', coordinate: '01', name: 'Command Center', path: '/dashboard', aliasPaths: ['/'] },
  { id: 'spend', coordinate: '02', name: 'Spend', path: '/spend' },
  { id: 'forecast', coordinate: '03', name: 'Forecast', path: '/forecast' },
  { id: 'changes', coordinate: '04', name: 'Changes', path: '/changes', aliasPaths: ['/anomalies'] },
  { id: 'optimization', coordinate: '05', name: 'Optimization', path: '/optimization' },
  { id: 'scenarios', coordinate: '06', name: 'Scenarios', path: '/scenarios' },
  { id: 'resources', coordinate: '07', name: 'Resources', path: '/resources' },
  { id: 'integrations', coordinate: '08', name: 'Integrations', path: '/integrations' },
  { id: 'settings', coordinate: '09', name: 'Settings', path: '/settings' },
];

interface NavigationSpineProps {
  onOpenHelp?: () => void;
}

export const NavigationSpine: React.FC<NavigationSpineProps> = ({ onOpenHelp }) => {
  const location = useLocation();
  const [isExpandedOverlay, setIsExpandedOverlay] = useState(false);
  const [hoveredCoord, setHoveredCoord] = useState<string | null>(null);

  const isCurrentActive = (item: SpineCoordinate) => {
    if (location.pathname === item.path) return true;
    if (item.aliasPaths && item.aliasPaths.includes(location.pathname)) return true;
    if (item.path !== '/' && item.path !== '/dashboard' && location.pathname.startsWith(item.path)) {
      return true;
    }
    return false;
  };

  return (
    <>
      {/* ── NARROW VERTICAL COORDINATE RAIL (48-60px) ────────────────────────── */}
      <nav
        role="navigation"
        aria-label="Coordinate Navigation Rail"
        className="relative z-30 flex flex-col items-center justify-between w-14 bg-[#080B10] border-r border-[#1E2638] py-4 select-none shrink-0"
      >
        {/* Top: Atlas Geometric Mark */}
        <div className="flex flex-col items-center pb-3">
          <NavLink
            to="/dashboard"
            className="p-1 rounded hover:bg-[#141B27] transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500/50"
            title="NEXORA ATLAS — Command Center"
            aria-label="Atlas Command Center"
          >
            <AtlasMark size={28} active={location.pathname === '/dashboard' || location.pathname === '/'} />
          </NavLink>
        </div>

        {/* Middle: Coordinate Rail with Vertical Trace Line */}
        <div className="relative flex flex-col items-center justify-center flex-1 my-2 py-4 space-y-4">
          {/* Subtle vertical spine guide */}
          <div className="absolute top-2 bottom-2 left-1/2 -translate-x-1/2 w-[1px] bg-[#17202D]" />

          {spineCoordinates.map((item) => {
            const active = isCurrentActive(item);
            const isHovered = hoveredCoord === item.coordinate;

            return (
              <div
                key={item.id}
                className="relative flex items-center justify-center w-full"
                onMouseEnter={() => setHoveredCoord(item.coordinate)}
                onMouseLeave={() => setHoveredCoord(null)}
              >
                <NavLink
                  to={item.path}
                  className={`group relative flex items-center justify-center w-8 h-8 rounded text-[11px] font-mono transition-all duration-150 focus:outline-none focus:ring-1 focus:ring-sky-500/50 ${
                    active
                      ? 'text-sky-400 font-bold bg-[#0F141C]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#141B27]'
                  }`}
                  aria-current={active ? 'page' : undefined}
                  aria-label={`${item.coordinate} — ${item.name}`}
                >
                  {/* Active Coordinate Dot */}
                  {active && (
                    <span className="absolute -left-1.5 w-1.5 h-1.5 rounded-full bg-sky-400 shadow-sm" />
                  )}

                  {/* 2-Digit Coordinate Identifier */}
                  <span>{item.coordinate}</span>
                </NavLink>

                {/* Subtle 1px Horizontal Coordinate Trace Line toward canvas */}
                {active && (
                  <div
                    className="absolute right-0 top-1/2 -translate-y-1/2 h-[1px] w-3 bg-sky-500/60 pointer-events-none transition-opacity duration-200"
                    aria-hidden="true"
                  />
                )}

                {/* Hover Flyout Destination Tag */}
                {isHovered && !isExpandedOverlay && (
                  <div className="absolute left-14 top-1/2 -translate-y-1/2 ml-2 px-2.5 py-1 bg-[#0F141C] border border-[#1E2638] rounded text-xs font-mono text-slate-200 whitespace-nowrap shadow-xl z-50 pointer-events-none animate-in fade-in duration-100 flex items-center gap-2">
                    <span className="text-sky-400 font-bold">{item.coordinate}</span>
                    <span className="text-slate-400">/</span>
                    <span className="uppercase tracking-wider">{item.name}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom Actions: Expand Drawer + Help Glyph */}
        <div className="flex flex-col items-center space-y-3 pt-3 border-t border-[#17202D]">
          {/* Overlay Expand Toggle */}
          <button
            type="button"
            onClick={() => setIsExpandedOverlay((prev) => !prev)}
            className="p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-[#141B27] transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500/50"
            title="Expand Navigation Overlay"
            aria-label="Expand navigation"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>

          {/* Help Circle Glyph */}
          <button
            type="button"
            onClick={onOpenHelp}
            className="w-6 h-6 rounded-full bg-[#0F141C] border border-[#1E2638] flex items-center justify-center text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-sky-500/50"
            title="Atlas Navigation & Methodology Help"
            aria-label="Help"
          >
            ?
          </button>
        </div>
      </nav>

      {/* ── EXPANDED NAVIGATION OVERLAY (Does not push content) ──────────────── */}
      {isExpandedOverlay && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-[2px] flex animate-in fade-in duration-150"
          onClick={() => setIsExpandedOverlay(false)}
        >
          <div
            className="w-64 bg-[#0A0D14] border-r border-[#1E2638] h-full p-4 flex flex-col justify-between shadow-2xl select-none"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Expanded Navigation"
          >
            <div>
              {/* Header */}
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#1E2638]">
                <div className="flex items-center gap-2.5">
                  <AtlasMark size={24} active />
                  <span className="font-mono font-bold text-xs tracking-wider text-slate-200">
                    NEXORA ATLAS
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsExpandedOverlay(false)}
                  className="p-1 text-slate-400 hover:text-slate-200"
                  aria-label="Close expanded navigation"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Coordinates List */}
              <div className="space-y-1 font-mono text-xs">
                {spineCoordinates.map((item) => {
                  const active = isCurrentActive(item);
                  return (
                    <NavLink
                      key={item.id}
                      to={item.path}
                      onClick={() => setIsExpandedOverlay(false)}
                      className={`flex items-center justify-between px-3 py-2 rounded transition-colors ${
                        active
                          ? 'bg-[#141B27] text-sky-400 font-bold border-l-2 border-sky-400'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-[#0F141C]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-slate-400 font-mono">{item.coordinate}</span>
                        <span>{item.name}</span>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 opacity-40" />
                    </NavLink>
                  );
                })}
              </div>
            </div>

            {/* Footer Trust Boundary Reminder */}
            <div className="pt-3 border-t border-[#1E2638] text-[10px] font-mono text-slate-400">
              <div>STRICT READ-ONLY ENFORCED</div>
              <div className="text-[9px] text-slate-400 mt-0.5">Zero live mutation boundary active.</div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

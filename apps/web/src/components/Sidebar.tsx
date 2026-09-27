import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart3,
  AlertTriangle,
  Zap,
  GitFork,
  TrendingUp,
  Server,
  CloudCog,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../lib/api';

interface SidebarProps {
  isDemo?: boolean;
}

interface NavItemConfig {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badgeKey?: 'anomalies' | 'optimization';
}

interface NavSection {
  title: string;
  items: NavItemConfig[];
}

const navSections: NavSection[] = [
  {
    title: 'OVERVIEW',
    items: [
      { name: 'Command Center', path: '/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    title: 'FINANCIAL',
    items: [
      { name: 'Spend', path: '/spend', icon: BarChart3 },
      { name: 'Forecast', path: '/forecast', icon: TrendingUp },
    ],
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { name: 'Changes', path: '/changes', icon: AlertTriangle, badgeKey: 'anomalies' },
      { name: 'Optimization', path: '/optimization', icon: Zap, badgeKey: 'optimization' },
      { name: 'Scenarios', path: '/scenarios', icon: GitFork },
    ],
  },
  {
    title: 'INFRASTRUCTURE',
    items: [
      { name: 'Resources', path: '/resources', icon: Server },
      { name: 'Integrations', path: '/integrations', icon: CloudCog },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { name: 'Settings', path: '/settings', icon: Settings },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ isDemo = true }) => {
  const [badgeCounts, setBadgeCounts] = useState<{ anomalies?: number; optimization?: number }>({});

  useEffect(() => {
    Promise.allSettled([api.getDashboardSummary(), api.getOptimization()]).then(
      ([summaryRes, optRes]) => {
        const counts: { anomalies?: number; optimization?: number } = {};
        if (summaryRes.status === 'fulfilled') {
          counts.anomalies = summaryRes.value.active_anomalies;
        }
        if (optRes.status === 'fulfilled') {
          counts.optimization = optRes.value.opportunity_count;
        }
        setBadgeCounts(counts);
      }
    );
  }, []);

  return (
    <aside
      className="w-60 flex-shrink-0 bg-[#0A0E17] border-r border-atlas-border flex flex-col justify-between select-none h-full"
      aria-label="Sidebar navigation"
    >
      {/* Brand Header */}
      <div>
        <div className="h-14 border-b border-atlas-border px-5 flex items-center gap-3">
          <div className="w-7 h-7 rounded bg-atlas-primary/15 border border-atlas-primary/40 flex items-center justify-center">
            <span className="font-mono font-bold text-xs text-atlas-primary tracking-tighter">NX</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold tracking-wider text-sm text-atlas-text">ATLAS</span>
              <span className="text-[9px] font-mono text-atlas-primary bg-atlas-primary/10 px-1 py-0.2 rounded border border-atlas-primary/20">
                COMMAND
              </span>
            </div>
            <span className="text-[10px] text-atlas-muted font-mono tracking-tight">Financial Intelligence</span>
          </div>
        </div>

        {/* 5-Tier Intent Navigation Sections */}
        <nav className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-140px)]" aria-label="Main Navigation">
          {navSections.map((section) => (
            <div key={section.title} className="space-y-1">
              <div className="px-2.5 py-1 text-[10px] font-mono font-semibold text-atlas-muted uppercase tracking-wider">
                {section.title}
              </div>
              {section.items.map((item) => {
                const Icon = item.icon;
                const count = item.badgeKey ? badgeCounts[item.badgeKey] : undefined;
                const badgeText = count !== undefined && count > 0 ? String(count) : undefined;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-atlas-primary ${
                        isActive
                          ? 'bg-atlas-elevated text-atlas-primary font-semibold border border-atlas-border/90 shadow-sm'
                          : 'text-atlas-secondary hover:text-atlas-text hover:bg-atlas-surface/60 border border-transparent'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{item.name}</span>
                    </div>
                    {badgeText && (
                      <span
                        className={`text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded border ${
                          item.badgeKey === 'anomalies'
                            ? 'bg-amber-400/10 text-amber-400 border-amber-400/30'
                            : 'bg-emerald-400/10 text-emerald-400 border-emerald-400/30'
                        }`}
                      >
                        {badgeText}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer Connection Status & Trust Badge */}
      <div className="p-3.5 border-t border-atlas-border bg-atlas-surface/30">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            <span className="font-semibold text-atlas-text font-mono text-xs">AWS Connected</span>
          </div>
          <span className="text-[11px] font-mono text-atlas-muted">3 accounts</span>
        </div>
        <div className="mt-2 text-[10px] text-atlas-muted font-mono flex items-center justify-between">
          <div className="flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-atlas-primary" />
            <span>Read-Only Boundary</span>
          </div>
          {isDemo && (
            <span className="text-[9px] font-mono text-amber-400 bg-amber-400/10 px-1 py-0.2 rounded border border-amber-400/25">
              DEMO
            </span>
          )}
        </div>
      </div>
    </aside>
  );
};

import React from 'react';
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

interface SidebarProps {
  isDemo?: boolean;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Spend', path: '/spend', icon: BarChart3 },
  { name: 'Anomalies', path: '/anomalies', icon: AlertTriangle, badge: '7' },
  { name: 'Optimization', path: '/optimization', icon: Zap, badge: '23' },
  { name: 'Scenarios', path: '/scenarios', icon: GitFork },
  { name: 'Forecast', path: '/forecast', icon: TrendingUp },
  { name: 'Resources', path: '/resources', icon: Server },
  { name: 'Integrations', path: '/integrations', icon: CloudCog },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ isDemo = true }) => {
  return (
    <aside
      className="w-64 flex-shrink-0 bg-[#0A0E17] border-r border-atlas-border flex flex-col justify-between select-none h-full"
      aria-label="Sidebar navigation"
    >
      {/* Brand Header */}
      <div>
        <div className="h-14 border-b border-atlas-border px-5 flex items-center gap-3">
          <div className="w-7 h-7 rounded bg-atlas-primary/20 border border-atlas-primary/50 flex items-center justify-center">
            <span className="font-mono font-bold text-xs text-atlas-primary tracking-tighter">NX</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold tracking-wider text-sm text-atlas-text">ATLAS</span>
              <span className="text-[10px] font-mono text-atlas-primary bg-atlas-primary/10 px-1 py-0.2 rounded border border-atlas-primary/20">
                FINOPS
              </span>
            </div>
            <span className="text-[10px] text-atlas-muted font-mono tracking-tight">Cost Intelligence</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-atlas-primary ${
                    isActive
                      ? 'bg-atlas-elevated text-atlas-primary font-semibold border border-atlas-border/80'
                      : 'text-atlas-secondary hover:text-atlas-text hover:bg-atlas-surface/60'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[11px] font-mono font-semibold px-1.5 py-0.5 rounded bg-atlas-elevated text-atlas-secondary border border-atlas-border">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Connection Status */}
      <div className="p-4 border-t border-atlas-border bg-atlas-surface/30">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-atlas-muted font-mono text-[11px]">PROVIDER:</span>
            <span className="font-semibold text-atlas-text font-mono text-xs">AWS</span>
          </div>
          {isDemo ? (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-mono text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/25">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
              DEMO
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-mono text-atlas-success bg-atlas-success/10 px-2 py-0.5 rounded border border-atlas-success/25">
              <span className="h-1.5 w-1.5 rounded-full bg-atlas-success"></span>
              CONNECTED
            </span>
          )}
        </div>
        <div className="mt-2 text-[10px] text-atlas-muted font-mono flex items-center gap-1">
          <ShieldCheck className="w-3 h-3 text-atlas-primary" />
          <span>Read-Only Ingestion IAM</span>
        </div>
      </div>
    </aside>
  );
};

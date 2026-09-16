import React from 'react';
import { LayoutDashboard, Clock } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Overview Dashboard</h1>
            <Badge variant="info">Phase 1 Foundation</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            High-level executive telemetry, total technology spend, and critical optimization flags.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /dashboard</span>
        </div>
      </div>

      {/* Architectural Placeholder Container */}
      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-primary/10 text-atlas-primary flex items-center justify-center mb-3">
          <LayoutDashboard className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">Overview Dashboard View</h3>
        <p className="text-xs text-atlas-muted max-w-md mb-4">
          Core KPI metrics (total spend, MoM change, potential savings, anomalies, and cost trend chart) will connect to the Demo Data Engine in Phase 4.
        </p>
        <div className="text-[11px] font-mono text-atlas-secondary bg-atlas-elevated px-3 py-1.5 rounded border border-atlas-border">
          Status: Ready for Phase 4 Implementation
        </div>
      </Card>
    </div>
  );
};

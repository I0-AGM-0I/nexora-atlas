import React from 'react';
import { Server, Clock } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const ResourcesPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Resource Inventory</h1>
            <Badge variant="info">Phase 1 Foundation</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Discovered cloud infrastructure assets across compute, database, storage, and networking.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /resources</span>
        </div>
      </div>

      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-primary/10 text-atlas-primary flex items-center justify-center mb-3">
          <Server className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">Resource Catalog View</h3>
        <p className="text-xs text-atlas-muted max-w-md mb-4">
          Detailed inventory tables with resource ARNs, native IDs, tags, running states, and attached cost telemetry.
        </p>
        <div className="text-[11px] font-mono text-atlas-secondary bg-atlas-elevated px-3 py-1.5 rounded border border-atlas-border">
          Status: Ready for Resource Catalog Integration
        </div>
      </Card>
    </div>
  );
};

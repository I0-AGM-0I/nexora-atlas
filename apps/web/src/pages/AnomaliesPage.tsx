import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const AnomaliesPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Anomaly Center</h1>
            <Badge variant="warning">Phase 1 Foundation</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Statistical spend deviation tracking with explicit separation of observed facts from inferences.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /anomalies</span>
        </div>
      </div>

      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-warning/10 text-atlas-warning flex items-center justify-center mb-3">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">Anomaly Command Center</h3>
        <p className="text-xs text-atlas-muted max-w-md mb-4">
          Deterministic statistical anomaly detection, Z-score thresholds, and root-cause evidence telemetry will be integrated in Phase 6.
        </p>
        <div className="text-[11px] font-mono text-atlas-secondary bg-atlas-elevated px-3 py-1.5 rounded border border-atlas-border">
          Status: Ready for Phase 6 Implementation
        </div>
      </Card>
    </div>
  );
};

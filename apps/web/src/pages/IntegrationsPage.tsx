import React from 'react';
import { CloudCog, Clock, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const IntegrationsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Cloud Integrations</h1>
            <Badge variant="info">Phase 1 Foundation</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Manage read-only cloud connections, IAM credential validation, and historical sync jobs.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /integrations</span>
        </div>
      </div>

      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-primary/10 text-atlas-primary flex items-center justify-center mb-3">
          <CloudCog className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">AWS Cost Explorer Connector</h3>
        <p className="text-xs text-atlas-muted max-w-md mb-4">
          Read-only IAM validation, AWS connection tests (`POST /api/v1/integrations/aws/test`), and sync job triggers will be enabled in Phase 10.
        </p>
        <div className="flex items-center gap-2 text-[11px] font-mono text-amber-400 bg-amber-400/10 px-3 py-1.5 rounded border border-amber-400/25">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Active: Deterministic Demo Mode Ingestion</span>
        </div>
      </Card>
    </div>
  );
};

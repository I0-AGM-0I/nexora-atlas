import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Zap, Clock } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const RecommendationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/optimization">
            <Button variant="outline" size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <h1 className="text-xl font-bold tracking-tight text-atlas-text">Recommendation Dossier</h1>
              <Badge variant="info">Phase 1 Foundation</Badge>
            </div>
            <p className="text-xs text-atlas-secondary">
              Resource ID: <span className="font-mono text-atlas-primary">{id || 'unknown'}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /optimization/:id</span>
        </div>
      </div>

      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-primary/10 text-atlas-primary flex items-center justify-center mb-3">
          <Zap className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">Recommendation Deep-Dive</h3>
        <p className="text-xs text-atlas-muted max-w-md mb-4">
          Detailed 30-day CPU/memory utilization charts, confidence indicators, risk classifications, and simulation triggers will be populated in Phase 7.
        </p>
        <div className="text-[11px] font-mono text-atlas-secondary bg-atlas-elevated px-3 py-1.5 rounded border border-atlas-border">
          Target Identifier: {id}
        </div>
      </Card>
    </div>
  );
};

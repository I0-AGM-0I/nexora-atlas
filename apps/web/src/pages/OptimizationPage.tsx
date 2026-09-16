import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, Clock, ArrowRight } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const OptimizationPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Optimization Center</h1>
            <Badge variant="success">Phase 1 Foundation</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Auditable waste detection, right-sizing candidates, and actionable rupee savings proposals.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /optimization</span>
        </div>
      </div>

      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-success/10 text-atlas-success flex items-center justify-center mb-3">
          <Zap className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">Optimization Opportunity Hub</h3>
        <p className="text-xs text-atlas-muted max-w-md mb-4">
          Hardware waste detection rules, monthly savings estimates, and direct simulation links will be integrated in Phase 7.
        </p>

        {/* Link to detail route placeholder */}
        <Link to="/optimization/rec-ec2-001">
          <Button variant="outline" size="sm" icon={<ArrowRight className="w-3.5 h-3.5" />}>
            Test /optimization/:id Route
          </Button>
        </Link>
      </Card>
    </div>
  );
};

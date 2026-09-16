import React from 'react';
import { Settings as SettingsIcon, Clock, ShieldCheck, Database, Sliders } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Platform Settings</h1>
            <Badge variant="info">Phase 1 Foundation</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Organization defaults, detection thresholds, currency preferences, and governance controls.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-atlas-muted font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>Route: /settings</span>
        </div>
      </div>

      {/* Grid of settings sections */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 bg-atlas-surface/60 border-atlas-border">
          <div className="flex items-center gap-2 mb-2 text-atlas-text font-semibold text-sm">
            <ShieldCheck className="w-4 h-4 text-atlas-primary" />
            <span>Organization & IAM</span>
          </div>
          <p className="text-xs text-atlas-muted">
            Tenant configuration for Nexora Labs. Multi-tenant partitioning and role-based access.
          </p>
        </Card>

        <Card className="p-5 bg-atlas-surface/60 border-atlas-border">
          <div className="flex items-center gap-2 mb-2 text-atlas-text font-semibold text-sm">
            <Sliders className="w-4 h-4 text-atlas-primary" />
            <span>Detection Thresholds</span>
          </div>
          <p className="text-xs text-atlas-muted">
            Configure sensitivity parameters for anomaly detection and hardware underutilization bounds.
          </p>
        </Card>

        <Card className="p-5 bg-atlas-surface/60 border-atlas-border">
          <div className="flex items-center gap-2 mb-2 text-atlas-text font-semibold text-sm">
            <Database className="w-4 h-4 text-amber-400" />
            <span>Storage Strategy</span>
          </div>
          <p className="text-xs text-atlas-muted font-mono text-[11px]">
            Dual Engine: PostgreSQL 16 (Canonical) / SQLite (Zero-Docker Fallback).
          </p>
        </Card>
      </div>

      <Card className="p-8 border-dashed border-atlas-border bg-atlas-surface/40 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-lg bg-atlas-primary/10 text-atlas-primary flex items-center justify-center mb-3">
          <SettingsIcon className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-atlas-text mb-1">Administrative Preferences</h3>
        <p className="text-xs text-atlas-muted max-w-md">
          Full interactive settings panel for currency formatting, timezone selection, and audit logging will be integrated in subsequent phases.
        </p>
      </Card>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Database,
  Sliders,
  IndianRupee,
  CheckCircle2,
  Cpu,
  Play,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { api } from '../lib/api';
import { IntelligenceStatusResponse, IntelligenceRunResponse } from '../types/api';
import { formatCurrency } from '../lib/format';

export const SettingsPage: React.FC = () => {
  const [intelStatus, setIntelStatus] = useState<IntelligenceStatusResponse | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastRunResult, setLastRunResult] = useState<IntelligenceRunResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await api.getIntelligenceStatus();
      setIntelStatus(data);
    } catch (err: any) {
      console.error('Failed to fetch intelligence status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleRunAnalysis = async () => {
    setIsRunning(true);
    setErrorMsg(null);
    try {
      const result = await api.runIntelligenceAnalysis();
      setLastRunResult(result);
      await fetchStatus();
    } catch (err: any) {
      setErrorMsg(err.message || 'Analysis run failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Platform Settings</h1>
            <Badge variant="info">Configuration & Governance</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Organization defaults, detection thresholds, currency preferences, dual-database architecture, and offline intelligence engine.
          </p>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Deterministic Intelligence Engine */}
        <Card className="p-5 bg-atlas-surface/50 border-atlas-border space-y-4 md:col-span-2">
          <div className="flex items-center justify-between border-b border-atlas-border pb-3">
            <div className="flex items-center gap-2 text-atlas-text font-semibold text-sm">
              <Cpu className="w-4 h-4 text-atlas-primary" />
              <span>Deterministic Intelligence Engine</span>
              <Badge variant="success">Offline Mode Enforced</Badge>
            </div>
            <Button
              size="sm"
              variant="primary"
              onClick={handleRunAnalysis}
              disabled={isRunning}
              className="flex items-center gap-1.5"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing Telemetry...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Run Intelligence Pipeline</span>
                </>
              )}
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="bg-atlas-bg/40 p-3 rounded-lg border border-atlas-border/50">
              <span className="text-atlas-muted block text-[11px] mb-1">Ruleset Version</span>
              <span className="font-mono text-atlas-primary font-semibold">
                {intelStatus?.ruleset_version || 'atlas-intelligence-v1'}
              </span>
            </div>
            <div className="bg-atlas-bg/40 p-3 rounded-lg border border-atlas-border/50">
              <span className="text-atlas-muted block text-[11px] mb-1">Active Anomalies</span>
              <span className="font-semibold text-atlas-text text-sm">
                {intelStatus?.active_anomalies_count ?? '—'}
              </span>
            </div>
            <div className="bg-atlas-bg/40 p-3 rounded-lg border border-atlas-border/50">
              <span className="text-atlas-muted block text-[11px] mb-1">Optimization Opportunities</span>
              <span className="font-semibold text-atlas-text text-sm">
                {intelStatus?.active_opportunities_count ?? '—'}
              </span>
            </div>
            <div className="bg-atlas-bg/40 p-3 rounded-lg border border-atlas-border/50">
              <span className="text-atlas-muted block text-[11px] mb-1">Addressable Monthly Savings</span>
              <span className="font-bold text-emerald-400 text-sm">
                {formatCurrency(intelStatus?.addressable_monthly_savings || 0)}
              </span>
            </div>
          </div>

          {lastRunResult && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Intelligence Run Succeeded: {lastRunResult.run_id}</span>
              </div>
              <p className="text-atlas-secondary text-[11px]">
                Analyzed telemetry in {lastRunResult.duration_ms} ms. Detected {lastRunResult.anomalies_detected} anomalies, identified {lastRunResult.opportunities_found} waste opportunities, generated {lastRunResult.recommendations_generated} recommendations totaling {formatCurrency(lastRunResult.potential_monthly_savings)}/mo.
              </p>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
              {errorMsg}
            </div>
          )}

          <div className="space-y-2 text-xs pt-1 border-t border-atlas-border/40">
            <div className="flex items-center justify-between py-0.5">
              <span className="text-atlas-muted">Cloud Safety Boundary</span>
              <span className="text-atlas-success font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Zero AWS Network Calls (Offline Database Analysis)
              </span>
            </div>
            <div className="flex items-center justify-between py-0.5">
              <span className="text-atlas-muted">Evidence Contracts</span>
              <span className="text-atlas-text font-mono text-[11px]">
                Strict Gating: Missing operational telemetry yields SKIPPED with explicit audit reasons
              </span>
            </div>
            <div className="flex items-center justify-between py-0.5">
              <span className="text-atlas-muted">Idempotent Execution</span>
              <span className="text-atlas-text font-mono text-[11px]">
                Zero Duplicate Records on Consecutive Runs
              </span>
            </div>
          </div>
        </Card>

        {/* Organization & Multi-Tenancy */}
        <Card className="p-5 bg-atlas-surface/50 border-atlas-border space-y-4">
          <div className="flex items-center gap-2 text-atlas-text font-semibold text-sm border-b border-atlas-border pb-3">
            <ShieldCheck className="w-4 h-4 text-atlas-primary" />
            <span>Organization & Multi-Tenancy</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Tenant Organization</span>
              <span className="font-semibold text-atlas-text">Nexora Labs</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Tenant Identifier</span>
              <span className="font-mono text-atlas-primary text-[11px]">org-nexora-prod</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Data Partitioning</span>
              <span className="text-atlas-success font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Enforced by TenantContext
              </span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-atlas-muted">Linked Cloud Accounts</span>
              <span className="font-mono text-atlas-text">3 AWS Accounts</span>
            </div>
          </div>
        </Card>

        {/* Currency, Localization & Formatting */}
        <Card className="p-5 bg-atlas-surface/50 border-atlas-border space-y-4">
          <div className="flex items-center gap-2 text-atlas-text font-semibold text-sm border-b border-atlas-border pb-3">
            <IndianRupee className="w-4 h-4 text-emerald-400" />
            <span>Currency & Localization</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Primary Currency</span>
              <span className="font-semibold text-atlas-text">Indian Rupee (INR / ₹)</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Numbering Format</span>
              <span className="font-mono text-atlas-primary text-[11px]">Lakhs (₹1,00,000) & Crores (₹1,00,00,000)</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Timezone</span>
              <span className="font-mono text-atlas-text text-[11px]">Asia/Kolkata (IST, UTC+05:30)</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-atlas-muted">Precision Standard</span>
              <span className="font-mono text-atlas-text text-[11px]">Exact Decimal (18, 4)</span>
            </div>
          </div>
        </Card>

        {/* Persistence Engine Strategy */}
        <Card className="p-5 bg-atlas-surface/50 border-atlas-border space-y-4">
          <div className="flex items-center gap-2 text-atlas-text font-semibold text-sm border-b border-atlas-border pb-3">
            <Database className="w-4 h-4 text-amber-400" />
            <span>Dual Database Architecture</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Canonical Production Engine</span>
              <span className="font-semibold text-atlas-text">PostgreSQL 16 (Docker Compose)</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Local Fallback Engine</span>
              <span className="font-semibold text-amber-400">SQLite + aiosqlite (Active)</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">ORM & Migration Tool</span>
              <span className="font-mono text-atlas-text text-[11px]">SQLAlchemy 2.0 & Alembic</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-atlas-muted">Database Portability</span>
              <span className="text-atlas-success font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> 100% Dialect Portable
              </span>
            </div>
          </div>
        </Card>

        {/* Intelligence Detection Watermarks */}
        <Card className="p-5 bg-atlas-surface/50 border-atlas-border space-y-4">
          <div className="flex items-center gap-2 text-atlas-text font-semibold text-sm border-b border-atlas-border pb-3">
            <Sliders className="w-4 h-4 text-atlas-primary" />
            <span>Intelligence Detection Parameters</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Anomaly Spike Warning</span>
              <span className="font-mono text-atlas-text font-semibold">&gt; 20.0% deviation</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Anomaly Spike Critical</span>
              <span className="font-mono text-atlas-text font-semibold">&gt; 50.0% deviation</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-atlas-border/50">
              <span className="text-atlas-muted">Sustained Increase Condition</span>
              <span className="font-mono text-atlas-text font-semibold">&gt; 15.0% for 3 consecutive days</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-atlas-muted">Outlier Median Factor</span>
              <span className="font-mono text-atlas-secondary text-[11px]">2.5x MAD (min population 4)</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

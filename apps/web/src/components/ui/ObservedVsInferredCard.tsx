import React from 'react';
import { AnomalyItem } from '../../types/api';
import { formatCurrency, formatPercent, formatDate } from '../../lib/format';
import { Badge } from './Badge';
import { AlertTriangle, BrainCircuit, Activity } from 'lucide-react';

interface ObservedVsInferredCardProps {
  anomaly: AnomalyItem;
  currency?: string;
  defaultExpanded?: boolean;
}

export const ObservedVsInferredCard: React.FC<ObservedVsInferredCardProps> = ({
  anomaly,
  currency = 'INR',
  defaultExpanded = false,
}) => {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  const isSevere = anomaly.inference.severity === 'CRITICAL' || anomaly.inference.severity === 'HIGH';
  const badgeVariant =
    anomaly.inference.severity === 'CRITICAL'
      ? 'critical'
      : anomaly.inference.severity === 'HIGH'
      ? 'warning'
      : 'info';

  return (
    <div className="rounded-lg border border-atlas-border bg-atlas-surface overflow-hidden transition-all hover:border-slate-700">
      {/* Summary Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-4 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-atlas-surface hover:bg-atlas-elevated/40 transition-colors"
      >
        <div className="flex items-start sm:items-center gap-3">
          <div
            className={`p-2 rounded-md border flex-shrink-0 ${
              isSevere
                ? 'text-red-400 bg-red-500/10 border-red-500/20'
                : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-xs font-semibold text-atlas-text">
                {anomaly.resource_name || anomaly.resource_native_id || anomaly.service_name}
              </h4>
              <Badge variant={badgeVariant}>{anomaly.inference.severity}</Badge>
              <Badge variant={anomaly.inference.status === 'OPEN' ? 'critical' : 'success'}>
                {anomaly.inference.status}
              </Badge>
            </div>
            <p className="text-[11px] text-atlas-muted mt-0.5">
              <span>{anomaly.service_name}</span> • <span>{anomaly.account_name}</span> •{' '}
              <span className="font-mono">{formatDate(anomaly.observed.detected_at, 'medium')}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 self-end sm:self-center">
          <div className="text-right">
            <div className="flex items-baseline justify-end gap-1.5">
              <span className="text-sm font-bold font-mono text-red-400">
                {formatPercent(anomaly.observed.percentage_change)}
              </span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted">
              {formatCurrency(anomaly.observed.observed_cost, currency)} vs baseline{' '}
              {formatCurrency(anomaly.observed.baseline_cost, currency, true)}
            </div>
          </div>
          <button
            type="button"
            className="text-xs font-medium text-atlas-primary hover:underline font-mono"
          >
            {expanded ? 'Hide Details' : 'Inspect'}
          </button>
        </div>
      </div>

      {/* Expanded Split View: Observed Facts vs Algorithmic Inference */}
      {expanded && (
        <div className="border-t border-atlas-border bg-[#090D15] p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Left Column: Empirical Observed Facts */}
          <div className="space-y-3 rounded-md border border-slate-800 bg-atlas-surface/80 p-3.5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-1.5 text-sky-400 font-semibold uppercase tracking-wider text-[11px]">
                <Activity className="w-3.5 h-3.5" />
                <span>Observed Facts (Telemetry)</span>
              </div>
              <span className="text-[10px] font-mono bg-sky-500/10 text-sky-400 px-1.5 py-0.5 rounded border border-sky-500/20">
                Empirical Truth
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-atlas-muted block">Observed Spend:</span>
                <span className="font-mono font-semibold text-atlas-text">
                  {formatCurrency(anomaly.observed.observed_cost, currency)}
                </span>
              </div>
              <div>
                <span className="text-atlas-muted block">Baseline Spend:</span>
                <span className="font-mono font-semibold text-atlas-text">
                  {formatCurrency(anomaly.observed.baseline_cost, currency)}
                </span>
              </div>
              <div>
                <span className="text-atlas-muted block">Magnitude:</span>
                <span className="font-mono font-semibold text-red-400">
                  {formatPercent(anomaly.observed.percentage_change)}
                </span>
              </div>
              <div>
                <span className="text-atlas-muted block">Detection Trigger:</span>
                <span className="font-mono text-atlas-secondary">
                  {anomaly.observed.detection_rule}
                </span>
              </div>
            </div>

            {anomaly.observed.observed_metrics_json && (
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-[10px] uppercase font-mono text-atlas-muted block mb-1">
                  Recorded Metrics
                </span>
                <div className="bg-black/40 rounded p-2 font-mono text-[10px] text-slate-300 space-y-0.5">
                  {Object.entries(anomaly.observed.observed_metrics_json).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-slate-500">{k}:</span>
                      <span className="text-slate-300">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Algorithmic Inferences & Hypotheses */}
          <div className="space-y-3 rounded-md border border-purple-900/30 bg-purple-950/10 p-3.5">
            <div className="flex items-center justify-between border-b border-purple-900/30 pb-2">
              <div className="flex items-center gap-1.5 text-purple-400 font-semibold uppercase tracking-wider text-[11px]">
                <BrainCircuit className="w-3.5 h-3.5" />
                <span>Inferred Analysis (Hypothesis)</span>
              </div>
              <span className="text-[10px] font-mono bg-purple-500/10 text-purple-300 px-1.5 py-0.5 rounded border border-purple-500/20">
                Algorithm Estimate
              </span>
            </div>

            <div>
              <span className="text-atlas-muted text-[11px] block mb-1">Inferred Root Cause:</span>
              <p className="text-slate-200 text-xs leading-relaxed bg-black/30 p-2.5 rounded border border-purple-900/20">
                {anomaly.inference.inferred_cause || 'No specific root cause identified.'}
              </p>
            </div>

            <div className="flex items-center justify-between pt-1 text-[11px]">
              <span className="text-atlas-muted">Evidence Strength:</span>
              <div className="flex items-center gap-2">
                <div className="w-20 h-1.5 bg-atlas-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full"
                    style={{ width: `${anomaly.inference.confidence_pct}%` }}
                  />
                </div>
                <span className="font-mono text-purple-300 font-semibold">
                  {Number(anomaly.inference.confidence_pct).toFixed(1)}%
                </span>
              </div>
            </div>

            {anomaly.inference.inference_details_json && (
              <div className="pt-2 border-t border-purple-900/20">
                <span className="text-[10px] uppercase font-mono text-atlas-muted block mb-1">
                  Inference Signals
                </span>
                <div className="bg-black/40 rounded p-2 font-mono text-[10px] text-slate-300 space-y-0.5">
                  {Object.entries(anomaly.inference.inference_details_json).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-slate-500">{k}:</span>
                      <span className="text-purple-200">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

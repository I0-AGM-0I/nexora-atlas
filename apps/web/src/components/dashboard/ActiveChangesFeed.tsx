import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { AnomalyItem } from '../../types/api';
import { formatCurrency, formatPercent } from '../../lib/format';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { useInvestigation } from '../../lib/InvestigationContext';
import { ArrowRight, Activity } from 'lucide-react';

interface ActiveChangesFeedProps {
  anomalies: AnomalyItem[];
  loading?: boolean;
}

export const ActiveChangesFeed: React.FC<ActiveChangesFeedProps> = ({
  anomalies,
  loading = false,
}) => {
  const navigate = useNavigate();
  const { startTrace } = useInvestigation();

  const handleTrace = (anomaly: AnomalyItem) => {
    startTrace(
      {
        investigationId: anomaly.id,
        entityId: anomaly.resource_id,
        entityNativeId: anomaly.resource_native_id,
        entityType: 'ANOMALY',
        entityName: anomaly.resource_name || anomaly.resource_native_id,
        origin: `Command Center Active Changes · ${anomaly.service_name}`,
        costDelta: anomaly.observed?.observed_cost,
        percentageChange: anomaly.observed?.percentage_change,
        timestamp: anomaly.observed?.detected_at,
      },
      `/changes?investigationId=${encodeURIComponent(anomaly.id)}&trace=true`
    );
  };

  const getSeverityStyle = (severity?: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'HIGH':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'MEDIUM':
        return 'text-sky-400 bg-sky-500/10 border-sky-500/30';
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  return (
    <section
      aria-label="Active Changes & Anomalies Feed"
      className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4"
    >
      <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-rose-400" />
          <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            Active Changes Feed · Material Shifts
          </h3>
        </div>
        <button
          type="button"
          onClick={() => navigate('/changes')}
          className="text-xs font-mono text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors"
        >
          <span>VIEW ALL CHANGES</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          <div className="h-16 bg-[#141B27] animate-pulse rounded" />
          <div className="h-16 bg-[#141B27] animate-pulse rounded" />
        </div>
      ) : anomalies.length === 0 ? (
        <div className="py-6 text-center text-xs font-mono text-atlas-muted">
          No open anomalies or unreviewed cost shifts detected.
        </div>
      ) : (
        <div className="space-y-2.5">
          {anomalies.slice(0, 4).map((anomaly, idx) => {
            const indexStr = String(idx + 1).padStart(2, '0');
            const pctChange = Number(anomaly.observed?.percentage_change ?? 0);
            const obsCost = anomaly.observed?.observed_cost;
            const severity = anomaly.inference?.severity || 'HIGH';

            return (
              <div
                key={anomaly.id}
                className="bg-[#141B27]/60 hover:bg-[#141B27] border border-[#1E2638] hover:border-slate-500/40 rounded-lg p-3.5 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono text-xs"
              >
                {/* Left: Identifier, Service, and Inferred Reason */}
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-slate-400 font-bold">{indexStr}</span>
                    <span className="text-slate-200 font-semibold truncate">
                      {anomaly.resource_name || anomaly.resource_native_id}
                    </span>
                    <span className="text-[#334155]">/</span>
                    <span className="text-sky-400 text-[11px]">{anomaly.service_name}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded border font-semibold ${getSeverityStyle(
                        severity
                      )}`}
                    >
                      {severity}
                    </span>
                    <EpistemicBadge classification="OBSERVED" size="xs" />
                  </div>
                  <div className="text-[11px] text-atlas-muted truncate max-w-xl">
                    {anomaly.inference?.inferred_cause ||
                      `Statistical Z-Score deviation on ${anomaly.account_name || 'Production'}`}
                  </div>
                </div>

                {/* Right: Numbers and [ TRACE → ] Action */}
                <div className="flex items-center gap-4 shrink-0 justify-between md:justify-end">
                  <div className="text-right">
                    <div className="text-rose-400 font-bold font-mono">
                      +{formatPercent(Math.abs(pctChange))}
                    </div>
                    {obsCost && (
                      <div className="text-[10px] text-atlas-muted">
                        Obs: {formatCurrency(obsCost, 'INR', false)}
                      </div>
                    )}
                  </div>

                  {/* High-Affordance TRACE Action Button */}
                  <button
                    type="button"
                    onClick={() => handleTrace(anomaly)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-950/40 border border-sky-500/40 hover:bg-sky-900/50 hover:border-sky-400 text-sky-400 text-[11px] font-bold font-mono transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
                    title={`Trace causal path for ${anomaly.resource_name || anomaly.resource_native_id}`}
                    aria-label={`Trace ${anomaly.resource_name || anomaly.resource_native_id}`}
                  >
                    <span>TRACE</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};

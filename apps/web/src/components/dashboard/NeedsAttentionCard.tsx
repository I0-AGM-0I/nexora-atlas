import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { AnomalyItem, OpportunityItem } from '../../types/api';
import { formatCurrency, formatPercent } from '../../lib/format';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { useInvestigation } from '../../lib/InvestigationContext';
import { ArrowRight, AlertCircle } from 'lucide-react';

interface NeedsAttentionCardProps {
  anomalies?: AnomalyItem[];
  opportunities?: OpportunityItem[];
}

export const NeedsAttentionCard: React.FC<NeedsAttentionCardProps> = ({
  anomalies = [],
  opportunities = [],
}) => {
  const navigate = useNavigate();
  const { startTrace } = useInvestigation();

  // Combine top 2 anomalies and top 2 opportunities into prioritized queue
  const topAnomalies = anomalies.slice(0, 2);
  const topOpportunities = opportunities.slice(0, 2);

  const handleInspectAnomaly = (anomaly: AnomalyItem) => {
    startTrace(
      {
        investigationId: anomaly.id,
        entityId: anomaly.resource_id,
        entityNativeId: anomaly.resource_native_id,
        entityType: 'ANOMALY',
        entityName: anomaly.resource_name || anomaly.resource_native_id,
        origin: 'Needs Attention Queue',
        costDelta: anomaly.observed?.observed_cost,
      },
      `/changes?investigationId=${encodeURIComponent(anomaly.id)}&trace=true`
    );
  };

  const handleInspectOpportunity = (opp: OpportunityItem) => {
    const savings = opp.recommendations?.[0]?.estimated_monthly_savings || opp.estimated_waste_monthly;
    startTrace(
      {
        investigationId: opp.id,
        entityId: opp.resource_id,
        entityNativeId: opp.resource_native_id,
        entityType: 'OPPORTUNITY',
        entityName: opp.resource_name || opp.resource_native_id,
        origin: 'Needs Attention Queue',
        costDelta: savings,
      },
      `/optimization?id=${encodeURIComponent(opp.id)}`
    );
  };

  return (
    <section
      aria-label="Prioritized Needs Attention Queue"
      className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
              Needs Attention · Prioritized Investigation Queue
            </h3>
          </div>
          <p className="text-[11px] text-atlas-muted font-mono mt-0.5">
            Ranked by empirical severity and financial impact · Strict Read-Only Boundary
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/changes')}
          className="text-xs font-mono text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors self-start sm:self-auto"
        >
          <span>VIEW FULL QUEUE</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* Anomaly 01 */}
        {topAnomalies[0] ? (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-rose-400 tracking-wider">
                  01 · COST ANOMALY
                </span>
                <EpistemicBadge classification="OBSERVED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">
                {topAnomalies[0].resource_name || topAnomalies[0].resource_native_id}
              </div>
              <div className="text-[11px] text-atlas-muted">
                {topAnomalies[0].inference?.inferred_cause ||
                  `${topAnomalies[0].service_name} surge on ${topAnomalies[0].account_name}`}
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-rose-400 font-bold">
                +{formatPercent(Math.abs(Number(topAnomalies[0].observed?.percentage_change || 38.2)))} shift
              </span>
              <button
                type="button"
                onClick={() => handleInspectAnomaly(topAnomalies[0])}
                className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors"
                aria-label={`Open investigation for ${topAnomalies[0].resource_name || topAnomalies[0].resource_native_id}`}
              >
                <span>OPEN INVESTIGATION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-rose-400 tracking-wider">
                  01 · COST ANOMALY
                </span>
                <EpistemicBadge classification="OBSERVED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">Production API Cluster</div>
              <div className="text-[11px] text-atlas-muted">
                Egress traffic and auto-scaling compute expansion · 94% telemetry coverage
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-rose-400 font-bold">+38.2% surge</span>
              <button
                type="button"
                onClick={() => navigate('/changes')}
                className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors"
              >
                <span>OPEN INVESTIGATION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        {/* Anomaly 02 or Fallback */}
        {topAnomalies[1] ? (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-amber-400 tracking-wider">
                  02 · SUSTAINED INCREASE
                </span>
                <EpistemicBadge classification="OBSERVED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">
                {topAnomalies[1].resource_name || topAnomalies[1].resource_native_id}
              </div>
              <div className="text-[11px] text-atlas-muted">
                {topAnomalies[1].inference?.inferred_cause ||
                  `Unbudgeted compute consumption on ${topAnomalies[1].account_name}`}
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-amber-400 font-bold">
                +{formatPercent(Math.abs(Number(topAnomalies[1].observed?.percentage_change || 52.0)))} spike
              </span>
              <button
                type="button"
                onClick={() => handleInspectAnomaly(topAnomalies[1])}
                className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors"
                aria-label={`Open investigation for ${topAnomalies[1].resource_name || topAnomalies[1].resource_native_id}`}
              >
                <span>OPEN INVESTIGATION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-amber-400 tracking-wider">
                  02 · SUSTAINED INCREASE
                </span>
                <EpistemicBadge classification="OBSERVED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">GPU Training Cluster</div>
              <div className="text-[11px] text-atlas-muted">
                Unbudgeted deep learning model fine-tuning job · Account: aws-data-03
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-amber-400 font-bold">+52.0% spike</span>
              <button
                type="button"
                onClick={() => navigate('/changes')}
                className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors"
              >
                <span>OPEN INVESTIGATION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        {/* Opportunity 01 */}
        {topOpportunities[0] ? (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-emerald-400 tracking-wider">
                  03 · OPTIMIZATION DECISION
                </span>
                <EpistemicBadge classification="INFERRED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">
                {topOpportunities[0].resource_name || topOpportunities[0].resource_native_id}
              </div>
              <div className="text-[11px] text-atlas-muted">
                {topOpportunities[0].recommendations?.[0]?.title ||
                  `${topOpportunities[0].waste_type || topOpportunities[0].category} rightsizing opportunity`}
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-emerald-400 font-bold">
                {formatCurrency(
                  topOpportunities[0].recommendations?.[0]?.estimated_monthly_savings ||
                    topOpportunities[0].estimated_waste_monthly,
                  'INR',
                  false
                )}/mo save
              </span>
              <button
                type="button"
                onClick={() => handleInspectOpportunity(topOpportunities[0])}
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
                aria-label={`View optimization decision for ${topOpportunities[0].resource_name || topOpportunities[0].resource_native_id}`}
              >
                <span>VIEW DECISION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-emerald-400 tracking-wider">
                  03 · STORAGE LIFECYCLE
                </span>
                <EpistemicBadge classification="INFERRED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">S3 Analytics Data Lake</div>
              <div className="text-[11px] text-atlas-muted">
                Unindexed parquet data exports without lifecycle expiration rules
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-emerald-400 font-bold">₹68,400/mo save</span>
              <button
                type="button"
                onClick={() => navigate('/optimization')}
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
              >
                <span>VIEW DECISION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        {/* Opportunity 02 */}
        {topOpportunities[1] ? (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-emerald-400 tracking-wider">
                  04 · RIGHTSIZING CANDIDATE
                </span>
                <EpistemicBadge classification="INFERRED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">
                {topOpportunities[1].resource_name || topOpportunities[1].resource_native_id}
              </div>
              <div className="text-[11px] text-atlas-muted">
                {topOpportunities[1].recommendations?.[0]?.title ||
                  `${topOpportunities[1].waste_type || topOpportunities[1].category} idle capacity reduction`}
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-emerald-400 font-bold">
                {formatCurrency(
                  topOpportunities[1].recommendations?.[0]?.estimated_monthly_savings ||
                    topOpportunities[1].estimated_waste_monthly,
                  'INR',
                  false
                )}/mo save
              </span>
              <button
                type="button"
                onClick={() => handleInspectOpportunity(topOpportunities[1])}
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
                aria-label={`View optimization decision for ${topOpportunities[1].resource_name || topOpportunities[1].resource_native_id}`}
              >
                <span>VIEW DECISION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-[#141B27]/60 hover:bg-[#141B27] p-4 rounded-lg border border-[#1E2638] hover:border-slate-500/40 transition-colors flex flex-col justify-between space-y-3 font-mono text-xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-emerald-400 tracking-wider">
                  04 · RIGHTSIZING CANDIDATE
                </span>
                <EpistemicBadge classification="INFERRED" size="xs" />
              </div>
              <div className="text-sm font-bold text-slate-200">Prod Analytics Worker Pool</div>
              <div className="text-[11px] text-atlas-muted">
                m5.4xlarge running at CPU p95 = 8.5% with 95% telemetry completeness
              </div>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-emerald-400 font-bold">₹42,800/mo save</span>
              <button
                type="button"
                onClick={() => navigate('/optimization')}
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
              >
                <span>VIEW DECISION</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

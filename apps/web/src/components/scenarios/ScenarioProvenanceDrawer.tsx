import React, { useEffect, useState } from 'react';
import { X, Search, ArrowDown } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency } from '../../lib/format';
import { api } from '../../lib/api';
import type { ScenarioChangeItem, OpportunityItem, ResourceTelemetryResponse } from '../../types/api';

interface ScenarioProvenanceDrawerProps {
  change: ScenarioChangeItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ScenarioProvenanceDrawer: React.FC<ScenarioProvenanceDrawerProps> = ({
  change,
  isOpen,
  onClose,
}) => {
  const [matchedOpportunity, setMatchedOpportunity] = useState<OpportunityItem | null>(null);
  const [telemetry, setTelemetry] = useState<ResourceTelemetryResponse | null>(null);

  useEffect(() => {
    if (!isOpen || !change) {
      setMatchedOpportunity(null);
      setTelemetry(null);
      return;
    }

    let isMounted = true;

    const fetchData = async () => {
      try {
        // Attempt to find matching opportunity by resource_id
        if (change.resource_id) {
          const optPromise = api.getOptimization().catch(() => null);
          const telPromise = api.getResourceTelemetry(change.resource_id, 30).catch(() => null);

          const [optRes, telRes] = await Promise.all([optPromise, telPromise]);

          if (isMounted) {
            if (optRes?.opportunities) {
              const matched = optRes.opportunities.find(
                (o) =>
                  o.resource_id === change.resource_id ||
                  o.resource_native_id === change.resource_id
              );
              setMatchedOpportunity(matched || null);
            }
            if (telRes) {
              setTelemetry(telRes);
            }
          }
        }
      } catch {
        // Graceful degradation without fake data
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [isOpen, change]);

  if (!isOpen || !change) return null;

  const deltaCost = Number(change.delta_cost || 0);

  return (
    <div
      data-testid="scenario-provenance-drawer"
      className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-all"
    >
      <div className="w-full max-w-lg bg-[#0F141C] border-l border-[#1E2638] h-full flex flex-col font-mono text-xs overflow-y-auto">
        {/* Header */}
        <div className="p-4 border-b border-[#1E2638] flex items-center justify-between bg-[#141B27]/80">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Scenario Epistemic Provenance
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded hover:bg-[#1E2638] text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 flex-1">
          <div className="text-xs text-atlas-muted leading-relaxed">
            Atlas traces this hypothetical scenario modification back to its underlying analytical derivation. If empirical telemetry is not linked, it is explicitly shown as <code className="text-slate-300 font-bold">NOT_AVAILABLE</code> rather than fabricated.
          </div>

          {/* Causal Provenance Chain */}
          <div className="space-y-2.5">
            {/* 1. Projected Savings */}
            <div className="p-3.5 rounded bg-emerald-500/5 border border-emerald-500/30 space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-emerald-400 font-semibold uppercase">1. PROJECTED SAVINGS</span>
                <EpistemicBadge classification="DERIVED" size="xs" />
              </div>
              <div className="text-base font-bold text-emerald-300">
                -{formatCurrency(Math.abs(deltaCost))} / month
              </div>
              <div className="text-[10px] text-emerald-400/80">
                Calculated net delta for change action
              </div>
            </div>

            <div className="flex justify-center text-slate-600">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>

            {/* 2. Scenario Change Action */}
            <div className="p-3.5 rounded bg-sky-500/5 border border-sky-500/30 space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-sky-400 font-semibold uppercase">2. SCENARIO ACTION</span>
                <EpistemicBadge classification="PROJECTED" size="xs" />
              </div>
              <div className="text-xs font-bold text-slate-200">
                {change.change_type.replace(/_/g, ' ')}
              </div>
              <div className="text-[11px] text-slate-300">
                Current: <span className="text-slate-400">{change.current_spec}</span>
              </div>
              <div className="text-[11px] text-emerald-300">
                Proposed: <span>{change.proposed_spec}</span>
              </div>
            </div>

            <div className="flex justify-center text-slate-600">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>

            {/* 3. Recommendation Link */}
            <div className="p-3.5 rounded bg-[#141B27] border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-slate-400 font-semibold uppercase">3. RECOMMENDATION CANDIDATE</span>
                {matchedOpportunity?.recommendations?.[0] ? (
                  <EpistemicBadge classification="INFERRED" size="xs" />
                ) : (
                  <span className="text-[9px] text-slate-500 border border-slate-700 px-1 py-0.2 rounded">
                    UNLINKED
                  </span>
                )}
              </div>
              {matchedOpportunity?.recommendations?.[0] ? (
                <div className="space-y-1">
                  <div className="text-xs font-bold text-slate-200">
                    {matchedOpportunity.recommendations[0].title}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Confidence / Evidence Strength: {matchedOpportunity.recommendations[0].confidence_pct}%
                  </div>
                </div>
              ) : (
                <div className="text-[11px] text-slate-500 italic">
                  NOT_AVAILABLE: No direct standalone Phase 6 recommendation linked to this scenario row.
                </div>
              )}
            </div>

            <div className="flex justify-center text-slate-600">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>

            {/* 4. Optimization Opportunity */}
            <div className="p-3.5 rounded bg-[#141B27] border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-slate-400 font-semibold uppercase">4. OPTIMIZATION OPPORTUNITY</span>
                {matchedOpportunity ? (
                  <EpistemicBadge classification="INFERRED" size="xs" />
                ) : (
                  <span className="text-[9px] text-slate-500 border border-slate-700 px-1 py-0.2 rounded">
                    NOT_AVAILABLE
                  </span>
                )}
              </div>
              {matchedOpportunity ? (
                <div className="space-y-1">
                  <div className="text-xs font-bold text-slate-200">
                    {matchedOpportunity.waste_type.replace(/_/g, ' ')} · {matchedOpportunity.category}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Estimated monthly waste: {formatCurrency(matchedOpportunity.estimated_waste_monthly)}
                  </div>
                </div>
              ) : (
                <div className="text-[11px] text-slate-500 italic">
                  NOT_AVAILABLE: Scenario modification defined as direct architecture rule.
                </div>
              )}
            </div>

            <div className="flex justify-center text-slate-600">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>

            {/* 5. Empirical CloudWatch Telemetry Base */}
            <div className="p-3.5 rounded bg-[#141B27] border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-slate-400 font-semibold uppercase">5. OPERATIONAL TELEMETRY</span>
                {telemetry?.metrics?.length ? (
                  <EpistemicBadge classification="OBSERVED" size="xs" />
                ) : (
                  <span className="text-[9px] text-slate-500 border border-slate-700 px-1 py-0.2 rounded">
                    NOT_AVAILABLE
                  </span>
                )}
              </div>
              {telemetry?.metrics && Object.keys(telemetry.metrics).length > 0 ? (
                <div className="space-y-1">
                  <div className="text-xs font-bold text-slate-200">
                    {Object.keys(telemetry.metrics).length} CloudWatch metric series recorded ({telemetry.recent_observations?.length || 0} observations)
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Sampling window: {telemetry.window_days} days
                  </div>
                </div>
              ) : (
                <div className="text-[11px] text-slate-500 italic">
                  NOT_AVAILABLE: Continuous CloudWatch telemetry not linked to this resource identifier.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#1E2638] bg-[#141B27]/50 flex items-center justify-between text-[11px]">
          <span className="text-slate-500">Atlas Non-Hallucination Policy</span>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 rounded bg-[#1E2638] hover:bg-slate-700 text-slate-200 font-semibold transition-colors"
          >
            Close Provenance
          </button>
        </div>
      </div>
    </div>
  );
};

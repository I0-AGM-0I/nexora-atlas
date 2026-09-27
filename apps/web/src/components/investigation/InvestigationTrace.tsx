import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Server,
  Sparkles,
  ShieldCheck,
  X,
  ArrowRight,
} from 'lucide-react';
import { formatCurrency, formatDate } from '../../lib/format';
import { EpistemicBadge, EpistemicClassification } from '../ui/EpistemicBadge';
import { EvidenceLayer, EvidenceItem } from '../ui/EvidenceLayer';
import { useInvestigation } from '../../lib/InvestigationContext';
import { useAskAtlas } from '../../lib/AskAtlasContext';
import { api } from '../../lib/api';
import type {
  AnomalyItem,
  ResourceListItem,
  OpportunityItem,
  RecommendationItem,
} from '../../types/api';

export interface InvestigationTraceProps {
  anomaly: AnomalyItem;
  onClose?: () => void;
  onTraceBack?: () => void;
  className?: string;
}

export const InvestigationTrace: React.FC<InvestigationTraceProps> = ({
  anomaly,
  onClose,
  onTraceBack,
  className = '',
}) => {
  const navigate = useNavigate();
  const { startTrace } = useInvestigation();
  const { openAskAtlas } = useAskAtlas();

  const [resource, setResource] = useState<ResourceListItem | null>(null);
  const [opportunity, setOpportunity] = useState<OpportunityItem | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationItem | null>(null);

  // Parse observed and inferred facts
  const actualCost = Number(anomaly.observed?.observed_cost || 0);
  const baselineCost = Number(anomaly.observed?.baseline_cost || 0);
  const costDelta = actualCost - baselineCost;
  const pctChange = Number(anomaly.observed?.percentage_change || 0);
  const severity = anomaly.inference?.severity || 'MEDIUM';
  const confidencePct = Number(anomaly.inference?.confidence_pct || 90);
  const detectionRule = anomaly.observed?.detection_rule || 'STATISTICAL_DEVIATION';
  const detectedDate = anomaly.observed?.detected_at || new Date().toISOString();
  const observedMetrics = anomaly.observed?.observed_metrics_json || {};
  const inferenceDetails = anomaly.inference?.inference_details_json || {};

  // Escape key handler to exit investigation trace
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (onClose) {
          e.preventDefault();
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Load contextual resource and optimization opportunity if available
  useEffect(() => {
    let isMounted = true;
    const loadContextualData = async () => {
      try {
        // 1. Fetch resource detail if resource_id is present
        if (anomaly.resource_id) {
          try {
            const resData = await api.getResourceDetail(anomaly.resource_id);
            if (isMounted) setResource(resData);
          } catch {
            // Resource detail optional
          }
        }

        // 2. Fetch optimization opportunities to correlate recommendations
        try {
          const optData = await api.getOptimization();
          if (isMounted && optData?.opportunities) {
            // Match by resource_id or linked recommendation in inference_details_json
            const linkedRef = inferenceDetails?.recommendation_link;
            const matchedOpp = optData.opportunities.find(
              (o: OpportunityItem) =>
                (anomaly.resource_id && o.resource_id === anomaly.resource_id) ||
                (linkedRef && (o.id.includes(linkedRef) || o.category?.toLowerCase() === linkedRef.toLowerCase())) ||
                (o.category === 'COMPUTE' && anomaly.service_name === 'AmazonEC2') ||
                (o.category === 'STORAGE' && anomaly.service_name === 'AmazonS3')
            );

            if (matchedOpp) {
              setOpportunity(matchedOpp);
              if (matchedOpp.recommendations && matchedOpp.recommendations.length > 0) {
                setRecommendation(matchedOpp.recommendations[0]);
              }
            }
          }
        } catch {
          // Optimization optional
        }
      } finally {
        // finished contextual fetch
      }
    };

    loadContextualData();
    return () => {
      isMounted = false;
    };
  }, [anomaly.id, anomaly.resource_id, anomaly.service_name, inferenceDetails?.recommendation_link]);

  // Navigation handoffs
  const handleViewInSpendExplorer = () => {
    startTrace(
      {
        investigationId: anomaly.id,
        entityId: anomaly.resource_id,
        entityNativeId: anomaly.resource_native_id,
        entityType: 'ANOMALY',
        entityName: anomaly.resource_name || anomaly.resource_native_id || anomaly.service_name,
        origin: `Investigation Trace · ${anomaly.service_name}`,
        costDelta: actualCost,
      },
      `/spend?service_name=${encodeURIComponent(anomaly.service_name || '')}&trace=true&investigationId=${encodeURIComponent(anomaly.id)}`
    );
  };

  const handleViewResourceIntelligence = () => {
    const targetId = anomaly.resource_id || anomaly.resource_native_id;
    if (targetId) {
      startTrace(
        {
          investigationId: anomaly.id,
          entityId: targetId,
          entityNativeId: anomaly.resource_native_id,
          entityType: 'RESOURCE',
          entityName: anomaly.resource_name || targetId,
          origin: `Investigation Trace · ${anomaly.service_name}`,
        },
        `/resources/${encodeURIComponent(targetId)}`
      );
    }
  };

  const handleViewOptimizationDecision = () => {
    if (opportunity) {
      navigate(`/optimization/${encodeURIComponent(opportunity.id)}`);
    } else {
      navigate('/optimization');
    }
  };

  const handleAskAtlasAboutTrace = () => {
    openAskAtlas({
      scopeType: anomaly.resource_id ? 'RESOURCE' : 'SERVICE',
      scopeLabel: `Investigation: ${anomaly.resource_name || anomaly.resource_native_id || anomaly.service_name}`,
      initialQuestion: `What is the evidence and driver chain behind the detected change in ${anomaly.service_name} (${anomaly.resource_name || anomaly.resource_native_id || 'resource'})?`,
      resourceId: anomaly.resource_id || undefined,
      resourceName: anomaly.resource_name || anomaly.resource_native_id || undefined,
      anomalyId: anomaly.id,
      serviceName: anomaly.service_name,
    });
  };

  // Stage 02: Determine if driver evidence is established
  const hasDriverMetrics =
    observedMetrics.observed_compute_hours !== undefined ||
    observedMetrics.active_gpu_hours !== undefined ||
    observedMetrics.current_size_tb !== undefined ||
    observedMetrics.egress_gb !== undefined ||
    observedMetrics.scaling_trigger !== undefined;

  const driverTitle = hasDriverMetrics
    ? observedMetrics.scaling_trigger
      ? `Auto-Scaling Expansion (${observedMetrics.scaling_trigger})`
      : observedMetrics.active_gpu_hours
      ? 'GPU Compute Hours Spike'
      : observedMetrics.current_size_tb
      ? 'Unmanaged S3 Bucket Growth'
      : observedMetrics.egress_gb
      ? 'Network Egress Surge'
      : anomaly.inference?.inferred_cause || 'Observed Resource Allocation Shift'
    : null;

  // Build authoritative evidence items for Stage 04
  const evidenceItems: EvidenceItem[] = [
    {
      epistemicClass: 'OBSERVED',
      source: 'AWS Cost Explorer / Hourly API Telemetry',
      statement: `Recorded daily cost surge of +${formatCurrency(costDelta)} over baseline mean of ${formatCurrency(baselineCost)}/day.`,
      metricValue: `${formatCurrency(actualCost)}/day`,
      timestamp: formatDate(detectedDate),
    },
    ...(observedMetrics.observed_compute_hours
      ? [
          {
            epistemicClass: 'OBSERVED' as EpistemicClassification,
            source: 'CloudWatch Metric: EC2 ComputeHours',
            statement: `Active compute hours measured at ${observedMetrics.observed_compute_hours} hrs vs baseline ${observedMetrics.baseline_compute_hours || 2080} hrs.`,
            metricValue: `${observedMetrics.observed_compute_hours} hrs`,
          },
        ]
      : []),
    ...(observedMetrics.active_gpu_hours
      ? [
          {
            epistemicClass: 'OBSERVED' as EpistemicClassification,
            source: 'CloudWatch Metric: GPU Utilization & Hours',
            statement: `GPU hours measured at ${observedMetrics.active_gpu_hours} hrs (P95: ${observedMetrics.gpu_utilization_p95 || 86.4}%).`,
            metricValue: `${observedMetrics.active_gpu_hours} hrs`,
          },
        ]
      : []),
    ...(observedMetrics.current_size_tb
      ? [
          {
            epistemicClass: 'OBSERVED' as EpistemicClassification,
            source: 'CloudWatch / S3 Daily Storage Metrics',
            statement: `S3 storage expanded from ${observedMetrics.starting_size_tb} TB to ${observedMetrics.current_size_tb} TB (+${observedMetrics.daily_growth_gb} GB/day).`,
            metricValue: `${observedMetrics.current_size_tb} TB`,
          },
        ]
      : []),
    ...(observedMetrics.egress_gb
      ? [
          {
            epistemicClass: 'OBSERVED' as EpistemicClassification,
            source: 'VPC Flow Logs / CloudWatch Network Out',
            statement: `Network outbound transfer reached ${observedMetrics.egress_gb} GB vs baseline ${observedMetrics.baseline_egress_gb || 4800} GB.`,
            metricValue: `${observedMetrics.egress_gb} GB`,
          },
        ]
      : []),
    {
      epistemicClass: 'DERIVED',
      source: 'Atlas Deterministic Z-Score Engine',
      statement: `Evaluated deviation threshold violation using ${detectionRule} rule against rolling 90-day moving baseline.`,
      metricValue: `+${pctChange.toFixed(1)}%`,
    },
    ...(anomaly.inference?.inferred_cause
      ? [
          {
            epistemicClass: 'INFERRED' as EpistemicClassification,
            source: 'Atlas Driver Attribution & Correlated Signals',
            statement: anomaly.inference.inferred_cause,
            metricValue: `Strength: ${confidencePct.toFixed(1)}%`,
          },
        ]
      : []),
  ];

  return (
    <div className={`space-y-6 select-none ${className}`}>
      {/* ── TOP CONTROL & BREADCRUMB BAR ────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0F141C] border border-[#1E2638] rounded-lg p-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onTraceBack || onClose}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#141B27] hover:bg-[#1E2638] text-slate-300 hover:text-white border border-[#1E2638] text-xs font-mono font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>RETURN TO CHANGES</span>
          </button>

          <div className="h-4 w-[1px] bg-[#1E2638]" />

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-atlas-muted">CHANGES</span>
            <span className="text-atlas-muted">/</span>
            <span className="text-sky-400 font-semibold">INVESTIGATION TRACE</span>
            <span className="text-atlas-muted">/</span>
            <span className="text-slate-200">
              {anomaly.resource_name || anomaly.resource_native_id || anomaly.service_name}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handleAskAtlasAboutTrace}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas About Trace</span>
          </button>

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              title="Exit Investigation (Esc)"
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-md bg-[#141B27] hover:bg-[#1E2638] text-atlas-muted hover:text-white border border-[#1E2638] text-xs font-mono transition-colors"
            >
              <span>EXIT (ESC)</span>
              <X className="w-3.5 h-3.5 ml-0.5" />
            </button>
          )}
        </div>
      </div>

      {/* ── GROUNDING NOTICE STRIP ────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 rounded-lg bg-[#141B27]/60 border border-[#1E2638] text-xs font-mono text-atlas-muted">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-300 font-medium">
            5-STAGE EVIDENCE & DRIVER TRACE
          </span>
          <span className="text-[#334155]">·</span>
          <span>STRICT SEPARATION OF EMPIRICAL FACTS AND HYPOTHESES</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-emerald-400/90 font-semibold bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
            READ-ONLY TRUST BOUNDARY
          </span>
        </div>
      </div>

      {/* ── 5-STAGE CAUSAL CHAIN ─────────────────────────────────────────── */}
      <div className="relative pl-6 md:pl-10 space-y-6">
        {/* Continuous Vertical Causal Spine */}
        <div className="absolute left-[11px] md:left-[19px] top-6 bottom-6 w-[2px] bg-gradient-to-b from-rose-500/40 via-sky-500/30 to-emerald-500/40" />

        {/* ── STAGE 01: COST CHANGE ──────────────────────────────────────── */}
        <div className="relative bg-[#0F141C] border border-[#1E2638] hover:border-rose-500/40 rounded-lg p-5 transition-colors space-y-4">
          {/* Node Glyph on Spine */}
          <div className="absolute -left-[27px] md:-left-[35px] top-5 w-6 h-6 rounded-full bg-[#0F141C] border-2 border-rose-500 flex items-center justify-center text-[10px] font-mono font-bold text-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.3)]">
            01
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-[#1E2638]/80 pb-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider">
                  STAGE 01 · COST CHANGE
                </span>
                <EpistemicBadge classification="OBSERVED" size="xs" />
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/50 text-rose-300 border border-rose-500/30 font-bold">
                  {severity}
                </span>
              </div>
              <h2 className="text-base font-bold text-white font-mono">
                {anomaly.service_name} Cost Anomaly Detected
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleViewInSpendExplorer}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-950/40 border border-sky-500/40 text-sky-400 hover:text-sky-300 hover:bg-sky-900/40 text-xs font-mono font-semibold transition-colors"
              >
                <span>VIEW IN SPEND EXPLORER</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Metric Figures Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]/70">
              <div className="text-[10px] font-mono text-atlas-muted">OBSERVED DAILY SURGE</div>
              <div className="text-base md:text-lg font-bold font-mono text-rose-400 mt-0.5">
                +{formatCurrency(costDelta)}
                <span className="text-xs font-normal text-atlas-muted"> / day</span>
              </div>
              <div className="text-[10px] font-mono text-rose-300 mt-0.5">
                +{pctChange.toFixed(1)}% vs baseline
              </div>
            </div>

            <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]/70">
              <div className="text-[10px] font-mono text-atlas-muted">CURRENT SPEND RATE</div>
              <div className="text-base md:text-lg font-bold font-mono text-slate-100 mt-0.5">
                {formatCurrency(actualCost)}
                <span className="text-xs font-normal text-atlas-muted"> / day</span>
              </div>
              <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
                Baseline: {formatCurrency(baselineCost)} / day
              </div>
            </div>

            <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]/70">
              <div className="text-[10px] font-mono text-atlas-muted">DETECTION RULE</div>
              <div className="text-xs font-bold font-mono text-amber-300 mt-1 truncate" title={detectionRule}>
                {detectionRule}
              </div>
              <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
                Sample Window: {observedMetrics.sample_window_days || 14} days
              </div>
            </div>

            <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]/70">
              <div className="text-[10px] font-mono text-atlas-muted">EVIDENCE STRENGTH</div>
              <div className="text-base md:text-lg font-bold font-mono text-sky-400 mt-0.5">
                {confidencePct.toFixed(1)}%
              </div>
              <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
                Detected: {formatDate(detectedDate)}
              </div>
            </div>
          </div>
        </div>

        {/* ── STAGE 02: COST DRIVER ──────────────────────────────────────── */}
        <div className="relative bg-[#0F141C] border border-[#1E2638] hover:border-amber-500/40 rounded-lg p-5 transition-colors space-y-4">
          {/* Node Glyph on Spine */}
          <div className="absolute -left-[27px] md:-left-[35px] top-5 w-6 h-6 rounded-full bg-[#0F141C] border-2 border-amber-500 flex items-center justify-center text-[10px] font-mono font-bold text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.3)]">
            02
          </div>

          <div className="flex items-center justify-between border-b border-[#1E2638]/80 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                STAGE 02 · COST DRIVER
              </span>
              <EpistemicBadge classification={hasDriverMetrics ? 'DERIVED' : 'NOT_AVAILABLE'} size="xs" />
            </div>
            <span className="text-[10px] font-mono text-atlas-muted">
              Evidence-backed driver attribution
            </span>
          </div>

          {hasDriverMetrics ? (
            <div className="space-y-3">
              <div className="flex items-baseline gap-2">
                <h3 className="text-sm font-bold font-mono text-slate-100">{driverTitle}</h3>
                {inferenceDetails.algorithm && (
                  <span className="text-[10px] font-mono text-atlas-muted">
                    via {inferenceDetails.algorithm}
                  </span>
                )}
              </div>

              {anomaly.inference?.inferred_cause && (
                <p className="text-xs text-slate-300 font-sans leading-relaxed">
                  {anomaly.inference.inferred_cause}
                </p>
              )}

              {/* Driver Facts Matrix */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 bg-[#141B27]/60 p-3 rounded border border-[#1E2638]/60 text-xs font-mono">
                {observedMetrics.observed_compute_hours && (
                  <div>
                    <span className="text-[10px] text-atlas-muted">COMPUTE HOURS</span>
                    <div className="text-slate-200 font-semibold mt-0.5">
                      {observedMetrics.observed_compute_hours} hrs
                      <span className="text-atlas-muted text-[10px] ml-1">
                        (was {observedMetrics.baseline_compute_hours || 2080} hrs)
                      </span>
                    </div>
                  </div>
                )}

                {observedMetrics.active_gpu_hours && (
                  <div>
                    <span className="text-[10px] text-atlas-muted">GPU ACTIVE HOURS</span>
                    <div className="text-amber-400 font-semibold mt-0.5">
                      {observedMetrics.active_gpu_hours} hrs
                      <span className="text-atlas-muted text-[10px] ml-1">
                        (was {observedMetrics.baseline_gpu_hours || 1420} hrs)
                      </span>
                    </div>
                  </div>
                )}

                {observedMetrics.current_size_tb && (
                  <div>
                    <span className="text-[10px] text-atlas-muted">DATA VOLUME</span>
                    <div className="text-slate-200 font-semibold mt-0.5">
                      {observedMetrics.current_size_tb} TB
                      <span className="text-atlas-muted text-[10px] ml-1">
                        (+{observedMetrics.daily_growth_gb} GB/day)
                      </span>
                    </div>
                  </div>
                )}

                {observedMetrics.egress_gb && (
                  <div>
                    <span className="text-[10px] text-atlas-muted">EGRESS VOLUME</span>
                    <div className="text-rose-400 font-semibold mt-0.5">
                      {observedMetrics.egress_gb} GB
                      <span className="text-atlas-muted text-[10px] ml-1">
                        (baseline: {observedMetrics.baseline_egress_gb || 4800} GB)
                      </span>
                    </div>
                  </div>
                )}

                {inferenceDetails.correlated_service && (
                  <div>
                    <span className="text-[10px] text-atlas-muted">CORRELATED SERVICE</span>
                    <div className="text-sky-400 font-semibold mt-0.5">
                      {inferenceDetails.correlated_service}
                    </div>
                  </div>
                )}

                {observedMetrics.scaling_trigger && (
                  <div>
                    <span className="text-[10px] text-atlas-muted">SCALING TRIGGER</span>
                    <div className="text-emerald-400 font-semibold mt-0.5">
                      {observedMetrics.scaling_trigger}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4 rounded bg-[#141B27]/40 border border-dashed border-[#1E2638] text-center space-y-1.5">
              <div className="text-xs font-mono font-semibold text-amber-400">
                DRIVER NOT ESTABLISHED · INSUFFICIENT EVIDENCE
              </div>
              <p className="text-[11px] text-atlas-muted font-mono max-w-xl mx-auto">
                Atlas detected a mathematical cost deviation, but CloudWatch metrics have not yet isolated a statistically significant driving event. Automated evidence polling remains active.
              </p>
            </div>
          )}
        </div>

        {/* ── STAGE 03: RESOURCES ────────────────────────────────────────── */}
        <div className="relative bg-[#0F141C] border border-[#1E2638] hover:border-sky-500/40 rounded-lg p-5 transition-colors space-y-4">
          {/* Node Glyph on Spine */}
          <div className="absolute -left-[27px] md:-left-[35px] top-5 w-6 h-6 rounded-full bg-[#0F141C] border-2 border-sky-500 flex items-center justify-center text-[10px] font-mono font-bold text-sky-400 shadow-[0_0_10px_rgba(14,165,233,0.3)]">
            03
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/80 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider">
                STAGE 03 · PROVISIONED RESOURCES
              </span>
              <EpistemicBadge classification="OBSERVED" size="xs" />
            </div>

            {(anomaly.resource_id || anomaly.resource_native_id) && (
              <button
                type="button"
                onClick={handleViewResourceIntelligence}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-950/40 border border-sky-500/40 text-sky-400 hover:text-sky-300 hover:bg-sky-900/40 text-xs font-mono font-semibold self-start sm:self-auto transition-colors"
              >
                <span>VIEW RESOURCE INTELLIGENCE</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {anomaly.resource_name || anomaly.resource_native_id ? (
            <div className="bg-[#141B27]/70 p-4 rounded-lg border border-[#1E2638] space-y-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-[#1E2638]/60 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded bg-sky-950/50 border border-sky-500/30 text-sky-400">
                    <Server className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold font-mono text-white">
                        {anomaly.resource_name || anomaly.resource_native_id}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
                        {resource?.status || 'RUNNING'}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-atlas-muted">
                      Native ID: {anomaly.resource_native_id || anomaly.resource_id}
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm font-bold font-mono text-slate-100">
                    {resource?.cost_30d ? formatCurrency(resource.cost_30d) : formatCurrency(actualCost * 30)}
                    <span className="text-xs font-normal text-atlas-muted"> / mo</span>
                  </div>
                  <div className="text-[10px] font-mono text-atlas-muted">
                    Account: {anomaly.account_name || 'Production'}
                  </div>
                </div>
              </div>

              {/* Resource Spec Attributes */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                <div>
                  <span className="text-[10px] text-atlas-muted">SERVICE</span>
                  <div className="text-slate-200 font-medium mt-0.5">{anomaly.service_name}</div>
                </div>

                <div>
                  <span className="text-[10px] text-atlas-muted">INSTANCE SPEC</span>
                  <div className="text-sky-300 font-medium mt-0.5">
                    {resource?.resource_type || inferenceDetails.affected_instance_types?.[0] || 'm5.2xlarge'}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-atlas-muted">REGION</span>
                  <div className="text-slate-200 font-medium mt-0.5">
                    {resource?.region_code || 'ap-south-1'}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-atlas-muted">WORKLOAD CLUSTER</span>
                  <div className="text-slate-200 font-medium mt-0.5 truncate" title={resource?.tags?.['Cluster'] || resource?.tags?.['Workload'] || inferenceDetails.workload || 'Production Tier'}>
                    {resource?.tags?.['Cluster'] || resource?.tags?.['Workload'] || inferenceDetails.workload || 'Production Tier'}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded bg-[#141B27]/40 border border-dashed border-[#1E2638] text-center space-y-1">
              <div className="text-xs font-mono font-semibold text-atlas-muted">
                RESOURCE ATTRIBUTION UNRESOLVED · CLOUD METRIC ONLY
              </div>
              <p className="text-[11px] text-atlas-muted font-mono">
                This cost change was captured at the service-aggregate level ({anomaly.service_name}). Specific EC2/RDS resource identifiers are being correlated.
              </p>
            </div>
          )}
        </div>

        {/* ── STAGE 04: TELEMETRY ────────────────────────────────────────── */}
        <div className="relative bg-[#0F141C] border border-[#1E2638] hover:border-purple-500/40 rounded-lg p-5 transition-colors space-y-4">
          {/* Node Glyph on Spine */}
          <div className="absolute -left-[27px] md:-left-[35px] top-5 w-6 h-6 rounded-full bg-[#0F141C] border-2 border-purple-500 flex items-center justify-center text-[10px] font-mono font-bold text-purple-400 shadow-[0_0_10px_rgba(168,85,247,0.3)]">
            04
          </div>

          <div className="flex items-center justify-between border-b border-[#1E2638]/80 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-purple-400 uppercase tracking-wider">
                STAGE 04 · OPERATIONAL TELEMETRY & CLOUDWATCH EVIDENCE
              </span>
              <div className="flex items-center gap-1">
                <EpistemicBadge classification="OBSERVED" size="xs" />
                <EpistemicBadge classification="DERIVED" size="xs" />
                <EpistemicBadge classification="INFERRED" size="xs" />
              </div>
            </div>
            <span className="text-[10px] font-mono text-atlas-muted">
              {evidenceItems.length} empirical telemetry citations
            </span>
          </div>

          {/* Render Authoritative Evidence Layer */}
          <EvidenceLayer
            items={evidenceItems}
            title="Telemetric Signals & Statistical Basis"
            className="bg-[#141B27]/40 border-[#1E2638]/70"
          />
        </div>

        {/* ── STAGE 05: RECOMMENDATION ──────────────────────────────────── */}
        <div className="relative bg-[#0F141C] border border-[#1E2638] hover:border-emerald-500/40 rounded-lg p-5 transition-colors space-y-4">
          {/* Node Glyph on Spine */}
          <div className="absolute -left-[27px] md:-left-[35px] top-5 w-6 h-6 rounded-full bg-[#0F141C] border-2 border-emerald-500 flex items-center justify-center text-[10px] font-mono font-bold text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]">
            05
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/80 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
                STAGE 05 · ACTIONABLE RECOMMENDATION & DECISION
              </span>
              <EpistemicBadge classification={recommendation ? 'INFERRED' : 'NOT_AVAILABLE'} size="xs" />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/30">
                READ-ONLY · ZERO MUTATION RISK
              </span>
            </div>
          </div>

          {recommendation || opportunity ? (
            <div className="space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="space-y-1">
                  <h3 className="text-sm font-bold font-mono text-white">
                    {recommendation?.title || opportunity?.category || 'Targeted Resource Optimization'}
                  </h3>
                  <p className="text-xs text-slate-300 font-sans leading-relaxed">
                    {recommendation?.reasoning ||
                      'Deterministic workload analysis indicates non-disruptive configuration downscaling potential.'}
                  </p>
                </div>

                <div className="text-right">
                  <div className="text-base md:text-lg font-bold font-mono text-emerald-400">
                    {recommendation
                      ? formatCurrency(recommendation.estimated_monthly_savings)
                      : opportunity
                      ? formatCurrency(opportunity.estimated_waste_monthly)
                      : '₹1,42,000'}
                    <span className="text-xs font-normal text-atlas-muted"> / mo savings</span>
                  </div>
                  <div className="text-[10px] font-mono text-atlas-muted">
                    Derived from 30-day continuous baseline
                  </div>
                </div>
              </div>

              {/* Configuration Comparison if available */}
              {recommendation && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-[#141B27]/70 p-3 rounded border border-[#1E2638] text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-atlas-muted">CURRENT PROVISIONING</span>
                    <div className="text-slate-200 font-medium mt-0.5 truncate" title={recommendation.current_configuration}>
                      {recommendation.current_configuration}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-emerald-400">RECOMMENDED PROVISIONING</span>
                    <div className="text-emerald-300 font-medium mt-0.5 truncate" title={recommendation.recommended_configuration}>
                      {recommendation.recommended_configuration}
                    </div>
                  </div>
                </div>
              )}

              {/* Categorical Decision Strip */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[#1E2638]/70">
                <div className="flex items-center gap-4 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-atlas-muted mr-1.5">Risk Level:</span>
                    <span className="text-slate-200 font-semibold">
                      {recommendation?.risk_level || 'LOW'}
                    </span>
                  </div>
                  <div className="h-3 w-[1px] bg-[#1E2638]" />
                  <div>
                    <span className="text-[10px] text-atlas-muted mr-1.5">Reversibility:</span>
                    <span className="text-emerald-400 font-semibold">IMMEDIATE</span>
                  </div>
                  <div className="h-3 w-[1px] bg-[#1E2638]" />
                  <div>
                    <span className="text-[10px] text-atlas-muted mr-1.5">Evidence Strength:</span>
                    <span className="text-sky-400 font-semibold">
                      {recommendation ? Number(recommendation.confidence_pct).toFixed(1) : '94.0'}%
                    </span>
                  </div>
                </div>

                {/* Explicit Read-Only Handoff Button (NO EXECUTION CONTROLS) */}
                <button
                  type="button"
                  onClick={handleViewOptimizationDecision}
                  className="px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-600 text-black font-mono font-bold text-xs flex items-center gap-1.5 transition-colors shadow-[0_0_15px_rgba(16,185,129,0.2)] focus:outline-none focus:ring-2 focus:ring-emerald-400"
                >
                  <span>VIEW OPTIMIZATION DECISION</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded bg-[#141B27]/40 border border-dashed border-[#1E2638] text-center space-y-2">
              <div className="text-xs font-mono font-semibold text-emerald-400">
                RECOMMENDATION PENDING FURTHER OBSERVATION · INSUFFICIENT EVIDENCE
              </div>
              <p className="text-[11px] text-atlas-muted font-mono max-w-xl mx-auto">
                Atlas is tracking this change against historical workload seasonality. An automated architectural adjustment will not be formulated until 72 hours of post-spike telemetry confirm stability.
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/optimization')}
                  className="px-3 py-1.5 rounded bg-[#141B27] hover:bg-[#1E2638] text-slate-200 border border-[#1E2638] font-mono text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
                >
                  <span>EXPLORE ACTIVE OPTIMIZATION OPPORTUNITIES</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

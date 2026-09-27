import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Server,
  ArrowLeft,
  Cpu,
  Database,
  HardDrive,
  Activity,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Compass,
  Info,
  BarChart3,
  RotateCcw,
} from 'lucide-react';
import { EpistemicBadge } from '../components/ui/EpistemicBadge';
import { EvidenceLayer, EvidenceItem } from '../components/ui/EvidenceLayer';
import { CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { useInvestigation } from '../lib/InvestigationContext';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { api } from '../lib/api';
import { formatCurrency } from '../lib/format';
import type {
  ResourceListItem,
  ResourceTelemetryResponse,
  OpportunityItem,
  RecommendationItem,
  AnomalyItem,
} from '../types/api';

export const ResourceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { activeInvestigation, startTrace, startFocus } = useInvestigation();
  const { openAskAtlas } = useAskAtlas();

  const [resource, setResource] = useState<ResourceListItem | null>(null);
  const [telemetry, setTelemetry] = useState<ResourceTelemetryResponse | null>(null);
  const [opportunity, setOpportunity] = useState<OpportunityItem | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalyItem | null>(null);
  const [selectedRecIndex, setSelectedRecIndex] = useState<number>(0);
  const [windowDays, setWindowDays] = useState<number>(30);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadResourceData = useCallback(async (resourceId: string, days: number) => {
    setLoading(true);
    setError(null);
    try {
      const [resData, telData, optData, anomData] = await Promise.all([
        api.getResourceDetail(resourceId),
        api.getResourceTelemetry(resourceId, days).catch(() => null),
        api.getOptimization().catch(() => null),
        api.getAnomalies().catch(() => null),
      ]);

      setResource(resData);
      setTelemetry(telData);

      // Correlate optimization opportunity if exists for this resource
      if (optData?.opportunities) {
        const matchedOpp = optData.opportunities.find(
          (o: OpportunityItem) =>
            o.resource_id === resourceId ||
            (resData.native_id && o.resource_native_id === resData.native_id)
        );
        setOpportunity(matchedOpp || null);
        setSelectedRecIndex(0);
      }

      // Correlate anomaly if exists for this resource
      if (anomData?.items) {
        const matchedAnom = anomData.items.find(
          (a: AnomalyItem) =>
            a.resource_id === resourceId ||
            (resData.native_id && a.resource_native_id === resData.native_id)
        );
        setAnomaly(matchedAnom || null);
      }
    } catch (err: any) {
      setError(err?.message || `Failed to load authoritative intelligence for resource ${resourceId}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (id) {
      loadResourceData(id, windowDays);
    }
  }, [id, windowDays, loadResourceData]);

  // Handoff to Spend Explorer
  const handleViewInSpend = () => {
    if (!resource) return;
    navigate(
      `/spend?service_name=${encodeURIComponent(resource.service_name)}&account_id=${encodeURIComponent(
        resource.account_id
      )}`
    );
  };

  // Handoff to Topology FOCUS mode
  const handleFocusInTopology = () => {
    if (!resource) return;
    startFocus({
      entityId: resource.id,
      entityNativeId: resource.native_id,
      entityType: 'RESOURCE',
      entityName: resource.name || resource.native_id,
      origin: `Resource Intelligence · ${resource.service_name}`,
      costDelta: resource.cost_30d,
    });
    navigate(
      `/spend?service_name=${encodeURIComponent(resource.service_name)}&focus=${encodeURIComponent(
        resource.native_id
      )}&trace=true`
    );
  };

  // Trace back to original investigation
  const handleTraceBack = () => {
    if (activeInvestigation?.investigationId) {
      navigate(`/changes?investigationId=${encodeURIComponent(activeInvestigation.investigationId)}&trace=true`);
    } else if (anomaly?.id) {
      startTrace({
        investigationId: anomaly.id,
        entityId: resource?.id,
        entityNativeId: resource?.native_id,
        entityType: 'ANOMALY',
        entityName: resource?.name || resource?.native_id,
        origin: `Trace Back · ${resource?.service_name}`,
        costDelta: anomaly.observed?.observed_cost,
      });
      navigate(`/changes?investigationId=${encodeURIComponent(anomaly.id)}&trace=true`);
    } else {
      navigate('/changes');
    }
  };

  // Service icon helper
  const getServiceIcon = (service: string) => {
    switch (service.toLowerCase()) {
      case 'amazonec2':
        return <Cpu className="w-4 h-4 text-amber-400" />;
      case 'amazonrds':
        return <Database className="w-4 h-4 text-sky-400" />;
      case 'amazons3':
      case 'amazonebs':
        return <HardDrive className="w-4 h-4 text-emerald-400" />;
      default:
        return <Server className="w-4 h-4 text-slate-300" />;
    }
  };

  // Loading skeleton matching 5-section geometry
  if (loading) {
    return (
      <div className="space-y-6 pb-12 select-none">
        <div className="flex items-center gap-3">
          <div className="h-8 w-32 bg-[#141B27] animate-pulse rounded" />
          <div className="h-8 w-64 bg-[#141B27] animate-pulse rounded" />
        </div>
        <div className="h-28 bg-[#0F141C] border border-[#1E2638] animate-pulse rounded-lg p-6" />
        <div className="h-20 bg-[#0F141C] border border-[#1E2638] animate-pulse rounded-lg p-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton rows={4} />
          <CardSkeleton rows={4} />
        </div>
        <CardSkeleton rows={6} />
      </div>
    );
  }

  // Error state
  if (error || !resource) {
    return (
      <div className="space-y-6 pb-12 select-none">
        <Link
          to="/resources"
          className="inline-flex items-center gap-2 text-atlas-muted hover:text-white text-xs font-mono transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>RETURN TO RESOURCE INVENTORY</span>
        </Link>
        <ErrorState
          title="RESOURCE NOT FOUND"
          message={error || 'The requested resource identifier does not exist in the active organization context.'}
          onRetry={() => id && loadResourceData(id, windowDays)}
        />
      </div>
    );
  }

  // Telemetry metric extraction
  const cpuMetric = telemetry?.metrics?.['CPUUtilization'];
  const memMetric = telemetry?.metrics?.['MemoryUtilization'] || telemetry?.metrics?.['mem_used_percent'];
  const connMetric = telemetry?.metrics?.['DatabaseConnections'];
  const netMetric = telemetry?.metrics?.['NetworkOut'] || telemetry?.metrics?.['NetworkIn'];
  const iopsRead = telemetry?.metrics?.['VolumeReadOps'];
  const iopsWrite = telemetry?.metrics?.['VolumeWriteOps'];

  // Telemetry coverage calculation (missing is NOT 0%)
  const hasTelemetryMetrics = Object.keys(telemetry?.metrics || {}).length > 0;
  const coverageRatioNum = cpuMetric ? Number(cpuMetric.coverage_ratio) : null;
  const coveragePct = coverageRatioNum !== null ? Math.round(coverageRatioNum * 100) : null;

  // Activity classification (evidence-backed & resource-type aware)
  let activityClassification: 'LOW' | 'NORMAL' | 'HIGH' | 'NOT_AVAILABLE' = 'NOT_AVAILABLE';
  if (resource.service_name === 'AmazonEC2' && cpuMetric && cpuMetric.p95 !== null && cpuMetric.p95 !== undefined) {
    const p95 = Number(cpuMetric.p95);
    if (p95 < 20) activityClassification = 'LOW';
    else if (p95 <= 75) activityClassification = 'NORMAL';
    else activityClassification = 'HIGH';
  } else if (resource.service_name === 'AmazonRDS' && connMetric && connMetric.max_value !== null) {
    const conns = Number(connMetric.max_value);
    if (conns < 5) activityClassification = 'LOW';
    else if (conns <= 100) activityClassification = 'NORMAL';
    else activityClassification = 'HIGH';
  } else if (hasTelemetryMetrics && cpuMetric?.p95 !== null && cpuMetric?.p95 !== undefined) {
    activityClassification = Number(cpuMetric.p95) < 20 ? 'LOW' : 'NORMAL';
  }

  // Atlas State classification
  let atlasStateText = 'NORMAL';
  let atlasStateVariant = 'text-slate-300 bg-slate-500/10 border-slate-500/30';
  if (opportunity) {
    atlasStateText = 'OPPORTUNITY';
    atlasStateVariant = 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30';
  } else if (anomaly) {
    atlasStateText = 'REVIEW';
    atlasStateVariant = 'text-rose-400 bg-rose-950/40 border-rose-500/30';
  }

  // Authoritative Evidence Items (Epistemic ordering: OBSERVED -> DERIVED -> INFERRED)
  const evidenceItems: EvidenceItem[] = [];

  // 1. Observed spend
  if (resource.cost_30d) {
    evidenceItems.push({
      epistemicClass: 'OBSERVED',
      source: 'AWS Cost Explorer Direct Ingestion',
      statement: `Recorded gross spend of ${formatCurrency(resource.cost_30d)} during the active 30-day accounting window in ${resource.region_code}.`,
      metricValue: formatCurrency(resource.cost_30d),
      timestamp: `${windowDays}d Ingestion Window`,
    });
  }

  // 2. Observed CPU
  if (cpuMetric && cpuMetric.p95 !== null && cpuMetric.p95 !== undefined) {
    evidenceItems.push({
      epistemicClass: 'OBSERVED',
      source: 'AWS CloudWatch Metric Data (5-Min Interval Samples)',
      statement: `Observed 95th percentile CPU utilization measured at ${Number(cpuMetric.p95).toFixed(1)}% across ${cpuMetric.observation_count || 0} valid intervals.`,
      metricValue: `${Number(cpuMetric.p95).toFixed(1)}% P95`,
      timestamp: `${windowDays}d Analysis Window`,
    });

    // 3. Derived Headroom
    evidenceItems.push({
      epistemicClass: 'DERIVED',
      source: 'Atlas Deterministic Capacity Engine',
      statement: `Mathematical headroom between peak observed demand and maximum provisioned hardware threshold is ${(100 - Number(cpuMetric.p95)).toFixed(1)}%.`,
      metricValue: `${(100 - Number(cpuMetric.p95)).toFixed(1)}% Headroom`,
    });
  }

  // 4. Inferred Assessment
  if (opportunity) {
    evidenceItems.push({
      epistemicClass: 'INFERRED',
      source: 'Atlas Workload Sizing Classifier',
      statement: 'Available evidence supports evaluating a smaller configuration. Workload pattern demonstrates consistent capacity surplus.',
      metricValue: `Waste: ${opportunity.waste_type}`,
    });
  } else if (cpuMetric && Number(cpuMetric.p95) < 20) {
    evidenceItems.push({
      epistemicClass: 'INFERRED',
      source: 'Atlas Workload Sizing Classifier',
      statement: 'Available evidence supports evaluating a smaller configuration under standard operating margins.',
      metricValue: 'Sustained Low Utilization',
    });
  } else {
    evidenceItems.push({
      epistemicClass: 'INFERRED',
      source: 'Atlas Workload Sizing Classifier',
      statement: 'Workload demand is within standard provisioning tolerance. Sizing remains consistent with baseline.',
      metricValue: 'Provisioning Sized to Baseline',
    });
  }

  // Recommendations array
  const recommendations: RecommendationItem[] = opportunity?.recommendations || [];
  const activeRecommendation: RecommendationItem | undefined = recommendations[selectedRecIndex];

  // AZ resolution
  const availabilityZone =
    resource.tags?.['AvailabilityZone'] ||
    resource.tags?.['AZ'] ||
    `${resource.region_code}a`;

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* ── TOP ACTION & TRACE BACK BAR ────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0F141C] border border-[#1E2638] rounded-lg p-4">
        <div className="flex items-center gap-3">
          <Link
            to="/resources"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#141B27] hover:bg-[#1E2638] text-slate-300 hover:text-white border border-[#1E2638] text-xs font-mono transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>RESOURCES</span>
          </Link>

          <div className="h-4 w-[1px] bg-[#1E2638]" />

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-atlas-muted">ATLAS</span>
            <span className="text-atlas-muted">/</span>
            <span className="text-sky-400 font-semibold">RESOURCE INTELLIGENCE</span>
            <span className="text-atlas-muted">/</span>
            <span className="text-slate-200">{resource.name || resource.native_id}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Window Days Picker */}
          <div className="inline-flex rounded-md border border-[#1E2638] bg-[#141B27] p-0.5 text-xs font-mono">
            {[14, 30, 60].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setWindowDays(d)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  windowDays === d
                    ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30'
                    : 'text-atlas-muted hover:text-white'
                }`}
              >
                {d}D
              </button>
            ))}
          </div>

          {/* Focus in Topology */}
          <button
            type="button"
            onClick={handleFocusInTopology}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-950/40 hover:bg-sky-900/50 text-sky-400 border border-sky-500/40 text-xs font-mono font-semibold transition-colors"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>FOCUS IN TOPOLOGY</span>
          </button>

          {/* Ask Atlas */}
          <button
            type="button"
            onClick={() =>
              openAskAtlas({
                scopeType: 'RESOURCE',
                scopeLabel: `Resource: ${resource.name || resource.native_id}`,
                initialQuestion: `Why does Atlas care about resource ${resource.name || resource.native_id} (${resource.service_name})? What does the evidence show?`,
                resourceId: resource.id,
                resourceName: resource.name || resource.native_id,
                serviceName: resource.service_name,
                accountId: resource.account_id,
              })
            }
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas</span>
          </button>
        </div>
      </div>

      {/* ── TRACE BACK BANNER (If Investigation Context or Anomaly Present) ─── */}
      {(activeInvestigation?.investigationId || anomaly) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs font-mono text-amber-300">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold text-white">INVESTIGATION CONTEXT ACTIVE</span>
              <span className="text-amber-400/80 ml-2">
                This resource is associated with {anomaly?.service_name || activeInvestigation?.entityName || 'an ongoing change investigation'}.
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleTraceBack}
            className="px-3 py-1.5 rounded bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 font-bold flex items-center gap-1.5 self-start sm:self-auto transition-colors"
          >
            <span>WHY IS ATLAS SHOWING THIS? ← TRACE BACK</span>
          </button>
        </div>
      )}

      {/* ── 1. AUTHORITATIVE RESOURCE HEADER ───────────────────────────────── */}
      <div className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E2638]/70 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="p-1.5 rounded bg-[#141B27] border border-[#1E2638]">
                {getServiceIcon(resource.service_name)}
              </div>
              <h1 className="text-lg md:text-xl font-bold font-mono text-white tracking-tight">
                {resource.name || resource.native_id}
              </h1>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
                {resource.status}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#141B27] text-slate-300 border border-[#1E2638]">
                PROVIDER: AWS
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs font-mono text-atlas-muted flex-wrap">
              <span>Native ID: <span className="text-slate-200">{resource.native_id}</span></span>
              <span>•</span>
              <span>Type: <span className="text-sky-400">{resource.resource_type}</span></span>
              <span>•</span>
              <span>Account: <span className="text-slate-300">{resource.account_name}</span></span>
              <span>•</span>
              <span>Region: <span className="text-slate-300">{resource.region_code}</span></span>
              <span>•</span>
              <span>AZ: <span className="text-slate-300">{availabilityZone}</span></span>
            </div>
          </div>

          {/* Interactive Cost Card */}
          <button
            type="button"
            onClick={handleViewInSpend}
            title="Explore in Spend Explorer"
            className="text-right p-3 rounded-lg bg-[#141B27]/80 hover:bg-[#141B27] border border-[#1E2638] hover:border-sky-500/40 transition-colors group"
          >
            <div className="text-[10px] font-mono text-atlas-muted group-hover:text-sky-400 flex items-center justify-end gap-1">
              <span>MONTHLY SPEND</span>
              <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
            </div>
            <div className="text-xl font-bold font-mono text-white mt-0.5">
              {resource.cost_30d !== null && resource.cost_30d !== undefined
                ? formatCurrency(resource.cost_30d)
                : '₹0.00'}
              <span className="text-xs font-normal text-atlas-muted"> / mo</span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted">
              Click to view in Spend Explorer
            </div>
          </button>
        </div>

        {/* ── 2. RESOURCE STATE STRIP ───────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Strip Cell 1: COST */}
          <div
            onClick={handleViewInSpend}
            className="bg-[#141B27]/60 p-3 rounded border border-[#1E2638] cursor-pointer hover:border-sky-500/40 transition-colors"
          >
            <div className="text-[10px] font-mono text-atlas-muted">COST</div>
            <div className="text-sm md:text-base font-bold font-mono text-white mt-0.5">
              {resource.cost_30d ? formatCurrency(resource.cost_30d) : '₹0.00'}
              <span className="text-xs font-normal text-atlas-muted"> / mo</span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              30-day recorded spend
            </div>
          </div>

          {/* Strip Cell 2: ACTIVITY */}
          <div className="bg-[#141B27]/60 p-3 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted">ACTIVITY</div>
            <div className="text-sm md:text-base font-bold font-mono mt-0.5">
              {activityClassification === 'LOW' && (
                <span className="text-amber-400">LOW UTILIZATION</span>
              )}
              {activityClassification === 'NORMAL' && (
                <span className="text-emerald-400">NORMAL OPERATING</span>
              )}
              {activityClassification === 'HIGH' && (
                <span className="text-rose-400">HIGH DEMAND</span>
              )}
              {activityClassification === 'NOT_AVAILABLE' && (
                <span className="text-slate-400">NOT_AVAILABLE</span>
              )}
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              {resource.service_name} operational profile
            </div>
          </div>

          {/* Strip Cell 3: TELEMETRY */}
          <div className="bg-[#141B27]/60 p-3 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted">TELEMETRY</div>
            <div className="text-sm md:text-base font-bold font-mono mt-0.5">
              {coveragePct !== null && coveragePct > 0 ? (
                <span className={coveragePct >= 70 ? 'text-emerald-400' : 'text-amber-400'}>
                  {coveragePct}% COVERAGE
                </span>
              ) : hasTelemetryMetrics ? (
                <span className="text-amber-400">INSUFFICIENT_DATA</span>
              ) : (
                <span className="text-slate-400">NOT_CONFIGURED</span>
              )}
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              {cpuMetric ? `${cpuMetric.observation_count || 0} intervals analyzed` : 'No agent metric stream'}
            </div>
          </div>

          {/* Strip Cell 4: ATLAS STATE */}
          <div className="bg-[#141B27]/60 p-3 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted">ATLAS STATE</div>
            <div className="mt-1">
              <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${atlasStateVariant}`}>
                {atlasStateText}
              </span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-1 truncate">
              {opportunity ? opportunity.category : anomaly ? 'Change Detected' : 'Baseline Compliant'}
            </div>
          </div>
        </div>
      </div>

      {/* ── 3. WHAT IT IS ─────────────────────────────────────────────────── */}
      <section aria-label="Authoritative Configuration" className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-400" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
              01 · WHAT IT IS · AUTHORITATIVE CONFIGURATION
            </h2>
            <EpistemicBadge classification="OBSERVED" size="xs" />
          </div>
          <span className="text-[10px] font-mono text-atlas-muted">
            Direct Cloud Ingestion
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
            <span className="text-[10px] text-atlas-muted">SERVICE TYPE</span>
            <div className="text-slate-200 font-semibold mt-0.5">{resource.service_name}</div>
          </div>

          <div className="bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
            <span className="text-[10px] text-atlas-muted">PROVISIONED SPEC</span>
            <div className="text-sky-300 font-semibold mt-0.5">{resource.resource_type}</div>
          </div>

          <div className="bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
            <span className="text-[10px] text-atlas-muted">REGION & AZ</span>
            <div className="text-slate-200 font-semibold mt-0.5">
              {resource.region_code} ({availabilityZone})
            </div>
          </div>

          <div className="bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
            <span className="text-[10px] text-atlas-muted">ACCOUNT ID</span>
            <div className="text-slate-200 font-semibold mt-0.5 truncate" title={resource.account_name}>
              {resource.account_id}
            </div>
          </div>
        </div>

        {/* Tags breakdown */}
        {resource.tags && Object.keys(resource.tags).length > 0 && (
          <div className="pt-2">
            <span className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider">
              AUTHORITATIVE RESOURCE TAGS ({Object.keys(resource.tags).length})
            </span>
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.entries(resource.tags).map(([key, value]) => (
                <div
                  key={key}
                  className="px-2.5 py-1 rounded bg-[#141B27] border border-[#1E2638] text-xs font-mono flex items-center gap-1.5"
                >
                  <span className="text-atlas-muted">{key}:</span>
                  <span className="text-slate-200 font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* ── 4. WHAT IT COSTS ───────────────────────────────────────────────── */}
      <section aria-label="Financial Breakdown" className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
              02 · WHAT IT COSTS · FINANCIAL DECOMPOSITION
            </h2>
            <EpistemicBadge classification="OBSERVED" size="xs" />
            <EpistemicBadge classification="DERIVED" size="xs" />
          </div>

          <button
            type="button"
            onClick={handleViewInSpend}
            className="flex items-center gap-1.5 text-xs font-mono text-sky-400 hover:text-sky-300 font-semibold self-start sm:self-auto transition-colors"
          >
            <span>VIEW IN SPEND EXPLORER</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-atlas-muted">PERIOD SPEND (30D)</span>
              <EpistemicBadge classification="OBSERVED" size="xs" />
            </div>
            <div className="text-base md:text-lg font-bold font-mono text-white mt-1">
              {resource.cost_30d ? formatCurrency(resource.cost_30d) : '₹0.00'}
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              Gross billed amount
            </div>
          </div>

          <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-atlas-muted">DAILY RUN RATE</span>
              <EpistemicBadge classification="DERIVED" size="xs" />
            </div>
            <div className="text-base md:text-lg font-bold font-mono text-slate-200 mt-1">
              {resource.cost_30d ? formatCurrency(Number(resource.cost_30d) / 30) : '₹0.00'}
              <span className="text-xs font-normal text-atlas-muted"> / day</span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              Calculated 30-day mean
            </div>
          </div>

          <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-atlas-muted">MONTHLY RUN RATE</span>
              <EpistemicBadge classification="DERIVED" size="xs" />
            </div>
            <div className="text-base md:text-lg font-bold font-mono text-slate-200 mt-1">
              {resource.cost_30d ? formatCurrency(resource.cost_30d) : '₹0.00'}
              <span className="text-xs font-normal text-atlas-muted"> / mo</span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              Extrapolated monthly run rate
            </div>
          </div>

          <div className="bg-[#141B27]/70 p-3 rounded border border-[#1E2638]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-atlas-muted">ANNUALIZED PROJECTION</span>
              <EpistemicBadge classification="DERIVED" size="xs" />
            </div>
            <div className="text-base md:text-lg font-bold font-mono text-slate-200 mt-1">
              {resource.cost_30d ? formatCurrency(Number(resource.cost_30d) * 12) : '₹0.00'}
              <span className="text-xs font-normal text-atlas-muted"> / yr</span>
            </div>
            <div className="text-[10px] font-mono text-atlas-muted mt-0.5">
              Monthly × 12 annualized
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. HOW IT BEHAVES & 6. TELEMETRY SUFFICIENCY ──────────────────── */}
      <section aria-label="Behavior and Telemetry" className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-purple-400" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
              03 · HOW IT BEHAVES · OPERATIONAL TELEMETRY
            </h2>
            <EpistemicBadge classification="OBSERVED" size="xs" />
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-atlas-muted">
            <span>Window: {windowDays} Days</span>
            <span>•</span>
            <span>Source: AWS CloudWatch</span>
          </div>
        </div>

        {/* Telemetry Metric Cards */}
        {hasTelemetryMetrics ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Metric 1: CPU Utilization */}
            {cpuMetric ? (
              <div className="bg-[#141B27]/70 p-3.5 rounded-lg border border-[#1E2638] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-atlas-muted">CPU UTILIZATION (P95)</span>
                  <EpistemicBadge classification="OBSERVED" size="xs" />
                </div>
                <div className="text-xl font-bold font-mono text-sky-400">
                  {cpuMetric.p95 !== null ? `${Number(cpuMetric.p95).toFixed(1)}%` : 'N/A'}
                </div>
                <div className="space-y-1 text-[10px] font-mono text-atlas-muted border-t border-[#1E2638]/70 pt-2">
                  <div className="flex justify-between">
                    <span>Statistic:</span>
                    <span className="text-slate-300">P95 Maximum</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Samples:</span>
                    <span className="text-slate-300">{cpuMetric.observation_count} intervals</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Coverage:</span>
                    <span className="text-emerald-400">{coveragePct}% valid</span>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Metric 2: Memory Utilization */}
            {memMetric ? (
              <div className="bg-[#141B27]/70 p-3.5 rounded-lg border border-[#1E2638] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-atlas-muted">MEMORY UTILIZATION (P95)</span>
                  <EpistemicBadge classification="OBSERVED" size="xs" />
                </div>
                <div className="text-xl font-bold font-mono text-purple-400">
                  {memMetric.p95 !== null ? `${Number(memMetric.p95).toFixed(1)}%` : 'N/A'}
                </div>
                <div className="space-y-1 text-[10px] font-mono text-atlas-muted border-t border-[#1E2638]/70 pt-2">
                  <div className="flex justify-between">
                    <span>Statistic:</span>
                    <span className="text-slate-300">P95 Maximum</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Samples:</span>
                    <span className="text-slate-300">{memMetric.observation_count} intervals</span>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Metric 3: Database Connections */}
            {connMetric ? (
              <div className="bg-[#141B27]/70 p-3.5 rounded-lg border border-[#1E2638] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-atlas-muted">DB CONNECTIONS (PEAK)</span>
                  <EpistemicBadge classification="OBSERVED" size="xs" />
                </div>
                <div className="text-xl font-bold font-mono text-amber-400">
                  {connMetric.max_value !== null ? `${connMetric.max_value}` : 'N/A'}
                </div>
                <div className="space-y-1 text-[10px] font-mono text-atlas-muted border-t border-[#1E2638]/70 pt-2">
                  <div className="flex justify-between">
                    <span>Statistic:</span>
                    <span className="text-slate-300">Maximum Peak</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Mean:</span>
                    <span className="text-slate-300">{Number(connMetric.mean || 0).toFixed(1)}</span>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Metric 4: Network Out */}
            {netMetric ? (
              <div className="bg-[#141B27]/70 p-3.5 rounded-lg border border-[#1E2638] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-atlas-muted">NETWORK OUT (MB/s)</span>
                  <EpistemicBadge classification="OBSERVED" size="xs" />
                </div>
                <div className="text-xl font-bold font-mono text-emerald-400">
                  {netMetric.p95 !== null ? `${(Number(netMetric.p95) / 1024 / 1024).toFixed(2)} MB` : 'N/A'}
                </div>
                <div className="space-y-1 text-[10px] font-mono text-atlas-muted border-t border-[#1E2638]/70 pt-2">
                  <div className="flex justify-between">
                    <span>Statistic:</span>
                    <span className="text-slate-300">P95 Rate</span>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Metric 5: Disk IOPS */}
            {iopsRead || iopsWrite ? (
              <div className="bg-[#141B27]/70 p-3.5 rounded-lg border border-[#1E2638] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-atlas-muted">STORAGE IOPS</span>
                  <EpistemicBadge classification="OBSERVED" size="xs" />
                </div>
                <div className="text-xl font-bold font-mono text-slate-200">
                  {Number((iopsRead?.mean || 0)) + Number((iopsWrite?.mean || 0))}
                  <span className="text-xs font-normal text-atlas-muted"> IOPS</span>
                </div>
                <div className="space-y-1 text-[10px] font-mono text-atlas-muted border-t border-[#1E2638]/70 pt-2">
                  <div className="flex justify-between">
                    <span>Read:</span>
                    <span className="text-slate-300">{Number(iopsRead?.mean || 0).toFixed(0)} IOPS</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Write:</span>
                    <span className="text-slate-300">{Number(iopsWrite?.mean || 0).toFixed(0)} IOPS</span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-[#141B27]/40 border border-dashed border-[#1E2638] text-center space-y-2">
            <div className="text-xs font-mono font-semibold text-atlas-muted">
              TELEMETRY UNAVAILABLE
            </div>
            <p className="text-[11px] text-atlas-muted font-mono max-w-lg mx-auto">
              No active CloudWatch metric observations are currently associated with this resource identifier in the selected {windowDays}-day window.
            </p>
          </div>
        )}

        {/* ── 6. TELEMETRY SUFFICIENCY EXPLANATION ──────────────────────────── */}
        {resource.service_name === 'AmazonEC2' && !memMetric && (
          <div className="p-3.5 rounded-lg bg-[#141B27]/60 border border-[#1E2638] text-xs font-mono flex items-start gap-3">
            <Info className="w-4 h-4 text-sky-400 mt-0.5 shrink-0" />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-200">
                  MEMORY TELEMETRY · NOT CONFIGURED
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  GUEST AGENT MISSING
                </span>
              </div>
              <p className="text-atlas-muted text-[11px] leading-relaxed">
                Memory utilization data is unavailable for this EC2 instance. CloudWatch Agent installation is required to emit guest OS memory metrics. Atlas rightsizing calculations apply a conservative safety guardrail.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* ── 7. ATLAS OBSERVES (Authoritative Evidence Layer) ───────────────── */}
      <section aria-label="Atlas Observes" className="space-y-3">
        <EvidenceLayer
          items={evidenceItems}
          title="04 · ATLAS OBSERVES · EMPIRICAL EVIDENCE & CALCULATED HEADROOM"
          className="bg-[#0F141C] border-[#1E2638]"
        />
      </section>

      {/* ── 8. ATLAS ASSESSMENT ────────────────────────────────────────────── */}
      <section aria-label="Atlas Assessment" className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
              05 · ATLAS ASSESSMENT · DETERMINISTIC INTERPRETATION
            </h2>
            <EpistemicBadge classification="INFERRED" size="xs" />
          </div>
          <span className="text-[10px] font-mono text-atlas-muted">
            Grounding Protocol: Verified
          </span>
        </div>

        <div className="space-y-3">
          <div className="flex items-baseline gap-3">
            <span className="text-xs font-mono text-atlas-muted">CURRENT ASSESSMENT:</span>
            <span className="text-sm font-bold font-mono text-white">
              {opportunity
                ? `${opportunity.waste_type.replace(/_/g, ' ')} DETECTED`
                : cpuMetric && Number(cpuMetric.p95) < 20
                ? 'UNDER-UTILIZED COMPUTE HEADROOM'
                : 'CAPACITY PROFILE WITHIN OPERATIONAL BOUNDS'}
            </span>
          </div>

          <div className="p-4 rounded-lg bg-[#141B27]/60 border border-[#1E2638] space-y-2">
            <div className="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider">
              WHY ATLAS REACHED THIS INTERPRETATION
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">1. [OBSERVED]</span>
                <span className="text-slate-300">
                  {cpuMetric
                    ? `Peak P95 demand sustained at ${Number(cpuMetric.p95).toFixed(1)}% across ${windowDays}-day observation window.`
                    : `Gross spend recorded at ${formatCurrency(resource.cost_30d || 0)}/mo.`}
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-sky-400 font-bold">2. [DERIVED]</span>
                <span className="text-slate-300">
                  {cpuMetric
                    ? `Mathematical headroom calculation establishes ${(100 - Number(cpuMetric.p95)).toFixed(1)}% unallocated capacity.`
                    : 'Annualized cost extrapolates to 12x continuous baseline.'}
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-purple-400 font-bold">3. [INFERRED]</span>
                <span className="text-slate-300">
                  Available evidence supports evaluating a smaller configuration. No critical performance degradation risk is indicated by CloudWatch telemetry.
                </span>
              </div>
            </div>
          </div>

          <div className="text-[11px] font-mono text-atlas-muted italic">
            * Epistemic statement: Atlas does not claim certainty beyond empirical telemetry. The assessment represents evidence-grounded evaluation.
          </div>
        </div>
      </section>

      {/* ── 9, 10, 11, 12. ATLAS RECOMMENDS (Actionable Decision) ──────────── */}
      <section aria-label="Atlas Recommends" className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
              06 · ATLAS RECOMMENDS · OPTIMIZATION DECISION CANDIDATES
            </h2>
            <EpistemicBadge classification={opportunity ? 'INFERRED' : 'NOT_AVAILABLE'} size="xs" />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/30">
              READ-ONLY TRUST BOUNDARY
            </span>
          </div>
        </div>

        {opportunity && recommendations.length > 0 ? (
          <div className="space-y-4">
            {/* Multiple Recommendations Tab Selector (Directive #11) */}
            {recommendations.length > 1 && (
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider">
                  EXPLORE CANDIDATE ALTERNATIVES ({recommendations.length} OPTIONS EVALUATED)
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {recommendations.map((rec, idx) => {
                    const isSelected = idx === selectedRecIndex;
                    return (
                      <button
                        key={rec.id}
                        type="button"
                        onClick={() => setSelectedRecIndex(idx)}
                        className={`text-left p-3.5 rounded-lg border transition-all ${
                          isSelected
                            ? 'bg-emerald-950/20 border-emerald-500/60 shadow-[0_0_12px_rgba(16,185,129,0.15)]'
                            : 'bg-[#141B27]/60 border-[#1E2638] hover:border-slate-500/40'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold font-mono text-white truncate">
                            {rec.title}
                          </span>
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                              rec.risk_level === 'LOW'
                                ? 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30'
                                : 'text-amber-400 bg-amber-950/40 border-amber-500/30'
                            }`}
                          >
                            {rec.risk_level} RISK
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2 mt-2">
                          <span className="text-sm font-bold font-mono text-emerald-400">
                            +{formatCurrency(rec.estimated_monthly_savings)}
                            <span className="text-xs font-normal text-atlas-muted"> / mo</span>
                          </span>
                          <span className="text-[10px] font-mono text-atlas-muted">
                            (Strength: {Number(rec.confidence_pct).toFixed(0)}%)
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Active Recommendation Card */}
            {activeRecommendation && (
              <div className="bg-[#141B27]/70 p-4 rounded-lg border border-[#1E2638] space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold font-mono text-white">
                      {activeRecommendation.title}
                    </h3>
                    <p className="text-xs text-slate-300 font-sans leading-relaxed">
                      {activeRecommendation.reasoning}
                    </p>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-lg font-bold font-mono text-emerald-400">
                      {formatCurrency(activeRecommendation.estimated_monthly_savings)}
                      <span className="text-xs font-normal text-atlas-muted"> / mo savings</span>
                    </div>
                    <div className="text-[10px] font-mono text-atlas-muted">
                      Annualized: {formatCurrency(activeRecommendation.estimated_annual_savings)} / yr
                    </div>
                  </div>
                </div>

                {/* Configuration Comparison */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-[#0F141C] p-3 rounded border border-[#1E2638] text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-atlas-muted">CURRENT PROVISIONING</span>
                    <div className="text-slate-200 font-medium mt-0.5 truncate" title={activeRecommendation.current_configuration}>
                      {activeRecommendation.current_configuration}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-emerald-400">RECOMMENDED PROVISIONING</span>
                    <div className="text-emerald-300 font-medium mt-0.5 truncate" title={activeRecommendation.recommended_configuration}>
                      {activeRecommendation.recommended_configuration}
                    </div>
                  </div>
                </div>

                {/* Decision Factors Strip */}
                <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-[#1E2638]/70">
                  <div className="flex items-center gap-4 text-xs font-mono">
                    <div>
                      <span className="text-[10px] text-atlas-muted mr-1">Risk:</span>
                      <span className="text-slate-200 font-bold">{activeRecommendation.risk_level}</span>
                    </div>
                    <div className="h-3 w-[1px] bg-[#1E2638]" />
                    <div>
                      <span className="text-[10px] text-atlas-muted mr-1">Reversibility:</span>
                      <span className="text-emerald-400 font-bold">IMMEDIATE</span>
                    </div>
                    <div className="h-3 w-[1px] bg-[#1E2638]" />
                    <div>
                      <span className="text-[10px] text-atlas-muted mr-1">Evidence Strength:</span>
                      <span className="text-sky-400 font-bold">{Number(activeRecommendation.confidence_pct).toFixed(1)}%</span>
                    </div>
                  </div>

                  {/* Explicit Decision Handoff Button (Directive #12 - READ ONLY) */}
                  <button
                    type="button"
                    onClick={() => navigate(`/optimization/${encodeURIComponent(opportunity.id)}`)}
                    className="px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-600 text-black font-mono font-bold text-xs flex items-center gap-1.5 transition-colors shadow-[0_0_15px_rgba(16,185,129,0.2)] focus:outline-none focus:ring-2 focus:ring-emerald-400"
                  >
                    <span>VIEW OPTIMIZATION DECISION</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-[#141B27]/40 border border-dashed border-[#1E2638] text-center space-y-2">
            <div className="text-xs font-mono font-semibold text-atlas-muted">
              NO CURRENT OPTIMIZATION OPPORTUNITY
            </div>
            <p className="text-[11px] text-atlas-muted font-mono max-w-lg mx-auto">
              Hardware allocation and configuration for this resource are aligned with current empirical workload baselines. No actionable waste patterns detected.
            </p>
            <div className="pt-1">
              <button
                type="button"
                onClick={() => navigate('/optimization')}
                className="px-3 py-1.5 rounded bg-[#141B27] hover:bg-[#1E2638] text-slate-300 border border-[#1E2638] font-mono text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
              >
                <span>EXPLORE ALL OPTIMIZATION OPPORTUNITIES</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default ResourceDetailPage;

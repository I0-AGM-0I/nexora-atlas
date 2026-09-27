import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type { AnomalyListResponse, AnomalyItem } from '../types/api';
import { CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { AlertTriangle, RefreshCw, ArrowRight, Sparkles, Compass } from 'lucide-react';
import { EpistemicBadge } from '../components/ui/EpistemicBadge';
import { formatCurrency, formatDate } from '../lib/format';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { useInvestigation } from '../lib/InvestigationContext';
import { InvestigationTrace } from '../components/investigation/InvestigationTrace';

export const ChangesPage: React.FC = () => {
  const { id: routeId } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { openAskAtlas } = useAskAtlas();
  const { startTrace, clearTrace } = useInvestigation();

  const queryInvestigationId = searchParams.get('investigationId') || searchParams.get('id');
  const activeAnomalyId = routeId || queryInvestigationId;

  const [filterDomain, setFilterDomain] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnomalyListResponse | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalyItem | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchAnomalies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const resp = await api.getAnomalies();
      setData(resp);
    } catch (err: any) {
      setError(err?.message || 'Failed to load detected environment changes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnomalies();
  }, [fetchAnomalies]);

  // Synchronize active anomaly based on URL route or query param
  useEffect(() => {
    if (!activeAnomalyId) {
      setSelectedAnomaly(null);
      return;
    }

    // Check if anomaly already in list
    if (data?.items) {
      const found = data.items.find((i) => i.id === activeAnomalyId);
      if (found) {
        setSelectedAnomaly(found);
        return;
      }
    }

    // If not in list yet or direct page load with ID, fetch detail directly
    let isMounted = true;
    const fetchDetail = async () => {
      setLoadingDetail(true);
      try {
        const item = await api.getAnomalyDetail(activeAnomalyId);
        if (isMounted) {
          setSelectedAnomaly(item);
        }
      } catch (err: any) {
        if (isMounted) {
          console.error(`Failed to fetch anomaly detail for ${activeAnomalyId}:`, err);
        }
      } finally {
        if (isMounted) setLoadingDetail(false);
      }
    };

    fetchDetail();
    return () => {
      isMounted = false;
    };
  }, [activeAnomalyId, data]);

  // Open investigation trace for a specific anomaly
  const handleOpenInvestigation = (item: AnomalyItem) => {
    setSelectedAnomaly(item);
    startTrace({
      investigationId: item.id,
      entityId: item.resource_id,
      entityNativeId: item.resource_native_id,
      entityType: 'ANOMALY',
      entityName: item.resource_name || item.resource_native_id || item.service_name,
      origin: `Changes · ${item.service_name}`,
      costDelta: item.observed?.observed_cost,
    });
    // Set URL query param or route
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('investigationId', item.id);
      return next;
    });
  };

  // Exit investigation trace
  const handleCloseInvestigation = () => {
    setSelectedAnomaly(null);
    clearTrace();
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('investigationId');
      next.delete('id');
      next.delete('trace');
      return next;
    });
    if (routeId) {
      navigate('/changes', { replace: true });
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-950/50 text-rose-400 border border-rose-500/40">
            CRITICAL SPIKE
          </span>
        );
      case 'HIGH':
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-950/50 text-amber-400 border border-amber-500/40">
            MATERIAL CHANGE
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-sky-950/50 text-sky-400 border border-sky-500/40">
            MODERATE SHIFT
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#1E293B] text-slate-300 border border-[#334155]">
            {sev}
          </span>
        );
    }
  };

  // Filter items based on domain
  const filteredItems = data?.items.filter((item) => {
    if (filterDomain === 'ALL') return true;
    if (filterDomain === 'COST SPIKES') {
      return item.observed?.detection_rule?.includes('SPIKE') || item.observed?.detection_rule?.includes('ZSCORE');
    }
    if (filterDomain === 'USAGE SURGES') {
      return item.observed?.observed_metrics_json?.observed_compute_hours || item.observed?.observed_metrics_json?.active_gpu_hours;
    }
    if (filterDomain === 'INFRASTRUCTURE DRIFT') {
      return item.observed?.observed_metrics_json?.current_size_tb || item.observed?.detection_rule?.includes('GROWTH');
    }
    return true;
  }) || [];

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* If an anomaly is selected for investigation, render the 5-Stage Investigation Trace view */}
      {selectedAnomaly ? (
        <InvestigationTrace
          anomaly={selectedAnomaly}
          onClose={handleCloseInvestigation}
          onTraceBack={handleCloseInvestigation}
        />
      ) : loadingDetail ? (
        <div className="space-y-4">
          <div className="h-10 w-64 bg-[#141B27] animate-pulse rounded" />
          <CardSkeleton rows={4} />
          <CardSkeleton rows={6} />
        </div>
      ) : (
        <>
          {/* ── HEADER ──────────────────────────────────────────────────────── */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E2638] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <h1 className="text-xl font-bold tracking-tight text-atlas-text font-mono">
                  CHANGES
                </h1>
              </div>
              <p className="text-xs text-atlas-muted font-mono mt-0.5">
                Something changed in your technology environment · Material shifts detected across 90-day baseline
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() =>
                  openAskAtlas({
                    scopeType: 'DASHBOARD',
                    scopeLabel: 'Detected Environment Changes',
                    initialQuestion: 'What are the most critical technology spend changes detected recently?',
                  })
                }
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Ask Atlas About Changes</span>
              </button>

              <button
                type="button"
                onClick={fetchAnomalies}
                className="p-1.5 rounded-md border border-[#1E2638] bg-[#0F141C] text-atlas-muted hover:text-atlas-text transition-colors"
                title="Refresh Changes"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* ── DOMAIN FILTER BUTTONS ───────────────────────────────────────── */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-atlas-muted mr-1">Filter Change Type:</span>
            {['ALL', 'COST SPIKES', 'USAGE SURGES', 'INFRASTRUCTURE DRIFT'].map((domain) => (
              <button
                key={domain}
                type="button"
                onClick={() => setFilterDomain(domain)}
                className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                  filterDomain === domain
                    ? 'bg-amber-400/15 text-amber-400 border border-amber-400/40 font-semibold'
                    : 'bg-[#141B27] text-atlas-muted hover:text-atlas-text border border-[#1E2638]'
                }`}
              >
                {domain}
              </button>
            ))}
          </div>

          {loading && !data && (
            <div className="space-y-4">
              <CardSkeleton rows={4} />
              <CardSkeleton rows={4} />
            </div>
          )}

          {error && !data && <ErrorState message={error} onRetry={fetchAnomalies} />}

          {/* ── CHANGE CARDS LIST ────────────────────────────────────────────── */}
          {data && (
            <div className="space-y-4">
              {filteredItems.length === 0 ? (
                <EmptyState
                  title="No unexpected changes detected"
                  message="Daily costs and usage metrics are fluctuating within standard operational baselines."
                />
              ) : (
                filteredItems.map((item: AnomalyItem) => {
                  const actualCost = Number(item.observed?.observed_cost || 0);
                  const expectedCost = Number(item.observed?.baseline_cost || 0);
                  const costDelta = actualCost - expectedCost;
                  const severity = item.inference?.severity || 'MEDIUM';
                  const description =
                    item.inference?.inferred_cause ||
                    item.observed?.detection_rule ||
                    'Cost deviation detected';
                  const detectedDate = item.observed?.detected_at || new Date().toISOString();

                  return (
                    <div
                      key={item.id}
                      className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 hover:border-amber-500/40 transition-colors space-y-4"
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            {getSeverityBadge(severity)}
                            <h3 className="text-sm font-bold text-atlas-text font-mono">
                              {item.resource_name || item.resource_id || item.service_name}
                            </h3>
                            <span className="text-[11px] font-mono text-atlas-muted">
                              ({item.service_name})
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 font-sans">{description}</p>
                        </div>

                        <div className="text-right">
                          <div className="text-lg font-bold font-mono text-rose-400">
                            +{formatCurrency(costDelta)}
                            <span className="text-xs font-normal text-atlas-muted"> / day surge</span>
                          </div>
                          <div className="text-[11px] font-mono text-atlas-muted">
                            Detected: {formatDate(detectedDate)}
                          </div>
                        </div>
                      </div>

                      {/* Telemetry & Attribution Evidence Strip */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-[#141B27]/50 p-3 rounded-lg border border-[#1E2638]/60 text-xs font-mono">
                        <div>
                          <span className="text-atlas-muted text-[10px]">OBSERVED COST SHIFT</span>
                          <div className="text-slate-200 font-semibold mt-0.5">
                            {formatCurrency(actualCost)} / day
                          </div>
                          <div className="text-[10px] text-atlas-muted">
                            Baseline Mean: {formatCurrency(expectedCost)} / day
                          </div>
                        </div>

                        <div>
                          <span className="text-atlas-muted text-[10px]">STATISTICAL SEVERITY</span>
                          <div className="text-amber-400 font-semibold mt-0.5">
                            Severity: {severity}
                          </div>
                          <div className="text-[10px] text-atlas-muted">
                            Evidence Strength: {Number(item.inference?.confidence_pct || 90).toFixed(1)}%
                          </div>
                        </div>

                        <div>
                          <span className="text-atlas-muted text-[10px]">ACCOUNT & DOMAIN</span>
                          <div className="text-sky-300 font-semibold mt-0.5">
                            {item.account_name || 'Production Account'}
                          </div>
                          <div className="text-[10px] text-atlas-muted">{item.service_name}</div>
                        </div>
                      </div>

                      {/* Grounding Badges & Dual Actions (OPEN INVESTIGATION + TRACE IN TOPOLOGY) */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <EpistemicBadge classification="OBSERVED" size="xs" />
                          <EpistemicBadge classification="DERIVED" size="xs" />
                          <EpistemicBadge classification="INFERRED" size="xs" />
                          <span className="text-[10px] font-mono text-atlas-muted ml-2">
                            Root cause attribution grounded in CloudWatch & Cost Explorer
                          </span>
                        </div>

                        <div className="flex items-center gap-2 self-start sm:self-auto">
                          {/* 1. Open 5-Stage Investigation Trace */}
                          <button
                            type="button"
                            onClick={() => handleOpenInvestigation(item)}
                            className="text-xs font-mono font-semibold px-3 py-1.5 rounded bg-amber-500/10 border border-amber-500/40 text-amber-400 hover:text-amber-300 hover:bg-amber-500/20 flex items-center gap-1.5 transition-colors focus:outline-none focus:ring-1 focus:ring-amber-500"
                          >
                            <span>OPEN INVESTIGATION</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>

                          {/* 2. Trace in Cost Topology */}
                          <button
                            type="button"
                            onClick={() =>
                              startTrace(
                                {
                                  investigationId: item.id,
                                  entityId: item.resource_id,
                                  entityNativeId: item.resource_native_id,
                                  entityType: 'ANOMALY',
                                  entityName: item.resource_name || item.resource_native_id,
                                  origin: `Changes Anomaly · ${item.service_name}`,
                                  costDelta: actualCost,
                                },
                                `/spend?service_name=${encodeURIComponent(item.service_name || '')}&trace=true&investigationId=${encodeURIComponent(item.id)}`
                              )
                            }
                            className="text-xs font-mono font-semibold px-3 py-1.5 rounded bg-sky-950/40 border border-sky-500/40 text-sky-400 hover:text-sky-300 hover:bg-sky-900/40 flex items-center gap-1.5 transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
                          >
                            <span>TRACE IN TOPOLOGY</span>
                            <Compass className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ChangesPage;

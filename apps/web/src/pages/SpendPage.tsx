import React, { useState, useEffect, useCallback } from 'react';

import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../lib/api';
import type {
  SpendExplorerResponse,
  AnalyticsSummaryResponse,
  AnomalyItem,
  OpportunityItem,
} from '../types/api';
import { formatCurrency, formatPercent, formatDate } from '../lib/format';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { TableSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { SpendTrendChart } from '../components/charts/SpendTrendChart';
import { CostTopology } from '../components/topology/CostTopology';
import { useInvestigation } from '../lib/InvestigationContext';
import { useAskAtlas } from '../lib/AskAtlasContext';
import {
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  ShieldCheck,
  Info,
  Sliders,
  Sparkles,
  ArrowRight,
  Compass,
} from 'lucide-react';

export const SpendPage: React.FC = () => {
  const { openAskAtlas } = useAskAtlas();
  const { startTrace } = useInvestigation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Read URL query parameters or fallback
  const periodDays = parseInt(searchParams.get('period') || '30', 10);
  const accountId = searchParams.get('account_id') || undefined;
  const serviceName = searchParams.get('service_name') || undefined;
  const focusParam = searchParams.get('focus') || undefined;
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SpendExplorerResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummaryResponse | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunityItem[]>([]);
  const [driverDimension, setDriverDimension] = useState<'SERVICE' | 'ACCOUNT'>('SERVICE');
  const [showExplanation, setShowExplanation] = useState(false);
  const [viewMode, setViewMode] = useState<'DUAL' | 'TOPOLOGY' | 'BREAKDOWN'>('DUAL');

  const fetchSpendData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [resp, analyticsResp, anomResp, oppResp] = await Promise.allSettled([
        api.getSpendExplorer({
          period_days: periodDays,
          account_id: accountId,
          service_name: serviceName,
          page,
          page_size: 15,
        }),
        api.getAnalyticsSummary(periodDays),
        api.getAnomalies().catch(() => ({ items: [], total: 0 })),
        api.getOptimization().catch(() => ({ opportunities: [], total_opportunities: 0 })),
      ]);

      if (resp.status === 'fulfilled') {
        setData(resp.value);
      } else {
        throw resp.reason;
      }

      if (analyticsResp.status === 'fulfilled') {
        setAnalytics(analyticsResp.value);
      }

      if (anomResp.status === 'fulfilled' && (anomResp.value as any)?.items) {
        setAnomalies((anomResp.value as any).items);
      }

      if (oppResp.status === 'fulfilled' && (oppResp.value as any)?.opportunities) {
        setOpportunities((oppResp.value as any).opportunities);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve spend data.');
    } finally {
      setLoading(false);
    }
  }, [periodDays, accountId, serviceName, page]);

  useEffect(() => {
    fetchSpendData();
  }, [fetchSpendData]);

  const setFilter = (key: string, value?: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    next.set('page', '1');
    setSearchParams(next);
  };

  const clearAllFilters = () => {
    setSearchParams({ period: '30', page: '1' });
  };

  const activeDrivers =
    driverDimension === 'SERVICE'
      ? analytics?.drivers.service_drivers || []
      : analytics?.drivers.account_drivers || [];

  return (
    <div className="space-y-6 select-none font-mono">
      {/* ── HEADER & CONTROLS ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E2638] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-sky-400"></span>
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">
              SPEND EXPLORER
            </h1>
          </div>
          <p className="text-xs text-atlas-muted mt-0.5">
            Hierarchical financial exploration by technology estate, cloud service, account, and resource
          </p>
        </div>

        {/* Filter Controls Bar */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Period Toggle */}
          <div className="bg-[#0F141C] p-1 rounded-md border border-[#1E2638] flex items-center gap-1 text-xs">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                type="button"
                onClick={() => setFilter('period', days.toString())}
                className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors ${
                  periodDays === days
                    ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30'
                    : 'text-atlas-muted hover:text-atlas-text'
                }`}
              >
                {days}D
              </button>
            ))}
          </div>

          {/* Service Filter */}
          {data?.service_breakdown && (
            <select
              value={serviceName || ''}
              onChange={(e) => setFilter('service_name', e.target.value || undefined)}
              className="bg-[#0F141C] border border-[#1E2638] rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono cursor-pointer"
            >
              <option value="">All Cloud Services</option>
              {data.service_breakdown.map((s) => (
                <option key={s.service_name} value={s.service_name}>
                  {s.service_name}
                </option>
              ))}
            </select>
          )}

          {/* Account Filter */}
          {data?.account_breakdown && (
            <select
              value={accountId || ''}
              onChange={(e) => setFilter('account_id', e.target.value || undefined)}
              className="bg-[#0F141C] border border-[#1E2638] rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono cursor-pointer"
            >
              <option value="">All Accounts</option>
              {data.account_breakdown.map((a) => (
                <option key={a.account_id} value={a.account_id}>
                  {a.account_name}
                </option>
              ))}
            </select>
          )}

          {(accountId || serviceName) && (
            <button
              type="button"
              onClick={clearAllFilters}
              className="px-2.5 py-1.5 rounded text-xs font-mono text-slate-400 hover:text-slate-200 bg-[#141B27] border border-[#1E2638] transition-colors"
            >
              Reset Filters
            </button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              openAskAtlas({
                scopeType: serviceName ? 'SERVICE' : 'DASHBOARD',
                scopeLabel: serviceName || `Spend Explorer (${periodDays}D)`,
                initialQuestion: `Explain the key cost drivers, concentration risk, and spend variance over the last ${periodDays} days.`,
              })
            }
            className="flex items-center gap-1.5 text-xs text-sky-400 border-sky-500/40 hover:bg-sky-500/10 ml-auto md:ml-0"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas</span>
          </Button>
        </div>
      </div>

      {/* ── CANONICAL HIERARCHY BREADCRUMB & VIEW MODE BAR ────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs bg-[#0B0F17] border border-[#1E2638] rounded-lg px-4 py-2.5 text-slate-400">
        <nav aria-label="Hierarchy Breadcrumb" className="flex items-center gap-1.5 overflow-x-auto py-0.5">
          <span className="text-atlas-muted text-[10px] uppercase font-bold tracking-wider mr-1 shrink-0 flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-sky-400" />
            Hierarchy:
          </span>
          <button
            type="button"
            onClick={clearAllFilters}
            className="hover:text-sky-400 transition-colors uppercase font-semibold shrink-0"
          >
            Technology
          </button>
          <span>/</span>
          <span className="text-slate-300 font-semibold shrink-0">AWS</span>
          {serviceName && (
            <>
              <span>/</span>
              <button
                type="button"
                onClick={() => setFilter('service_name', serviceName)}
                className="text-sky-400 font-bold hover:underline uppercase shrink-0"
              >
                {serviceName.replace('Amazon', '')}
              </button>
            </>
          )}
          {accountId && (
            <>
              <span>/</span>
              <span className="text-amber-400 font-semibold uppercase shrink-0">
                {data?.account_breakdown?.find((a) => a.account_id === accountId)?.account_name || accountId}
              </span>
            </>
          )}
        </nav>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 bg-[#141B27] p-0.5 rounded border border-[#1E2638] text-[10px] shrink-0 self-start sm:self-auto">
          {(['DUAL', 'TOPOLOGY', 'BREAKDOWN'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setViewMode(mode)}
              className={`px-2.5 py-1 rounded font-mono transition-colors ${
                viewMode === mode
                  ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {mode} VIEW
            </button>
          ))}
        </div>
      </div>

      {loading && !data && <TableSkeleton cols={6} rows={10} />}

      {error && (
        <div className="py-8">
          <ErrorState
            title="Failed to load spend explorer"
            message={error}
            onRetry={fetchSpendData}
          />
        </div>
      )}

      {data && (
        <>
          {/* ── TOPOLOGY SPATIAL CANVAS (Milestone 3 Core) ─────────────────── */}
          {(viewMode === 'DUAL' || viewMode === 'TOPOLOGY') && (
            <div className="space-y-2">
              <CostTopology
                services={data.service_breakdown}
                accounts={data.account_breakdown}
                resources={data.resource_items}
                anomalies={anomalies}
                opportunities={opportunities}
                initialFocusId={
                  serviceName ? `service:${serviceName}` : focusParam || undefined
                }
                onSelectNode={(node) => {
                  if (node.type === 'service') {
                    setFilter('service_name', node.metadata?.fullName || node.label);
                  } else if (node.type === 'workload') {
                    setFilter('account_id', node.metadata?.accountId);
                  }
                }}
              />
            </div>
          )}

          {/* ── HIERARCHICAL BREAKDOWN & TELEMETRY DETAILS ─────────────────── */}
          {(viewMode === 'DUAL' || viewMode === 'BREAKDOWN') && (
            <div className="space-y-6">
              {/* Top Period Metric Strip */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <Card className="p-4 border-[#1E2638] bg-[#0F141C]">
                  <span className="text-xs text-atlas-muted font-medium block mb-1">
                    {periodDays}-Day Period Spend
                  </span>
                  <div className="text-2xl font-bold font-mono text-slate-100">
                    {formatCurrency(data.total_spend, data.currency)}
                  </div>
                  <span className="text-[11px] font-mono text-atlas-muted mt-1 block">
                    {formatDate(data.start_date, 'medium')} – {formatDate(data.end_date, 'medium')}
                  </span>
                </Card>

                <Card className="p-4 border-[#1E2638] bg-[#0F141C]">
                  <span className="text-xs text-atlas-muted font-medium block mb-1">
                    Period Delta
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold font-mono text-amber-400">
                      {data.period_change_pct !== null
                        ? `▲ +${formatPercent(data.period_change_pct)}`
                        : '—'}
                    </span>
                    {data.period_change_pct !== null && (
                      <span className="text-xs text-atlas-muted font-mono">
                        vs prev {periodDays}d
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-atlas-muted mt-1 block">
                    Prior: {formatCurrency(data.previous_period_spend, data.currency)}
                  </span>
                </Card>

                <Card className="p-4 border-[#1E2638] bg-[#0F141C]">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-atlas-muted font-medium">Trend & Regime</span>
                    {analytics?.trends.current_regime && (
                      <Badge
                        variant={
                          analytics.trends.current_regime === 'SPIKE'
                            ? 'critical'
                            : analytics.trends.current_regime === 'ELEVATED'
                            ? 'warning'
                            : analytics.trends.current_regime === 'RECOVERY'
                            ? 'info'
                            : 'success'
                        }
                      >
                        {analytics.trends.current_regime}
                      </Badge>
                    )}
                  </div>
                  <div className="text-xl font-bold font-mono text-slate-100 flex items-center gap-1.5">
                    {analytics?.trends.trend_direction === 'INCREASING' ? (
                      <TrendingUp className="w-5 h-5 text-rose-400" />
                    ) : analytics?.trends.trend_direction === 'DECREASING' ? (
                      <TrendingDown className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <Activity className="w-5 h-5 text-sky-400" />
                    )}
                    {analytics?.trends.trend_direction || 'STABLE'}
                  </div>
                  <span className="text-[11px] font-mono text-atlas-muted mt-1 block">
                    CV: {analytics?.trends.coefficient_of_variation ?? '0.00'} (Volatility Index)
                  </span>
                </Card>

                <Card className="p-4 border-[#1E2638] bg-[#0F141C]">
                  <span className="text-xs text-atlas-muted font-medium block mb-1">
                    Concentration (HHI)
                  </span>
                  <div className="text-2xl font-bold font-mono text-slate-100">
                    {analytics?.concentration.spend_concentration_index ?? '—'}
                  </div>
                  <span
                    className="text-[11px] font-mono text-atlas-muted mt-1 block truncate"
                    title={analytics?.concentration.hhi_interpretation}
                  >
                    Top 1: {analytics?.concentration.top_1_service_share_pct ?? '0'}% | Top 3: {analytics?.concentration.top_3_service_share_pct ?? '0'}%
                  </span>
                </Card>
              </div>

              {/* Phase 6 Cost Drivers & Attribution Panel with TRACE Actions */}
              {analytics && (
                <Card className="p-5 border-[#1E2638] bg-[#0F141C]">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1E2638] pb-4 mb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-sky-400" />
                        <h3 className="text-sm font-semibold text-slate-100">
                          Cost Driver Attribution (Why Did Spend Change?)
                        </h3>
                        {analytics.drivers.reconciled && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-500/30 font-bold flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3" />
                            Reconciled
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-atlas-muted mt-0.5">
                        Decomposes period-over-period net change across dimensions with distinct absolute and net contribution metrics
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="bg-[#141B27] p-0.5 rounded border border-[#1E2638] flex text-xs">
                        <button
                          type="button"
                          onClick={() => setDriverDimension('SERVICE')}
                          className={`px-3 py-1 rounded font-mono ${
                            driverDimension === 'SERVICE'
                              ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30'
                              : 'text-atlas-muted hover:text-atlas-text'
                          }`}
                        >
                          By Service
                        </button>
                        <button
                          type="button"
                          onClick={() => setDriverDimension('ACCOUNT')}
                          className={`px-3 py-1 rounded font-mono ${
                            driverDimension === 'ACCOUNT'
                              ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30'
                              : 'text-atlas-muted hover:text-atlas-text'
                          }`}
                        >
                          By Account
                        </button>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowExplanation(!showExplanation)}
                        className="text-xs flex items-center gap-1 text-slate-400 hover:text-slate-200"
                      >
                        <Info className="w-3.5 h-3.5" />
                        {showExplanation ? 'Hide Lineage' : 'Lineage'}
                      </Button>
                    </div>
                  </div>

                  {/* Provenance Box if toggled */}
                  {showExplanation && (
                    <div className="mb-4 p-3 bg-[#080B10] border border-[#1E2638] rounded-md text-xs font-mono text-atlas-muted space-y-1">
                      <div className="font-semibold text-slate-200 flex items-center gap-1">
                        <Layers className="w-3.5 h-3.5 text-sky-400" />
                        Analytical Provenance & Explanations ({analytics.drivers.explanation.version})
                      </div>
                      <div>Method: {analytics.drivers.explanation.method}</div>
                      <div>
                        Total Delta: ₹{analytics.drivers.net_change} ({analytics.drivers.net_change_pct}%)
                      </div>
                      <div>Evidence: {analytics.drivers.explanation.evidence.join('; ')}</div>
                    </div>
                  )}

                  {/* Drivers Grid with Prominent TRACE in Topology Actions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {activeDrivers.slice(0, 6).map((d) => {
                      const isUp = Number(d.cost_delta) > 0;
                      return (
                        <div
                          key={d.identifier}
                          className="p-3.5 bg-[#141B27]/40 hover:bg-[#141B27]/80 border border-[#1E2638] rounded-md space-y-2.5 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-400 font-mono">
                                #{d.rank}
                              </span>
                              <span className="text-xs font-semibold text-slate-200 truncate max-w-[140px]">
                                {d.name}
                              </span>
                            </div>
                            <span
                              className={`text-[10px] px-1.5 py-0.2 rounded border font-semibold ${
                                isUp
                                  ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
                                  : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                              }`}
                            >
                              {d.direction}
                            </span>
                          </div>

                          <div className="flex items-baseline justify-between font-mono">
                            <span className="text-sm font-bold text-slate-200">
                              {formatCurrency(d.current_period_cost, data.currency)}
                            </span>
                            <span
                              className={`text-xs font-semibold ${
                                isUp ? 'text-rose-400' : 'text-emerald-400'
                              }`}
                            >
                              {isUp ? '+' : ''}
                              {formatCurrency(d.cost_delta, data.currency)}
                            </span>
                          </div>

                          <div className="pt-1.5 border-t border-[#1E2638] grid grid-cols-2 gap-2 text-[11px] font-mono text-atlas-muted">
                            <div>
                              <span className="block text-[10px] uppercase text-atlas-muted">
                                Abs Contribution
                              </span>
                              <span className="font-semibold text-slate-200">
                                {d.absolute_contribution_pct}%
                              </span>
                            </div>
                            <div>
                              <span className="block text-[10px] uppercase text-atlas-muted">
                                Net Impact
                              </span>
                              <span className="font-semibold text-slate-200">
                                {d.net_change_contribution_pct !== null
                                  ? `${d.net_change_contribution_pct}%`
                                  : '—'}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]">
                            <span className="text-[10px] text-atlas-muted uppercase">
                              {d.classification}
                            </span>
                            <button
                              type="button"
                              onClick={() =>
                                startTrace(
                                  {
                                    entityId: d.name,
                                    entityType: 'SERVICE',
                                    entityName: d.name,
                                    origin: `Spend Explorer Driver Attribution · ${d.direction}`,
                                    costDelta: d.cost_delta,
                                  },
                                  `/spend?service_name=${encodeURIComponent(d.name)}&trace=true`
                                )
                              }
                              className="px-2 py-0.5 rounded bg-sky-950/40 border border-sky-500/40 hover:bg-sky-900/50 text-sky-400 text-[10px] font-bold flex items-center gap-1 transition-colors"
                            >
                              <span>TRACE</span>
                              <ArrowRight className="w-2.5 h-2.5" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Spend Trend Chart for Selected Filter Context */}
              <Card className="p-5 border-[#1E2638] bg-[#0F141C]">
                <div className="flex items-center justify-between mb-4 border-b border-[#1E2638] pb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
                      Expenditure Trajectory ({periodDays} Days)
                    </h3>
                    <p className="text-xs text-atlas-muted">
                      Reflects currently selected account and service filter context with rolling baselines
                    </p>
                  </div>
                </div>
                <SpendTrendChart points={data.trend} currency={data.currency} height={240} />
              </Card>

              {/* Resource-Level Cost Allocation Table with TRACE Action */}
              <Card className="border-[#1E2638] bg-[#0F141C] overflow-hidden">
                <div className="p-4 border-b border-[#1E2638] flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
                      Resource Spend Allocations
                    </h3>
                    <p className="text-xs text-atlas-muted">
                      Individual resource cost accounting with direct causal trace handoff
                    </p>
                  </div>
                  <div className="text-xs font-mono text-atlas-muted">
                    Showing Page {data.page} of {data.total_pages} ({data.total_resources} resources)
                  </div>
                </div>

                {data.resource_items.length === 0 ? (
                  <div className="py-12">
                    <EmptyState
                      title="No resources found"
                      message="Try adjusting your filters or time window."
                    />
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-[#090D15] border-b border-[#1E2638] text-atlas-muted uppercase text-[10px]">
                        <tr>
                          <th className="py-2.5 px-4 font-semibold">Resource</th>
                          <th className="py-2.5 px-4 font-semibold">Service</th>
                          <th className="py-2.5 px-4 font-semibold">Account</th>
                          <th className="py-2.5 px-4 font-semibold">Region</th>
                          <th className="py-2.5 px-4 font-semibold text-right">Spend</th>
                          <th className="py-2.5 px-4 font-semibold text-right">Share</th>
                          <th className="py-2.5 px-4 font-semibold text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1E2638]/50 text-slate-200">
                        {data.resource_items.map((r) => (
                          <tr
                            key={r.resource_id}
                            className="hover:bg-[#141B27]/50 transition-colors"
                          >
                            <td className="py-2.5 px-4">
                              <Link
                                to={`/resources/${r.resource_id}`}
                                className="font-semibold text-slate-200 hover:text-sky-400 transition-colors block"
                              >
                                {r.resource_name}
                              </Link>
                              <div className="text-[10px] text-atlas-muted truncate max-w-[200px]">
                                {r.native_id}
                              </div>
                            </td>
                            <td className="py-2.5 px-4 text-slate-400">{r.service_name}</td>
                            <td className="py-2.5 px-4 text-slate-400">{r.account_name}</td>
                            <td className="py-2.5 px-4 text-atlas-muted">{r.region}</td>
                            <td className="py-2.5 px-4 text-right font-bold">
                              {formatCurrency(r.spend, data.currency)}
                            </td>
                            <td className="py-2.5 px-4 text-right text-atlas-muted">
                              {formatPercent(r.percentage_of_total)}
                            </td>
                            <td className="py-2.5 px-4 text-center">
                              <button
                                type="button"
                                onClick={() =>
                                  startTrace(
                                    {
                                      entityId: r.resource_id,
                                      entityNativeId: r.native_id,
                                      entityType: 'RESOURCE',
                                      entityName: r.resource_name,
                                      origin: `Spend Explorer Resource · ${r.service_name}`,
                                      costDelta: r.spend,
                                    },
                                    `/spend?service_name=${encodeURIComponent(r.service_name)}&trace=true&entityId=${encodeURIComponent(r.resource_id)}`
                                  )
                                }
                                className="px-2 py-0.5 rounded bg-sky-950/40 border border-sky-500/40 hover:bg-sky-900/50 text-sky-400 font-mono text-[10px] font-bold inline-flex items-center gap-1 transition-colors"
                                title={`Trace ${r.resource_name}`}
                              >
                                <span>TRACE</span>
                                <ArrowRight className="w-2.5 h-2.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Pagination Controls */}
                {data.total_pages > 1 && (
                  <div className="p-3 border-t border-[#1E2638] flex items-center justify-between text-xs">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={data.page <= 1}
                      onClick={() => setFilter('page', (data.page - 1).toString())}
                      className="flex items-center gap-1 text-slate-400"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      Previous
                    </Button>
                    <span className="text-atlas-muted font-mono text-[11px]">
                      Page {data.page} of {data.total_pages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={data.page >= data.total_pages}
                      onClick={() => setFilter('page', (data.page + 1).toString())}
                      className="flex items-center gap-1 text-slate-400"
                    >
                      Next
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                )}
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
};

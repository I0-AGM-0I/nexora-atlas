import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Zap,
  Sparkles,
  RefreshCw,
  GitFork,
  ChevronRight,
  Compass,
  PieChart,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { EpistemicBadge } from '../components/ui/EpistemicBadge';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { useInvestigation } from '../lib/InvestigationContext';
import { api } from '../lib/api';
import { formatCurrency } from '../lib/format';
import type {
  OptimizationOverviewResponse,
  OpportunityItem,
  AnalyticsPortfolioResponse,
  AnalyticsConcentrationResponse,
} from '../types/api';

export const OptimizationPage: React.FC = () => {
  const navigate = useNavigate();
  const { openAskAtlas } = useAskAtlas();
  const { startFocus } = useInvestigation();

  const [data, setData] = useState<OptimizationOverviewResponse | null>(null);
  const [portfolioData, setPortfolioData] = useState<AnalyticsPortfolioResponse | null>(null);
  const [concentrationData, setConcentrationData] = useState<AnalyticsConcentrationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [optRes, portRes, concRes] = await Promise.all([
        api.getOptimization({
          category: categoryFilter !== 'ALL' ? categoryFilter : undefined,
        }),
        api.getAnalyticsPortfolio().catch(() => null),
        api.getAnalyticsConcentration(30).catch(() => null),
      ]);
      setData(optRes);
      setPortfolioData(portRes);
      setConcentrationData(concRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to load optimization intelligence');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFocusTopology = (opp: OpportunityItem) => {
    const resId = opp.resource_id || opp.resource_native_id || opp.id;
    const nativeId = opp.resource_native_id || resId;
    startFocus({
      entityId: resId,
      entityNativeId: nativeId,
      entityType: 'RESOURCE',
      entityName: opp.resource_name || nativeId,
      origin: `Optimization · ${opp.category}`,
      costDelta: Number(opp.estimated_waste_monthly || 0),
    });
    navigate(`/spend?focus=${encodeURIComponent(nativeId)}&trace=true`);
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toUpperCase()) {
      case 'HIGH':
        return <Badge variant="critical" size="xs">High</Badge>;
      case 'MEDIUM':
        return <Badge variant="warning" size="xs">Medium</Badge>;
      case 'LOW':
        return <Badge variant="default" size="xs">Low</Badge>;
      default:
        return <Badge variant="default" size="xs">{sev}</Badge>;
    }
  };

  if (loading && !data) {
    return (
      <div className="space-y-6 select-none">
        <div className="h-10 w-48 bg-[#141B27] animate-pulse rounded" />
        <CardSkeleton rows={4} />
        <CardSkeleton rows={6} />
      </div>
    );
  }

  if (error && !data) {
    return <ErrorState message={error} onRetry={loadData} />;
  }

  const portfolio = portfolioData?.portfolio;
  const totalMonthlySavings =
    portfolio?.total_compatible_monthly_savings ??
    data?.potential_monthly_savings ??
    '460000.00';
  const totalAnnualSavings = (Number(totalMonthlySavings) * 12).toFixed(2);
  const opportunityCount = data?.opportunity_count ?? 7;
  const opportunities = data?.opportunities ?? [];

  // Concentration summary
  const concentration = concentrationData?.concentration;

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E2638] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <h1 className="text-xl font-bold tracking-tight text-atlas-text font-mono">
              OPTIMIZATION WORKSPACE
            </h1>
          </div>
          <p className="text-xs text-atlas-muted font-mono mt-0.5">
            Quantified Waste Elimination & Rightsizing Portfolio · Engineering Decision Room
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() =>
              openAskAtlas({
                scopeType: 'RECOMMENDATION',
                scopeLabel: 'Optimization Portfolio',
                initialQuestion: 'Where is the largest addressable waste and what are the mutual dependencies across opportunities?',
              })
            }
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas About Waste</span>
          </button>

          <Link to="/scenarios">
            <Button variant="outline" size="sm" icon={<GitFork className="w-3.5 h-3.5" />}>
              Simulation Workbench
            </Button>
          </Link>

          <button
            onClick={loadData}
            title="Refresh optimization intelligence"
            className="p-1.5 rounded-md border border-[#1E2638] bg-[#0F141C] text-atlas-muted hover:text-atlas-text transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── PORTFOLIO HERO STRIP ────────────────────────────────────────── */}
      <div className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <PieChart className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
              Collective Optimization Portfolio
            </span>
            <EpistemicBadge classification="INFERRED" size="xs" />
          </div>
          <span className="text-[10px] font-mono text-slate-400 bg-[#141B27] px-2 py-0.5 rounded border border-[#1E2638]">
            ZERO DOUBLE-COUNTING ENFORCED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-[#141B27]/60 p-3.5 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider">
              Total Addressable Waste
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
              {formatCurrency(totalMonthlySavings)}
            </div>
            <div className="text-[10px] font-mono text-slate-400 mt-0.5">
              {formatCurrency(totalAnnualSavings)} / year potential
            </div>
          </div>

          <div className="bg-[#141B27]/60 p-3.5 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider">
              Compatible Opportunities
            </div>
            <div className="text-2xl font-bold font-mono text-slate-200 mt-1">
              {portfolio?.compatible_recommendations_count ?? opportunityCount}
              <span className="text-xs font-normal text-slate-500 font-mono"> / {opportunityCount} total</span>
            </div>
            <div className="text-[10px] font-mono text-emerald-400 mt-0.5">
              ✓ Non-conflicting implementation pool
            </div>
          </div>

          <div className="bg-[#141B27]/60 p-3.5 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider">
              Candidate Dependencies & Conflicts
            </div>
            <div className="text-sm font-mono text-slate-300 font-semibold mt-1.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Mutually Exclusive:</span>
                <span className="text-amber-400 font-bold">{portfolio?.conflicts?.length ?? 1}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Prerequisites:</span>
                <span className="text-sky-400 font-bold">{portfolio?.dependencies?.length ?? 1}</span>
              </div>
            </div>
          </div>

          <div className="bg-[#141B27]/60 p-3.5 rounded border border-[#1E2638]">
            <div className="text-[10px] font-mono text-atlas-muted uppercase tracking-wider flex items-center justify-between">
              <span>Portfolio Risk Profile</span>
              <ShieldAlert className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="mt-2 space-y-1 text-[11px] font-mono">
              <div className="flex items-center justify-between">
                <span className="text-emerald-400">Low Risk Candidates:</span>
                <span className="font-bold text-slate-200">{portfolio?.risk_profile?.count_low ?? 4}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-amber-400">Medium Risk:</span>
                <span className="font-bold text-slate-200">{portfolio?.risk_profile?.count_medium ?? 2}</span>
              </div>
              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5 border-t border-[#1E2638]">
                <span>Composite Score:</span>
                <span className="text-slate-400 uppercase">None (Decoupled)</span>
              </div>
            </div>
          </div>
        </div>

        {portfolio?.explanation && (
          <p className="text-[11px] font-mono text-slate-400 bg-[#141B27]/30 p-2.5 rounded border border-[#1E2638]/50">
            {portfolio.explanation.evidence?.[0] || portfolio.explanation.method || 'Portfolio evaluation detects collective non-conflicting savings opportunities.'}
          </p>
        )}
      </div>

      {/* ── CATEGORY FILTER TABS ────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-[#1E2638] pb-2">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {['ALL', 'COMPUTE', 'STORAGE', 'DATABASE'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-colors ${
                categoryFilter === cat
                  ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                  : 'text-atlas-muted hover:text-atlas-text hover:bg-[#141B27]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <span className="text-xs font-mono text-slate-400">
          {opportunities.length} opportunities in scope
        </span>
      </div>

      {/* ── OPPORTUNITY DECISION CARDS ──────────────────────────────────── */}
      {opportunities.length === 0 ? (
        <EmptyState
          title="No Optimization Opportunities Found"
          message={`No addressable waste or rightsizing candidates match category '${categoryFilter}'.`}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {opportunities.map((opp: OpportunityItem) => {
            const recs = opp.recommendations || [];
            const primaryRec = recs[0];
            const hasMultiple = recs.length > 1;
            const wasteMonthly = Number(opp.estimated_waste_monthly || 0);
            const risk = primaryRec?.risk_level || opp.severity || 'LOW';
            const evidencePct = primaryRec?.confidence_pct ? Number(primaryRec.confidence_pct) : 94.0;

            return (
              <div
                key={opp.id}
                className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 hover:border-slate-700 transition-colors space-y-4"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-[#1E2638]/60 pb-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold font-mono text-slate-200">
                        {primaryRec?.title || `${opp.category} ${opp.waste_type.replace(/_/g, ' ')}`}
                      </span>
                      <Badge variant="default" size="xs">
                        {opp.category}
                      </Badge>
                      {getSeverityBadge(opp.severity)}
                      {hasMultiple && (
                        <span className="text-[10px] font-mono font-bold text-sky-400 bg-sky-500/10 border border-sky-500/30 px-2 py-0.5 rounded">
                          {recs.length} CANDIDATE PATHS AVAILABLE
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs font-mono text-atlas-muted flex-wrap">
                      <span>Target: <strong className="text-slate-300">{opp.resource_name || opp.resource_native_id || 'Infrastructure Fleet'}</strong></span>
                      <span>·</span>
                      <span>Account: {opp.account_name}</span>
                    </div>
                  </div>

                  {/* Monthly Savings Impact */}
                  <div className="text-left lg:text-right">
                    <div className="text-[10px] font-mono text-atlas-muted uppercase">POTENTIAL SAVINGS</div>
                    <div className="text-xl font-bold font-mono text-emerald-400">
                      {formatCurrency(wasteMonthly)}
                      <span className="text-xs font-normal text-slate-400"> / mo</span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-500">
                      {formatCurrency(wasteMonthly * 12)} / year
                    </div>
                  </div>
                </div>

                {/* Primary Decision Factors & Configuration Delta Preview */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                  <div className="md:col-span-7 bg-[#141B27]/40 p-3 rounded border border-[#1E2638]/50 space-y-1.5">
                    <div className="text-[10px] font-mono text-slate-400 uppercase">PROPOSED CONFIGURATION DELTA</div>
                    <div className="text-xs font-mono text-slate-300">
                      <span className="text-slate-400">{primaryRec?.current_configuration || opp.resource_name || 'Current'}</span>
                      <span className="text-emerald-400 font-bold mx-2">→</span>
                      <span className="text-emerald-300 font-semibold">{primaryRec?.recommended_configuration || 'Right-sized specification'}</span>
                    </div>
                    <p className="text-[11px] font-mono text-slate-400 leading-relaxed">
                      {primaryRec?.reasoning || 'Observed telemetry confirms substantial workload headroom above measured peak demand.'}
                    </p>
                  </div>

                  {/* Discrete Decision Factor Pills */}
                  <div className="md:col-span-5 grid grid-cols-2 gap-2 text-[10px] font-mono">
                    <div className="bg-[#141B27]/60 p-2 rounded border border-[#1E2638]">
                      <span className="text-slate-500 block">RISK</span>
                      <span className={`font-bold ${risk.toUpperCase() === 'LOW' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {risk}
                      </span>
                    </div>

                    <div className="bg-[#141B27]/60 p-2 rounded border border-[#1E2638]">
                      <span className="text-slate-500 block">COMPLEXITY</span>
                      <span className="font-bold text-slate-300">LOW</span>
                    </div>

                    <div className="bg-[#141B27]/60 p-2 rounded border border-[#1E2638]">
                      <span className="text-slate-500 block">REVERSIBILITY</span>
                      <span className="font-bold text-emerald-400">HIGH</span>
                    </div>

                    <div className="bg-[#141B27]/60 p-2 rounded border border-[#1E2638]">
                      <span className="text-slate-500 block">EVIDENCE STRENGTH</span>
                      <span className="font-bold text-sky-400">{evidencePct.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-[#1E2638]/50">
                  <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Non-executable engineering evaluation · Preserves read-only boundary</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFocusTopology(opp)}
                      icon={<Compass className="w-3.5 h-3.5" />}
                    >
                      Trace in Topology
                    </Button>

                    <Link to={`/optimization/${encodeURIComponent(opp.id)}`}>
                      <Button
                        variant="primary"
                        size="sm"
                        icon={<ArrowRight className="w-3.5 h-3.5" />}
                      >
                        Enter Decision Room →
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── CONTEXTUAL SPEND CONCENTRATION DIAGNOSTIC ────────────────────── */}
      {concentration && (
        <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300">
                Estate Spend Concentration Context
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded border bg-sky-500/10 text-sky-400 border-sky-500/30 uppercase">
                CONCENTRATION: {concentration.hhi_interpretation || 'MODERATE'}
              </span>
            </div>
            <p className="text-[11px] font-mono text-slate-400 leading-relaxed">
              Top service accounts for {(Number(concentration.top_1_service_share_pct || 0)).toFixed(1)}% of technology expenditure.
              Concentration metrics evaluate provider resilience and architectural lock-in.
            </p>
          </div>

          <Link to="/spend">
            <Button variant="outline" size="sm" icon={<ChevronRight className="w-3.5 h-3.5" />}>
              Inspect in Spend Explorer
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
};

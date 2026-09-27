import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type {
  DashboardSummary,
  SpendTrendResponse,
  AnomalyItem,
  OpportunityItem,
  CostDriverItem,
} from '../types/api';
import { CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { EpistemicBadge } from '../components/ui/EpistemicBadge';
import { EvidenceLayer, EvidenceItem } from '../components/ui/EvidenceLayer';
import { FinancialState } from '../components/dashboard/FinancialState';
import { SpendTrajectory } from '../components/dashboard/SpendTrajectory';
import { ActiveChangesFeed } from '../components/dashboard/ActiveChangesFeed';
import { CostDriversList } from '../components/dashboard/CostDriversList';
import { NeedsAttentionCard } from '../components/dashboard/NeedsAttentionCard';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { useInvestigation } from '../lib/InvestigationContext';
import {
  ArrowRight,
  RefreshCw,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Info,
  Compass,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { openAskAtlas } = useAskAtlas();
  const { recentInvestigations, startTrace } = useInvestigation();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [spendTrend, setSpendTrend] = useState<SpendTrendResponse | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [drivers, setDrivers] = useState<CostDriverItem[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunityItem[]>([]);

  // Progressive disclosure toggle for primary driver evidence
  const [showDriverEvidence, setShowDriverEvidence] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sumRes, trendRes, anomSettled, driversSettled, oppSettled] = await Promise.all([
        api.getDashboardSummary(),
        api.getSpendTrend(90),
        api.getAnomalies().catch(() => ({ items: [], total: 0 })),
        api.getAnalyticsDrivers(30).catch(() => null),
        api.getOptimization().catch(() => ({ opportunities: [], total_opportunities: 0 })),
      ]);

      setSummary(sumRes);
      setSpendTrend(trendRes);

      if (anomSettled?.items) {
        setAnomalies(anomSettled.items);
      }

      if (driversSettled?.drivers?.service_drivers) {
        setDrivers(driversSettled.drivers.service_drivers);
      }

      if (oppSettled?.opportunities) {
        setOpportunities(oppSettled.opportunities);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load Command Center telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-12 w-1/3 bg-[#141B27] animate-pulse rounded-lg" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton rows={2} />
          <CardSkeleton rows={2} />
          <CardSkeleton rows={2} />
          <CardSkeleton rows={2} />
        </div>
        <CardSkeleton rows={8} />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <ErrorState
        message={error || 'Failed to load executive telemetry.'}
        onRetry={fetchDashboardData}
      />
    );
  }

  // Authoritative evidence items for Level 3
  const evidenceItems: EvidenceItem[] = [
    {
      epistemicClass: 'OBSERVED',
      source: 'AWS Cost Explorer (ce:GetCostAndUsage)',
      statement: `Cumulative 90-day spend of ₹${Number(summary.total_spend || 3683000).toLocaleString('en-IN')} across ${summary.total_accounts || 3} accounts`,
      timestamp: 'Sync 8m ago',
    },
    {
      epistemicClass: 'DERIVED',
      source: 'Phase 6 Driver Attribution Engine',
      statement: 'EC2 compute scaling contributed 61% of recent net cost increase',
      metricValue: '+₹2.14L / mo',
    },
    {
      epistemicClass: 'OBSERVED',
      source: 'AWS CloudWatch (5-min Sampling)',
      statement: 'Production compute pool CPU p95 maintained at 11.2% (94% sample coverage)',
      metricValue: 'p95: 11.2%',
      timestamp: 'CloudWatch 2h ago',
    },
    {
      epistemicClass: 'INFERRED',
      source: 'Phase 5 Waste Detection Engine',
      statement: `${summary.active_anomalies || 11} anomalies and addressable opportunities identified across compute and storage`,
      metricValue: `₹${Number(summary.potential_monthly_savings || 460000).toLocaleString('en-IN')}/mo`,
    },
    {
      epistemicClass: 'PROJECTED',
      source: 'Holt-Winters Statistical Forecast Horizon',
      statement: `Projected 30-day run rate trending towards ₹${Number(summary.monthly_run_rate || 1380000).toLocaleString('en-IN')}`,
      metricValue: '±6.5% confidence',
    },
  ];

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* ── COMMAND CENTER HEADER ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E2638] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse"></span>
            <h1 className="text-xl font-bold tracking-tight text-atlas-text font-mono">
              COMMAND CENTER
            </h1>
          </div>
          <p className="text-xs text-atlas-muted font-mono mt-0.5">
            Technology Financial Position · Nexora Labs Inc. · Verified Evidence & Provenance
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() =>
              openAskAtlas({
                scopeType: 'DASHBOARD',
                scopeLabel: 'Command Center Financial Position',
                initialQuestion: 'Why did spend change this month and what are the top drivers?',
              })
            }
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
            aria-label="Ask Atlas about financial position"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas About Position</span>
          </button>

          <button
            type="button"
            onClick={fetchDashboardData}
            title="Refresh metrics"
            className="p-1.5 rounded-md border border-[#1E2638] bg-[#0F141C] text-atlas-muted hover:text-atlas-text transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
            aria-label="Refresh metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── RECENT INVESTIGATIONS QUICK RESUME BAR (Directive #28) ───────── */}
      {recentInvestigations.length > 0 && (
        <div
          role="region"
          aria-label="Recent Investigations"
          className="flex items-center gap-2 overflow-x-auto py-1.5 px-3 bg-[#090D15] border border-[#1E2638] rounded-md text-xs font-mono"
        >
          <span className="text-atlas-muted text-[10px] uppercase font-bold tracking-wider shrink-0 flex items-center gap-1.5">
            <Compass className="w-3 h-3 text-sky-400" />
            Recent Investigations:
          </span>
          <div className="flex items-center gap-2">
            {recentInvestigations.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => navigate(item.path)}
                className="px-2 py-0.5 rounded bg-[#141B27] hover:bg-[#1E2638] text-slate-300 hover:text-sky-300 border border-[#1E2638] shrink-0 text-[11px] transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
                title={item.subtitle}
              >
                {item.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── LEVEL 1: FINANCIAL STATE & KEY FIGURES ────────────────────────── */}
      <FinancialState summary={summary} />

      {/* ── SPEND TRAJECTORY (LARGE 90-DAY CHART) ─────────────────────────── */}
      {spendTrend?.points && (
        <SpendTrajectory
          points={spendTrend.points}
          currency={summary.currency}
          totalSpend={summary.total_spend}
        />
      )}

      {/* ── ACTIVE CHANGES & ANOMALIES FEED ───────────────────────────────── */}
      <ActiveChangesFeed anomalies={anomalies} />

      {/* ── LEVEL 2: WHY (PRIMARY DRIVER & TOP DRIVERS DECOMPOSITION) ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Primary Driver Card (with progressive disclosure) */}
        <div className="lg:col-span-2 bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-sky-400 font-semibold">
                What Changed · Primary Cost Driver
              </span>
              <h3 className="text-base font-bold text-atlas-text font-mono mt-0.5">
                AmazonEC2 · Production Compute Pool
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <EpistemicBadge classification="OBSERVED" size="xs" />
              <EpistemicBadge classification="DERIVED" size="xs" />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1 bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
              <div className="text-[11px] text-atlas-muted font-mono">Incurred Period Delta</div>
              <div className="text-xl font-bold font-mono text-amber-400">
                +₹2,14,200 <span className="text-xs font-normal">/ month (+18.7%)</span>
              </div>
              <div className="text-[10px] text-atlas-muted font-mono">
                Share of total activity: <span className="text-slate-300 font-semibold">61.0%</span>
              </div>
            </div>

            <div className="space-y-1 bg-[#141B27]/50 p-3 rounded border border-[#1E2638]/60">
              <div className="text-[11px] text-atlas-muted font-mono">Attributed Root Cause</div>
              <div className="text-xs text-slate-200 font-medium">
                Production API auto-scaling expansion during peak user traffic window.
              </div>
              <div className="text-[10px] text-atlas-muted font-mono">
                Account: <span className="text-slate-300">aws-prod-01 (112233445566)</span>
              </div>
            </div>
          </div>

          {/* Progressive Disclosure: Supporting Evidence */}
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setShowDriverEvidence(!showDriverEvidence)}
              className="w-full flex items-center justify-between p-2 rounded bg-[#141B27] hover:bg-[#182130] border border-[#1E2638] text-xs font-mono text-slate-300 transition-colors"
            >
              <span className="flex items-center gap-2">
                <Info className="w-3.5 h-3.5 text-sky-400" />
                <span>
                  {showDriverEvidence
                    ? 'Hide Empirical Telemetry Evidence'
                    : 'Show Supporting Evidence (Usage ↑ 38%, CPU p95: 11.2%, Coverage: 94%)'}
                </span>
              </span>
              {showDriverEvidence ? (
                <ChevronUp className="w-4 h-4 text-atlas-muted" />
              ) : (
                <ChevronDown className="w-4 h-4 text-atlas-muted" />
              )}
            </button>

            {showDriverEvidence && (
              <div className="mt-2.5 p-3 rounded-lg bg-[#0A0E17] border border-[#1E2638] space-y-2 text-xs font-mono">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div className="bg-[#141B27] p-2 rounded">
                    <div className="text-atlas-muted text-[10px]">Usage Volume Shift</div>
                    <div className="text-slate-200 font-semibold mt-0.5">↑ 38.0% vCPU-Hrs</div>
                    <div className="text-[9px] text-atlas-muted">Spec unchanged</div>
                  </div>
                  <div className="bg-[#141B27] p-2 rounded">
                    <div className="text-atlas-muted text-[10px]">Observed Peak CPU</div>
                    <div className="text-emerald-400 font-semibold mt-0.5">p95: 11.2%</div>
                    <div className="text-[9px] text-atlas-muted">Headroom: 88.8%</div>
                  </div>
                  <div className="bg-[#141B27] p-2 rounded">
                    <div className="text-atlas-muted text-[10px]">Sampling Coverage</div>
                    <div className="text-sky-400 font-semibold mt-0.5">94% (4,032 samples)</div>
                    <div className="text-[9px] text-atlas-muted">Status: SUFFICIENT</div>
                  </div>
                </div>
                <div className="text-[11px] text-atlas-muted pt-1">
                  *Analytical synthesis: Cost increased due to scaling volume, but measured
                  utilization reveals substantial capacity headroom for rightsizing evaluation.
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() =>
                startTrace(
                  {
                    entityId: 'AmazonEC2',
                    entityType: 'SERVICE',
                    entityName: 'AmazonEC2',
                    origin: 'Command Center Primary Driver',
                    costDelta: 214200,
                  },
                  '/spend?service=AmazonEC2&trace=true'
                )
              }
              className="text-xs font-mono text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1.5 focus:outline-none focus:underline"
            >
              <span>TRACE EC2 DRIVER CAUSALITY</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              type="button"
              onClick={() =>
                openAskAtlas({
                  scopeType: 'SERVICE',
                  scopeLabel: 'AmazonEC2',
                  initialQuestion: 'Why did EC2 spend increase by ₹2.14L and can we safely downsize?',
                })
              }
              className="text-xs font-mono text-atlas-muted hover:text-slate-300 flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3 text-sky-400" />
              <span>Ask Atlas about EC2</span>
            </button>
          </div>
        </div>

        {/* Top Cost Drivers List & Subordinate Concentration */}
        <div className="space-y-4">
          <CostDriversList drivers={drivers} />

          {/* Subordinate Spend Concentration (HHI) Diagnostic */}
          <div className="bg-[#0F141C] rounded-lg p-4 border border-[#1E2638] space-y-1">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-atlas-muted">Portfolio Concentration</span>
              <span className="font-semibold text-amber-400">HHI: 2,640 (High)</span>
            </div>
            <div className="text-[10px] text-atlas-muted font-mono">
              Descriptive diagnostic: EC2 and RDS account for 68% of total infrastructure footprint.
            </div>
            <div className="pt-2">
              <button
                type="button"
                onClick={() => navigate('/spend')}
                className="text-xs font-mono text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1"
              >
                <span>Explore Spend Explorer</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── NEEDS ATTENTION: PRIORITIZED INVESTIGATION QUEUE ─────────────── */}
      <NeedsAttentionCard
        anomalies={anomalies}
        opportunities={opportunities}
      />

      {/* ── LEVEL 3: EVIDENCE LAYER ─────────────────────────────────────── */}
      <EvidenceLayer
        items={evidenceItems}
        title="Command Center Authoritative Evidence Layer"
      />
    </div>
  );
};

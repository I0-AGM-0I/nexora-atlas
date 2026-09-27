import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertCircle,
  Sparkles,
  Clock,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { EpistemicBadge } from '../components/ui/EpistemicBadge';
import { EvidenceLayer, EvidenceItem } from '../components/ui/EvidenceLayer';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { api } from '../lib/api';
import { formatCurrency, formatPercent } from '../lib/format';
import { ForecastItem, ForecastResponse } from '../types/api';

export const ForecastPage: React.FC = () => {
  const { openAskAtlas } = useAskAtlas();
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadForecast();
  }, []);

  const loadForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getForecast();
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to load forecast data');
    } finally {
      setLoading(false);
    }
  };

  // Aggregations for KPI cards
  const forecasts = data?.forecasts || [];
  const totalProjected = forecasts.reduce(
    (acc, cur) => acc + (typeof cur.projected_cost === 'number' ? cur.projected_cost : parseFloat(String(cur.projected_cost) || '0')),
    0
  );
  const avgConfidence = forecasts.length > 0
    ? forecasts.reduce((acc, cur) => acc + (typeof cur.confidence_pct === 'number' ? cur.confidence_pct : parseFloat(String(cur.confidence_pct) || '0')), 0) / forecasts.length
    : 0;

  // Epistemic Evidence Layer items for Forecast
  const forecastEvidence: EvidenceItem[] = [
    {
      epistemicClass: 'OBSERVED',
      source: 'AWS Cost Explorer Ingestion (Historical Invoices)',
      statement: 'Historical empirical spend established baseline variance and seasonal weight factors.',
      metricValue: '90-Day Trajectory',
    },
    {
      epistemicClass: 'PROJECTED',
      source: 'Atlas Deterministic Forecasting Model',
      statement: 'Forward projected spend computed across forecast horizons with upper and lower confidence intervals.',
      metricValue: formatCurrency(totalProjected),
      timestamp: `${forecasts.length} Months Horizon`,
    },
    {
      epistemicClass: 'ASSUMED',
      source: 'Forecasting Boundary Contract',
      statement: 'Model assumes active cloud architecture and reserved capacity commitments remain stable without unannounced scaling shifts.',
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Cost Forecast</h1>
            <EpistemicBadge classification="PROJECTED" size="sm" />
            <Badge variant="info">Synthetic Statistical Model</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Forward-looking spend projections, uncertainty confidence bands, and epistemic attribution across forecast horizons.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              openAskAtlas({
                scopeType: 'DASHBOARD',
                scopeLabel: 'Spend Forecast',
                initialQuestion: 'What are the key drivers, assumptions, and confidence bands in the current spend forecast?',
              })
            }
            className="flex items-center gap-1.5 text-xs text-atlas-primary border-atlas-primary/40 hover:bg-atlas-primary/10"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas about this forecast</span>
          </Button>
        </div>
      </div>

      {/* Prominent Demo Mode & Epistemic Disclaimer Banner */}
      <Card className="p-4 bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-xs">
        <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-semibold text-amber-300 flex items-center gap-2">
            <span>Synthetic Demo Forecast Model • Epistemic Class: PROJECTED</span>
          </div>
          <p className="text-amber-200/80 text-[11px] leading-relaxed">
            {data?.disclaimer ||
              'This forecast is generated from synthetic demo fixtures. Projections represent statistical extrapolations under assumed steady-state conditions, not committed financial expenditure. Full statistical time-series algorithms (ARIMA/Prophet) will be enabled in Phase 9.'}
          </p>
        </div>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-atlas-surface/60 border-atlas-border">
          <div className="text-xs text-atlas-muted font-medium">Next Horizon Projected Spend</div>
          <div className="mt-2 text-2xl font-bold font-mono text-atlas-text tracking-tight">
            {loading ? '—' : formatCurrency(forecasts[0]?.projected_cost || 0)}
          </div>
          <div className="text-[11px] text-atlas-muted mt-0.5">
            {forecasts[0]?.forecast_month ? `Month: ${forecasts[0].forecast_month}` : 'Next month'}
          </div>
        </Card>

        <Card className="p-4 bg-atlas-surface/60 border-atlas-border">
          <div className="text-xs text-atlas-muted font-medium">Cumulative Forecast Sum</div>
          <div className="mt-2 text-2xl font-bold font-mono text-atlas-primary tracking-tight">
            {loading ? '—' : formatCurrency(totalProjected)}
          </div>
          <div className="text-[11px] text-atlas-muted mt-0.5">
            Across {forecasts.length} forecast horizons
          </div>
        </Card>

        <Card className="p-4 bg-atlas-surface/60 border-atlas-border">
          <div className="text-xs text-atlas-muted font-medium">Model Confidence</div>
          <div className="mt-2 text-2xl font-bold font-mono text-atlas-success tracking-tight">
            {loading ? '—' : `${avgConfidence.toFixed(1)}%`}
          </div>
          <div className="text-[11px] text-atlas-muted mt-0.5">Mean confidence bound</div>
        </Card>

        <Card className="p-4 bg-atlas-surface/60 border-atlas-border">
          <div className="text-xs text-atlas-muted font-medium">Forecasting Algorithm</div>
          <div className="mt-2 text-sm font-bold font-mono text-atlas-text tracking-tight uppercase">
            {forecasts[0]?.algorithm || 'DEMO_FIXTURE'}
          </div>
          <div className="text-[11px] text-atlas-muted mt-0.5">Deterministic benchmark</div>
        </Card>
      </div>

      {/* Visual Forecast Chart with Historical vs Projected Demarcation */}
      {!loading && forecasts.length > 0 && (
        <Card className="p-5 bg-atlas-surface/50 border-atlas-border space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-atlas-primary" />
              <span className="text-xs font-bold text-atlas-text uppercase tracking-wide">
                Temporal Trajectory: Historical Spend vs Projected Horizons
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-atlas-muted">
              <span className="flex items-center gap-1.5">
                <span className="w-4 h-0.5 bg-emerald-400" />
                <span className="text-emerald-400">Historical Actual (OBSERVED)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-4 h-0.5 border-t-2 border-dashed border-sky-400" />
                <span className="text-sky-400">Projected (PROJECTED)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-sky-400/20 border border-sky-400/40" />
                <span>Confidence Envelope</span>
              </span>
            </div>
          </div>

          {/* Temporal Demarcation Banner */}
          <div className="p-2.5 rounded bg-atlas-elevated/40 border border-atlas-border flex items-center justify-between text-[11px] font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-atlas-text font-semibold">Solid Line: Observed Invoiced Spend</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-300 font-bold bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
              <Clock className="w-3 h-3" />
              <span>TODAY (Temporal Threshold)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sky-400 font-semibold">Dashed Line: Modeled Projections</span>
              <span className="w-2 h-2 rounded-full bg-sky-400" />
            </div>
          </div>

          {/* SVG Forecast Chart with Temporal Threshold */}
          <div className="h-72 w-full relative">
            <svg className="w-full h-full" viewBox="0 0 880 260" preserveAspectRatio="none">
              <defs>
                <linearGradient id="forecastBandGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.04" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              {[40, 90, 140, 190].map((y) => (
                <line
                  key={y}
                  x1="70"
                  y1={y}
                  x2="840"
                  y2={y}
                  stroke="#1E2638"
                  strokeDasharray="4 4"
                />
              ))}

              {(() => {
                // Synthetic historical anchors to display the solid past line
                const historicalMonths = [
                  { label: 'M-2', cost: 1080000 },
                  { label: 'M-1', cost: 1150000 },
                  { label: 'Current', cost: 1220000 },
                ];

                const allCosts = [
                  ...historicalMonths.map((h) => h.cost),
                  ...forecasts.map((f) => Number(f.upper_bound) || 1400000),
                ];
                const maxVal = Math.max(...allCosts) * 1.15;
                const minVal = Math.min(...allCosts) * 0.75;

                const paddingLeft = 80;
                const paddingRight = 40;
                const chartWidth = 880 - paddingLeft - paddingRight;
                const chartHeight = 180;
                const topPadding = 30;

                const totalSteps = historicalMonths.length + forecasts.length - 1;
                const stepWidth = chartWidth / totalSteps;

                // 1. Calculate Historical Points
                const histPoints = historicalMonths.map((h, i) => {
                  const x = paddingLeft + i * stepWidth;
                  const y = topPadding + chartHeight - ((h.cost - minVal) / (maxVal - minVal)) * chartHeight;
                  return { x, y, label: h.label, cost: h.cost };
                });

                // The "Today" boundary point is the last historical point
                const todayPoint = histPoints[histPoints.length - 1];

                // 2. Calculate Forecast Points (starting from Today's point)
                const forecastPoints = forecasts.map((f, i) => {
                  const x = paddingLeft + (historicalMonths.length + i) * stepWidth;
                  const proj = Number(f.projected_cost) || 0;
                  const low = Number(f.lower_bound) || 0;
                  const upp = Number(f.upper_bound) || 0;

                  const yProj = topPadding + chartHeight - ((proj - minVal) / (maxVal - minVal)) * chartHeight;
                  const yLow = topPadding + chartHeight - ((low - minVal) / (maxVal - minVal)) * chartHeight;
                  const yUpp = topPadding + chartHeight - ((upp - minVal) / (maxVal - minVal)) * chartHeight;

                  return { x, yProj, yLow, yUpp, f };
                });

                // Combine Today anchor into projection paths
                const bandPoints = [
                  { x: todayPoint.x, yLow: todayPoint.y, yUpp: todayPoint.y },
                  ...forecastPoints,
                ];

                const upperBand = bandPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.yUpp}`).join(' ');
                const lowerBand = bandPoints.slice().reverse().map((p) => `L ${p.x} ${p.yLow}`).join(' ');
                const bandPath = `${upperBand} ${lowerBand} Z`;

                const histLinePath = histPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
                const projLinePath = [todayPoint, ...forecastPoints].map((p: any, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.yProj !== undefined ? p.yProj : p.y}`).join(' ');

                return (
                  <g>
                    {/* Shaded Confidence Envelope for Future Horizons */}
                    <path d={bandPath} fill="url(#forecastBandGrad)" />

                    {/* Temporal Divider Line (TODAY) */}
                    <line
                      x1={todayPoint.x}
                      y1="20"
                      x2={todayPoint.x}
                      y2="225"
                      stroke="#F59E0B"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                    />
                    <text
                      x={todayPoint.x}
                      y="18"
                      textAnchor="middle"
                      fill="#F59E0B"
                      fontSize="10"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      ▲ TODAY
                    </text>

                    {/* Historical Spend: Solid Emerald Line */}
                    <path
                      d={histLinePath}
                      fill="none"
                      stroke="#10B981"
                      strokeWidth="2.5"
                    />

                    {/* Projected Spend: Dashed Sky Blue Line */}
                    <path
                      d={projLinePath}
                      fill="none"
                      stroke="#38BDF8"
                      strokeWidth="2.5"
                      strokeDasharray="6 4"
                    />

                    {/* Historical Nodes (Solid Filled) */}
                    {histPoints.map((p, i) => (
                      <g key={`hist-${i}`}>
                        <circle cx={p.x} cy={p.y} r="4" fill="#10B981" stroke="#080B10" strokeWidth="2" />
                        <text
                          x={p.x}
                          y="242"
                          textAnchor="middle"
                          fill="#94A3B8"
                          fontSize="10"
                          fontFamily="monospace"
                        >
                          {p.label}
                        </text>
                      </g>
                    ))}

                    {/* Projected Nodes (Hollow with Sky-blue Ring) */}
                    {forecastPoints.map((p, i) => (
                      <g key={`proj-${i}`}>
                        <circle cx={p.x} cy={p.yProj} r="4.5" fill="#0E131F" stroke="#38BDF8" strokeWidth="2.5" />
                        <text
                          x={p.x}
                          y="242"
                          textAnchor="middle"
                          fill="#38BDF8"
                          fontSize="10"
                          fontFamily="monospace"
                          fontWeight="bold"
                        >
                          {p.f.forecast_month}
                        </text>
                      </g>
                    ))}
                  </g>
                );
              })()}
            </svg>
          </div>
        </Card>
      )}

      {/* Authoritative Evidence Layer */}
      <EvidenceLayer items={forecastEvidence} title="Forecasting Model Epistemic Breakdown" />

      {/* Forecast Data Table */}
      {loading ? (
        <div className="space-y-4">
          <CardSkeleton rows={4} />
        </div>
      ) : error ? (
        <ErrorState
          title="Unable to Load Forecasts"
          message={error}
          onRetry={loadForecast}
        />
      ) : forecasts.length === 0 ? (
        <EmptyState
          title="No Forecast Projections"
          message="No forward-looking forecast data generated yet."
        />
      ) : (
        <Card className="bg-atlas-surface/50 border-atlas-border overflow-hidden">
          <div className="p-4 border-b border-atlas-border bg-atlas-surface/80 flex items-center justify-between">
            <span className="text-xs font-bold text-atlas-text uppercase tracking-wide">
              Horizon Breakdown Table ({forecasts.length} Months)
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-atlas-border bg-atlas-surface/40 text-atlas-muted uppercase text-[10px] tracking-wider font-semibold">
                  <th className="py-2.5 px-4">Forecast Month</th>
                  <th className="py-2.5 px-3">Account</th>
                  <th className="py-2.5 px-4 text-right">Projected Spend</th>
                  <th className="py-2.5 px-4 text-right">Confidence Interval (Lower – Upper)</th>
                  <th className="py-2.5 px-3 text-right">Confidence</th>
                  <th className="py-2.5 px-3">Algorithm</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-atlas-border/50 font-mono">
                {forecasts.map((item: ForecastItem) => (
                  <tr key={item.id} className="hover:bg-atlas-elevated/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-atlas-text">
                      {item.forecast_month}
                    </td>
                    <td className="py-3 px-3 font-sans text-atlas-secondary">
                      {item.account_name}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-atlas-primary">
                      {formatCurrency(item.projected_cost)}
                    </td>
                    <td className="py-3 px-4 text-right text-atlas-muted">
                      {formatCurrency(item.lower_bound)} – {formatCurrency(item.upper_bound)}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded bg-atlas-success/10 text-atlas-success text-[11px]">
                        {formatPercent(item.confidence_pct)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-atlas-muted text-[11px] uppercase">
                      {item.algorithm}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

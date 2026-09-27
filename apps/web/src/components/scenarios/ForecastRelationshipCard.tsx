import React, { useEffect, useState } from 'react';
import { TrendingUp, GitFork, ArrowUpRight } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency } from '../../lib/format';
import { api } from '../../lib/api';
import type { ForecastResponse, ScenarioItem } from '../../types/api';

interface ForecastRelationshipCardProps {
  activeScenario: ScenarioItem;
}

export const ForecastRelationshipCard: React.FC<ForecastRelationshipCardProps> = ({
  activeScenario,
}) => {
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    api
      .getForecast()
      .then((res) => {
        if (isMounted) setForecastData(res);
      })
      .catch(() => {
        // Graceful degradation if forecast API is unavailable
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const monthlySavings = Number(activeScenario.monthly_savings || 0);
  const forecasts = forecastData?.forecasts || [];
  const nextMonthForecast = forecasts[0]?.projected_cost
    ? Number(forecasts[0].projected_cost)
    : Number(activeScenario.baseline_monthly_cost);

  const scenarioProjectedNextMonth = Math.max(0, nextMonthForecast - monthlySavings);
  const threeMonthDivergence = monthlySavings * 3;
  const annualDivergence = monthlySavings * 12;

  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-sky-400" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            09 · Forecast Trajectory vs Scenario Intervention
          </h4>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="text-slate-400">ORGANIC FORECAST:</span>
          <EpistemicBadge classification="PROJECTED" size="xs" />
          <span className="text-slate-600">vs</span>
          <span className="text-emerald-400">SCENARIO:</span>
          <EpistemicBadge classification="PROJECTED" size="xs" />
        </div>
      </div>

      {/* Conceptual Distinction Callout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
        <div className="p-3 rounded bg-[#141B27]/60 border border-[#1E2638] space-y-1">
          <div className="flex items-center gap-1.5 text-slate-300 font-bold uppercase text-[11px]">
            <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
            <span>ORGANIC FORECAST (Status Quo)</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            What Atlas projects if current organic provisioning and utilization trends continue without deliberate intervention.
          </p>
          <div className="pt-2 text-base font-bold text-slate-200">
            {loading ? '—' : formatCurrency(nextMonthForecast)}
            <span className="text-xs text-slate-500 font-normal"> / month projected</span>
          </div>
        </div>

        <div className="p-3 rounded bg-emerald-500/5 border border-emerald-500/30 space-y-1">
          <div className="flex items-center gap-1.5 text-emerald-300 font-bold uppercase text-[11px]">
            <GitFork className="w-3.5 h-3.5 text-emerald-400" />
            <span>SCENARIO TRAJECTORY (Intervention)</span>
          </div>
          <p className="text-[11px] text-emerald-300/80 leading-relaxed">
            What Atlas projects if the {activeScenario.changes.length} architectural modifications in "{activeScenario.name}" are implemented.
          </p>
          <div className="pt-2 text-base font-bold text-emerald-400">
            {loading ? '—' : formatCurrency(scenarioProjectedNextMonth)}
            <span className="text-xs text-emerald-400/80 font-normal"> / month target</span>
          </div>
        </div>
      </div>

      {/* Divergence Metrics */}
      <div className="p-3.5 rounded bg-[#141B27]/40 border border-[#1E2638] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <div className="space-y-0.5">
          <div className="text-slate-300 font-semibold flex items-center gap-1.5">
            <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            <span>Projected Estate Divergence (Cumulative Benefit)</span>
          </div>
          <div className="text-[10px] text-slate-500">
            Difference between status-quo forecast and scenario execution
          </div>
        </div>

        <div className="flex items-center gap-4 text-right">
          <div>
            <span className="text-[10px] text-slate-500 block">90-DAY GAP</span>
            <span className="font-bold text-emerald-400">
              {formatCurrency(threeMonthDivergence)}
            </span>
          </div>
          <div className="border-l border-[#1E2638] pl-4">
            <span className="text-[10px] text-slate-500 block">ANNUAL GAP</span>
            <span className="font-bold text-emerald-300">
              {formatCurrency(annualDivergence)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

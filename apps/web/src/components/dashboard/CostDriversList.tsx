import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { CostDriverItem } from '../../types/api';
import { formatCurrency } from '../../lib/format';
import { useInvestigation } from '../../lib/InvestigationContext';
import { ArrowRight, BarChart2 } from 'lucide-react';

interface CostDriversListProps {
  drivers: CostDriverItem[];
  loading?: boolean;
}

export const CostDriversList: React.FC<CostDriversListProps> = ({
  drivers,
  loading = false,
}) => {
  const navigate = useNavigate();
  const { startTrace } = useInvestigation();

  const handleTraceDriver = (driver: CostDriverItem) => {
    startTrace(
      {
        entityId: driver.identifier || driver.name,
        entityType: 'SERVICE',
        entityName: driver.name,
        origin: `Command Center Cost Driver · ${driver.dimension}`,
        costDelta: driver.cost_delta,
        percentageChange: driver.absolute_contribution_pct,
      },
      `/spend?service=${encodeURIComponent(driver.name)}&trace=true`
    );
  };

  return (
    <section
      aria-label="Top Cost Drivers"
      className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 flex flex-col justify-between space-y-4"
    >
      <div>
        <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
              Top Cost Drivers (30D)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-atlas-muted">Period Decomposition</span>
        </div>

        {loading ? (
          <div className="space-y-2.5 mt-3">
            <div className="h-10 bg-[#141B27] animate-pulse rounded" />
            <div className="h-10 bg-[#141B27] animate-pulse rounded" />
            <div className="h-10 bg-[#141B27] animate-pulse rounded" />
          </div>
        ) : drivers.length === 0 ? (
          <div className="py-6 text-center text-xs font-mono text-atlas-muted">
            No driver decomposition available for current window.
          </div>
        ) : (
          <div className="divide-y divide-[#1E2638]/60 text-xs font-mono mt-2">
            {drivers.slice(0, 5).map((driver, idx) => {
              const rankStr = String(driver.rank || idx + 1).padStart(2, '0');
              const deltaNum = Number(driver.cost_delta || 0);
              const isPositive = deltaNum >= 0;

              return (
                <div
                  key={`${driver.dimension}-${driver.identifier || driver.name}-${idx}`}
                  className="py-2.5 flex items-center justify-between gap-3 group"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-slate-400 font-bold text-[11px]">{rankStr}</span>
                    <span className="text-slate-200 font-medium truncate">{driver.name}</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#141B27] border border-[#1E2638] text-slate-400 uppercase">
                      {driver.classification}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <span
                        className={`font-semibold ${
                          isPositive ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {isPositive ? '+' : ''}
                        {formatCurrency(deltaNum, 'INR', false)}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleTraceDriver(driver)}
                      className="px-2 py-1 rounded bg-[#141B27] hover:bg-sky-950/40 border border-[#1E2638] hover:border-sky-500/40 text-slate-400 hover:text-sky-400 text-[10px] font-bold transition-colors flex items-center gap-1 focus:outline-none focus:ring-1 focus:ring-sky-500"
                      title={`Trace spend for ${driver.name}`}
                      aria-label={`Trace ${driver.name}`}
                    >
                      <span>TRACE</span>
                      <ArrowRight className="w-2.5 h-2.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="pt-2 border-t border-[#1E2638]/70">
        <button
          type="button"
          onClick={() => navigate('/spend')}
          className="text-xs font-mono text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 transition-colors"
        >
          <span>EXPLORE FULL SPEND DECOMPOSITION</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </section>
  );
};

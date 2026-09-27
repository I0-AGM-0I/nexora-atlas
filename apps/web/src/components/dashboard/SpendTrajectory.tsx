import React from 'react';
import type { SpendTrendPoint } from '../../types/api';
import { SpendTrendChart } from '../charts/SpendTrendChart';

interface SpendTrajectoryProps {
  points: SpendTrendPoint[];
  currency?: string;
  totalSpend?: string | number;
}

export const SpendTrajectory: React.FC<SpendTrajectoryProps> = ({
  points,
  currency = 'INR',
}) => {
  return (
    <section
      aria-label="Spend Trajectory & 90-Day Moving Baseline"
      className="bg-[#0F141C] border border-[#1E2638] rounded-lg p-5 space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div>
          <h2 className="text-sm font-semibold text-atlas-text font-mono uppercase tracking-wide">
            Monthly Technology Spend Trajectory
          </h2>
          <p className="text-xs text-atlas-muted font-mono mt-0.5">
            90 consecutive days of daily AWS cost records with statistical anomaly event markers
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400 bg-[#141B27] px-2.5 py-1 rounded border border-[#1E2638]">
            90-Day Moving Baseline
          </span>
        </div>
      </div>

      <div className="w-full">
        <SpendTrendChart points={points} currency={currency} height={260} />
      </div>
    </section>
  );
};

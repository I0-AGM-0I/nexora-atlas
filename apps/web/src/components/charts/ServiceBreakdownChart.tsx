import React from 'react';
import { ServiceBreakdownItem } from '../../types/api';
import { formatCurrency, parseNumber } from '../../lib/format';

interface ServiceBreakdownChartProps {
  items: ServiceBreakdownItem[];
  currency?: string;
}

const SERVICE_COLORS: Record<string, string> = {
  AmazonEC2: 'bg-sky-500',
  AmazonRDS: 'bg-emerald-500',
  AmazonEKS: 'bg-indigo-500',
  AmazonS3: 'bg-amber-500',
  AWSCloudTrail: 'bg-rose-500',
  AmazonCloudWatch: 'bg-purple-500',
};

export const ServiceBreakdownChart: React.FC<ServiceBreakdownChartProps> = ({
  items,
  currency = 'INR',
}) => {
  if (!items || items.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-atlas-muted font-mono">
        No service breakdown data
      </div>
    );
  }

  return (
    <div className="space-y-3.5">
      {items.map((srv) => {
        const pct = parseNumber(srv.percentage);
        const barColor = SERVICE_COLORS[srv.service_name] || 'bg-slate-400';

        return (
          <div key={srv.service_name} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${barColor}`} />
                <span className="font-medium text-atlas-text">{srv.service_name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-atlas-text font-medium">
                  {formatCurrency(srv.total_spend, currency)}
                </span>
                <span className="text-[11px] font-mono text-atlas-muted bg-atlas-elevated px-1.5 py-0.5 rounded border border-atlas-border">
                  {pct.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Visual Bar Track */}
            <div className="h-2 w-full bg-atlas-elevated rounded-full overflow-hidden">
              <div
                className={`h-full ${barColor} rounded-full transition-all duration-500 ease-out`}
                style={{ width: `${Math.max(1, Math.min(100, pct))}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

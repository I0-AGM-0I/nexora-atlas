import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AccountBreakdownItem } from '../../types/api';
import { formatCurrency, parseNumber } from '../../lib/format';
import { ShieldCheck, Layers, Terminal, ArrowUpRight } from 'lucide-react';

interface AccountBreakdownCardProps {
  items: AccountBreakdownItem[];
  currency?: string;
}

const ACCOUNT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Production Core': ShieldCheck,
  'Staging Workloads': Layers,
  'Development Sandbox': Terminal,
};

const ACCOUNT_ACCENTS: Record<string, string> = {
  'Production Core': 'text-sky-400 border-sky-500/30 bg-sky-500/10',
  'Staging Workloads': 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10',
  'Development Sandbox': 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10',
};

export const AccountBreakdownCard: React.FC<AccountBreakdownCardProps> = ({
  items,
  currency = 'INR',
}) => {
  const navigate = useNavigate();

  if (!items || items.length === 0) {
    return (
      <div className="h-28 flex items-center justify-center text-xs text-atlas-muted font-mono">
        No account breakdown data
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {items.map((acc) => {
        const Icon = ACCOUNT_ICONS[acc.account_name] || ShieldCheck;
        const accent = ACCOUNT_ACCENTS[acc.account_name] || 'text-slate-400 border-slate-500/30 bg-slate-500/10';
        const pct = parseNumber(acc.percentage);

        return (
          <div
            key={acc.account_id}
            onClick={() => navigate(`/spend?account_id=${acc.account_id}`)}
            className="group p-3.5 rounded-lg border border-atlas-border bg-atlas-surface/60 hover:bg-atlas-elevated hover:border-slate-700 transition-all cursor-pointer flex flex-col justify-between relative overflow-hidden"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={`p-1.5 rounded-md border ${accent}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-atlas-text group-hover:text-atlas-primary transition-colors">
                    {acc.account_name}
                  </h4>
                  <span className="text-[10px] font-mono text-atlas-muted">{acc.provider_account_id}</span>
                </div>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 text-atlas-muted opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>

            <div className="flex items-baseline justify-between pt-2 border-t border-atlas-border/50">
              <span className="text-sm font-bold font-mono text-atlas-text">
                {formatCurrency(acc.total_spend, currency)}
              </span>
              <span className="text-xs font-mono font-medium text-atlas-secondary">
                {pct.toFixed(1)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

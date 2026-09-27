import React from 'react';
import { Link } from 'react-router-dom';
import { Server, Zap, Search } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency } from '../../lib/format';
import type { ScenarioChangeItem } from '../../types/api';

interface ScenarioChangesTableProps {
  changes: ScenarioChangeItem[];
  onInspectProvenance: (change: ScenarioChangeItem) => void;
}

export const ScenarioChangesTable: React.FC<ScenarioChangesTableProps> = ({
  changes,
  onInspectProvenance,
}) => {
  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            03 · Simulated Architectural Alterations ({changes.length})
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="text-slate-400">Current:</span>
          <EpistemicBadge classification="OBSERVED" size="xs" />
          <span className="text-slate-600">→</span>
          <span className="text-slate-400">Proposed:</span>
          <EpistemicBadge classification="PROJECTED" size="xs" />
        </div>
      </div>

      {changes.length === 0 ? (
        <div className="p-8 text-center text-xs text-atlas-muted font-mono bg-[#141B27]/30 rounded border border-[#1E2638]">
          No discrete changes registered in this scenario contract.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#141B27] border-b border-[#1E2638] text-atlas-muted uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Change Type</th>
                <th className="py-2.5 px-3 font-semibold">Current Spec (Observed)</th>
                <th className="py-2.5 px-3 font-semibold">Proposed Spec (Projected)</th>
                <th className="py-2.5 px-3 font-semibold text-right">Monthly Delta</th>
                <th className="py-2.5 px-3 font-semibold text-right">Exploration Handoffs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E2638]/60 text-atlas-text">
              {changes.map((c, idx) => {
                const deltaNum = Number(c.delta_cost || 0);
                const isSavings = deltaNum <= 0;

                return (
                  <tr
                    key={c.id || idx}
                    data-testid={`scenario-change-row-${c.id || idx}`}
                    className="hover:bg-[#141B27]/50 transition-colors"
                  >
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-200">
                        {c.change_type.replace(/_/g, ' ')}
                      </div>
                      {c.resource_id && (
                        <div className="text-[10px] text-slate-500 truncate max-w-[180px]">
                          Target: {c.resource_id}
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-3 text-slate-300">
                      <div className="max-w-[220px] truncate" title={c.current_spec}>
                        {c.current_spec}
                      </div>
                    </td>

                    <td className="py-3 px-3 text-emerald-300">
                      <div className="max-w-[220px] truncate font-medium" title={c.proposed_spec}>
                        {c.proposed_spec}
                      </div>
                    </td>

                    <td className="py-3 px-3 text-right">
                      <span
                        className={`font-bold ${
                          isSavings ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {isSavings ? '-' : '+'}
                        {formatCurrency(Math.abs(deltaNum))}
                      </span>
                      <span className="text-[10px] text-slate-500 block">/ month</span>
                    </td>

                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => onInspectProvenance(c)}
                          title="Inspect epistemic provenance behind this modification"
                          className="px-2 py-1 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-[10px] font-mono transition-colors flex items-center gap-1"
                        >
                          <Search className="w-3 h-3" />
                          <span>Provenance</span>
                        </button>

                        {c.resource_id && (
                          <Link
                            to={`/resources/${encodeURIComponent(c.resource_id)}`}
                            className="px-2 py-1 rounded bg-[#141B27] hover:bg-[#1E2638] text-slate-300 border border-[#1E2638] text-[10px] font-mono transition-colors flex items-center gap-1"
                          >
                            <Server className="w-3 h-3 text-slate-400" />
                            <span>Resource</span>
                          </Link>
                        )}

                        <Link
                          to={`/optimization`}
                          className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono transition-colors flex items-center gap-1"
                        >
                          <Zap className="w-3 h-3" />
                          <span>Decisions</span>
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

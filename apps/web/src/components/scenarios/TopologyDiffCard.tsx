import React from 'react';
import { GitCompare, CheckCircle2, RefreshCw, Trash2, Edit3 } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import type { ScenarioChangeItem } from '../../types/api';

export type DiffCategory = 'MODIFIED' | 'REPLACED' | 'REMOVED' | 'UNCHANGED';

interface TopologyDiffCardProps {
  changes: ScenarioChangeItem[];
  totalEstateNodes?: number;
}

export function classifyChangeType(changeType: string): DiffCategory {
  const ct = changeType.toUpperCase();
  if (ct.includes('TERMINATE') || ct.includes('RELEASE') || ct.includes('DELETE')) {
    return 'REMOVED';
  }
  if (ct.includes('TIER') || ct.includes('MODERNIZE') || ct.includes('MIGRATE')) {
    return 'REPLACED';
  }
  if (ct.includes('RIGHTSIZE') || ct.includes('SCHEDULE') || ct.includes('PAUSE') || ct.includes('SCALE')) {
    return 'MODIFIED';
  }
  return 'MODIFIED';
}

export const TopologyDiffCard: React.FC<TopologyDiffCardProps> = ({
  changes,
  totalEstateNodes = 14,
}) => {
  const counts = {
    MODIFIED: 0,
    REPLACED: 0,
    REMOVED: 0,
    UNCHANGED: 0,
  };

  changes.forEach((c) => {
    const cat = classifyChangeType(c.change_type);
    counts[cat]++;
  });

  const changedCount = changes.length;
  counts.UNCHANGED = Math.max(0, totalEstateNodes - changedCount);

  const pctUnchanged = Math.round((counts.UNCHANGED / totalEstateNodes) * 100);
  const pctModified = Math.round((counts.MODIFIED / totalEstateNodes) * 100);
  const pctReplaced = Math.round((counts.REPLACED / totalEstateNodes) * 100);
  const pctRemoved = Math.round((counts.REMOVED / totalEstateNodes) * 100);

  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-[#1E2638]/70 pb-2">
        <div className="flex items-center gap-2">
          <GitCompare className="w-3.5 h-3.5 text-sky-400" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            07 · Topology Mutation Ledger (Semantic Diff)
          </h4>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono">
          <span className="text-slate-400">Classified as:</span>
          <EpistemicBadge classification="PROJECTED" size="xs" />
        </div>
      </div>

      {/* Semantic Summary Pills */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded bg-[#141B27] border border-[#1E2638] flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-slate-400">
            <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
            <span>UNCHANGED</span>
          </div>
          <span className="font-bold text-slate-300">{counts.UNCHANGED} nodes</span>
        </div>

        <div className="p-2.5 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-sky-300">
            <Edit3 className="w-3.5 h-3.5 text-sky-400" />
            <span>MODIFIED</span>
          </div>
          <span className="font-bold text-sky-200">{counts.MODIFIED} nodes</span>
        </div>

        <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-amber-300">
            <RefreshCw className="w-3.5 h-3.5 text-amber-400" />
            <span>REPLACED</span>
          </div>
          <span className="font-bold text-amber-200">{counts.REPLACED} nodes</span>
        </div>

        <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-rose-300">
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span>REMOVED</span>
          </div>
          <span className="font-bold text-rose-200">{counts.REMOVED} nodes</span>
        </div>
      </div>

      {/* Estate Proportional Diff Bar */}
      <div className="space-y-1 pt-1">
        <div className="flex justify-between text-[10px] font-mono text-slate-400">
          <span>ESTATE INTEGRITY IMPACT</span>
          <span>{pctUnchanged}% Unaffected Infrastructure</span>
        </div>
        <div className="h-2 w-full rounded bg-[#1E2638] flex overflow-hidden">
          <div style={{ width: `${pctUnchanged}%` }} className="bg-slate-600" title={`Unchanged: ${pctUnchanged}%`} />
          <div style={{ width: `${pctModified}%` }} className="bg-sky-400" title={`Modified: ${pctModified}%`} />
          <div style={{ width: `${pctReplaced}%` }} className="bg-amber-400" title={`Replaced: ${pctReplaced}%`} />
          <div style={{ width: `${pctRemoved}%` }} className="bg-rose-400" title={`Removed: ${pctRemoved}%`} />
        </div>
      </div>
    </div>
  );
};

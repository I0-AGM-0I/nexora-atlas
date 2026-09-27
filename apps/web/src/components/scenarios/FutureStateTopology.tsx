import React from 'react';
import { Compass, ArrowRight } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';
import { formatCurrency } from '../../lib/format';
import { TopologyDiffCard, classifyChangeType } from './TopologyDiffCard';
import type { ScenarioChangeItem } from '../../types/api';

interface FutureStateTopologyProps {
  scenarioName: string;
  changes: ScenarioChangeItem[];
  onFocusResource?: (resourceId: string) => void;
}

export const FutureStateTopology: React.FC<FutureStateTopologyProps> = ({
  scenarioName,
  changes,
  onFocusResource,
}) => {
  return (
    <div className="space-y-4">
      {/* 06 · Future-State Topology Header & Container */}
      <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
              06 · Future-State Topology Projection
            </h3>
            <span className="text-slate-600 font-mono">/</span>
            <span className="text-xs font-mono text-slate-400 font-semibold truncate max-w-[200px]">
              {scenarioName}
            </span>
          </div>

          <div className="flex items-center gap-3 text-[10px] font-mono">
            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#1E2638] border border-slate-500 inline-block" />
              <span>Current (Observed)</span>
            </div>
            <div className="flex items-center gap-1.5 text-sky-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-sky-500/10 border border-dashed border-sky-400 inline-block" />
              <span>Projected (Hypothetical)</span>
            </div>
          </div>
        </div>

        <p className="text-xs text-atlas-muted font-mono leading-relaxed">
          Side-by-side comparison of active infrastructure vs hypothetical future state. Observed infrastructure remains in solid dark styling; hypothetical modifications render with dashed cyan borders and explicit <code className="text-sky-300 font-bold">PROJECTED</code> badges so that models never visually masquerade as reality.
        </p>

        {/* Estate Transformation Cards */}
        <div className="space-y-3 pt-1">
          {changes.length === 0 ? (
            <div className="p-8 text-center text-xs text-atlas-muted font-mono bg-[#141B27]/40 rounded border border-[#1E2638]">
              No topology modifications present in this scenario.
            </div>
          ) : (
            changes.map((change, idx) => {
              const diffType = classifyChangeType(change.change_type);
              const delta = Number(change.delta_cost || 0);
              const isRemoved = diffType === 'REMOVED';

              return (
                <div
                  key={change.id || idx}
                  data-testid={`topology-node-pair-${change.id || idx}`}
                  className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center p-3 rounded-lg bg-[#141B27]/30 border border-[#1E2638]"
                >
                  {/* Left Column: Current Estate Node (OBSERVED) */}
                  <div className="md:col-span-5 p-3.5 rounded bg-[#141B27] border border-[#1E2638] space-y-1.5 transition-all hover:border-slate-500">
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span className="text-slate-400 uppercase font-semibold">
                        CURRENT ESTATE NODE
                      </span>
                      <EpistemicBadge classification="OBSERVED" size="xs" />
                    </div>
                    <div className="text-xs font-bold font-mono text-slate-200 truncate">
                      {change.resource_id || 'Infrastructure Target'}
                    </div>
                    <div className="text-xs font-mono text-slate-300">
                      {change.current_spec}
                    </div>
                    <div className="text-[10px] font-mono text-slate-500">
                      Measured 30-day baseline specification
                    </div>
                  </div>

                  {/* Middle Column: Transformation Flow Vector */}
                  <div className="md:col-span-2 flex flex-col items-center justify-center py-2 space-y-1">
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${
                        diffType === 'REMOVED'
                          ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                          : diffType === 'REPLACED'
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                          : 'bg-sky-500/10 text-sky-300 border-sky-500/30'
                      }`}
                    >
                      {diffType}
                    </span>

                    <div className="flex items-center gap-1 text-slate-500">
                      <div className="w-6 h-[1px] bg-slate-600 hidden md:block" />
                      <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                      <div className="w-6 h-[1px] bg-slate-600 hidden md:block" />
                    </div>

                    <div className="text-[10px] font-mono font-bold text-emerald-400">
                      -{formatCurrency(Math.abs(delta))}
                    </div>
                  </div>

                  {/* Right Column: Projected Estate Node (PROJECTED) */}
                  <div
                    className={`md:col-span-5 p-3.5 rounded border-dashed transition-all ${
                      isRemoved
                        ? 'bg-rose-500/5 border border-dashed border-rose-500/40 opacity-75'
                        : 'bg-sky-500/5 border-2 border-dashed border-sky-400/60 shadow-[0_0_12px_rgba(56,189,248,0.06)]'
                    } space-y-1.5`}
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span
                        className={`uppercase font-semibold ${
                          isRemoved ? 'text-rose-400' : 'text-sky-300'
                        }`}
                      >
                        {isRemoved ? 'DECOMMISSIONED' : 'PROJECTED ESTATE NODE'}
                      </span>
                      <EpistemicBadge classification="PROJECTED" size="xs" />
                    </div>

                    <div
                      className={`text-xs font-bold font-mono ${
                        isRemoved ? 'text-slate-400 line-through' : 'text-sky-200'
                      }`}
                    >
                      {change.resource_id || 'Infrastructure Target'}
                    </div>

                    <div
                      className={`text-xs font-mono font-medium ${
                        isRemoved ? 'text-rose-300 line-through' : 'text-emerald-300'
                      }`}
                    >
                      {change.proposed_spec}
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono pt-0.5">
                      <span className={isRemoved ? 'text-rose-400/80' : 'text-emerald-400/80'}>
                        {isRemoved ? 'Resource terminated' : 'Projected target run-rate'}
                      </span>
                      {change.resource_id && onFocusResource && (
                        <button
                          type="button"
                          onClick={() => onFocusResource(change.resource_id!)}
                          className="text-sky-400 hover:text-sky-300 underline underline-offset-2"
                        >
                          Focus in Live Topology →
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 07 · Semantic Diff Breakdown */}
      <TopologyDiffCard changes={changes} />
    </div>
  );
};

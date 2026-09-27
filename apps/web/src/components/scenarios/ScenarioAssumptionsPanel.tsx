import React from 'react';
import { HelpCircle, AlertCircle } from 'lucide-react';
import { EpistemicBadge } from '../ui/EpistemicBadge';

interface ScenarioAssumptionsPanelProps {
  assumptionsJson?: Record<string, any> | null;
}

export const ScenarioAssumptionsPanel: React.FC<ScenarioAssumptionsPanelProps> = ({
  assumptionsJson,
}) => {
  const entries = assumptionsJson ? Object.entries(assumptionsJson) : [];
  const hasAssumptions = entries.length > 0;

  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-sky-400" />
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            04 · Explicit Scenario Assumptions
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="text-slate-400">Epistemic Tier:</span>
          <EpistemicBadge classification="ASSUMED" size="xs" />
        </div>
      </div>

      <p className="text-xs text-atlas-muted font-mono leading-relaxed">
        Scenario assumptions represent operational premises and parameter boundaries required to compute the projected run-rate. These are strictly assumed conditions, not measured telemetry.
      </p>

      {!hasAssumptions ? (
        <div className="p-4 rounded bg-[#141B27]/40 border border-[#1E2638] flex items-center gap-2 text-xs font-mono text-slate-400">
          <AlertCircle className="w-4 h-4 text-slate-500 shrink-0" />
          <span>
            <strong>NOT_CONFIGURED:</strong> No custom parameter assumptions were declared in this scenario contract. Projections operate under standard default baseline constraints.
          </span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {entries.map(([key, val]) => {
            const formattedKey = key.replace(/_/g, ' ').toUpperCase();
            const formattedVal =
              typeof val === 'object' && val !== null
                ? JSON.stringify(val)
                : typeof val === 'boolean'
                ? val ? 'TRUE / ENFORCED' : 'FALSE'
                : String(val);

            return (
              <div
                key={key}
                className="bg-[#141B27]/50 p-3.5 rounded border border-[#1E2638] space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-atlas-muted uppercase truncate max-w-[180px]">
                    {formattedKey}
                  </span>
                  <EpistemicBadge classification="ASSUMED" size="xs" />
                </div>
                <div className="text-xs font-bold font-mono text-slate-200 break-words">
                  {formattedVal}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

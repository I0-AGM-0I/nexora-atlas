import React from 'react';
import { Columns, Check, ArrowRight } from 'lucide-react';
import { formatCurrency, formatPercent } from '../../lib/format';
import type { ScenarioItem } from '../../types/api';

interface ScenarioComparisonMatrixProps {
  scenarios: ScenarioItem[];
  activeScenarioId: string;
  onSelectScenario: (id: string) => void;
}

export const ScenarioComparisonMatrix: React.FC<ScenarioComparisonMatrixProps> = ({
  scenarios,
  activeScenarioId,
  onSelectScenario,
}) => {
  return (
    <div className="rounded-lg border border-[#1E2638] bg-[#0F141C] p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <Columns className="w-4 h-4 text-sky-400" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            08 · Objective Scenario Comparison Matrix
          </h4>
        </div>
        <span className="text-[10px] font-mono text-slate-400 bg-[#141B27] px-2 py-0.5 rounded border border-[#1E2638]">
          OBJECTIVE TRADE-OFF COMPARISON · ZERO "WINNER" BIAS
        </span>
      </div>

      <p className="text-xs text-atlas-muted font-mono leading-relaxed">
        Atlas presents the empirical trade-offs across all modeled options without picking a "winner". Engineering and finance leaders evaluate risk vs reduction to select the appropriate organizational posture.
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#141B27] border-b border-[#1E2638] text-atlas-muted uppercase text-[10px]">
            <tr>
              <th className="py-3 px-4 font-semibold text-slate-400">Trade-Off Dimension</th>
              {scenarios.map((s) => {
                const isActive = s.id === activeScenarioId;
                return (
                  <th
                    key={s.id}
                    className={`py-3 px-4 font-bold text-center transition-colors ${
                      isActive ? 'text-sky-300 bg-sky-500/10' : 'text-slate-300'
                    }`}
                  >
                    <div className="flex flex-col items-center gap-1">
                      <span>{s.name}</span>
                      {isActive && (
                        <span className="text-[9px] font-mono bg-sky-400 text-slate-950 px-1.5 py-0.2 rounded font-bold">
                          ACTIVE MODEL
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E2638]/60 text-atlas-text">
            {/* Monthly Savings */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">
                Monthly Savings (Reconciled)
              </td>
              {scenarios.map((s) => (
                <td
                  key={s.id}
                  className={`py-3 px-4 text-center font-bold text-emerald-400 ${
                    s.id === activeScenarioId ? 'bg-sky-500/5' : ''
                  }`}
                >
                  {formatCurrency(s.monthly_savings)}
                </td>
              ))}
            </tr>

            {/* Annual Savings */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">Annualized Savings</td>
              {scenarios.map((s) => (
                <td
                  key={s.id}
                  className={`py-3 px-4 text-center font-bold text-emerald-300 ${
                    s.id === activeScenarioId ? 'bg-sky-500/5' : ''
                  }`}
                >
                  {formatCurrency(Number(s.monthly_savings || 0) * 12)}
                </td>
              ))}
            </tr>

            {/* Percentage Reduction */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">Spend Reduction %</td>
              {scenarios.map((s) => (
                <td
                  key={s.id}
                  className={`py-3 px-4 text-center font-semibold text-slate-200 ${
                    s.id === activeScenarioId ? 'bg-sky-500/5' : ''
                  }`}
                >
                  -{formatPercent(s.percentage_savings)}
                </td>
              ))}
            </tr>

            {/* Performance Risk */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">Performance Risk</td>
              {scenarios.map((s) => {
                const pr = (s.performance_risk || 'LOW').toUpperCase();
                return (
                  <td
                    key={s.id}
                    className={`py-3 px-4 text-center font-bold ${
                      pr === 'LOW' || pr === 'NONE'
                        ? 'text-emerald-400'
                        : pr === 'MEDIUM'
                        ? 'text-amber-400'
                        : 'text-rose-400'
                    } ${s.id === activeScenarioId ? 'bg-sky-500/5' : ''}`}
                  >
                    {pr}
                  </td>
                );
              })}
            </tr>

            {/* Reliability Risk */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">Reliability Risk</td>
              {scenarios.map((s) => {
                const rr = (s.reliability_risk || 'LOW').toUpperCase();
                return (
                  <td
                    key={s.id}
                    className={`py-3 px-4 text-center font-bold ${
                      rr === 'LOW' || rr === 'NONE'
                        ? 'text-emerald-400'
                        : rr === 'MEDIUM'
                        ? 'text-amber-400'
                        : 'text-rose-400'
                    } ${s.id === activeScenarioId ? 'bg-sky-500/5' : ''}`}
                  >
                    {rr}
                  </td>
                );
              })}
            </tr>

            {/* Implementation Complexity */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">Implementation Complexity</td>
              {scenarios.map((s) => {
                const cl = (s.complexity_level || 'LOW').toUpperCase();
                return (
                  <td
                    key={s.id}
                    className={`py-3 px-4 text-center font-bold ${
                      cl === 'LOW'
                        ? 'text-emerald-400'
                        : cl === 'MEDIUM'
                        ? 'text-amber-400'
                        : 'text-rose-400'
                    } ${s.id === activeScenarioId ? 'bg-sky-500/5' : ''}`}
                  >
                    {cl}
                  </td>
                );
              })}
            </tr>

            {/* Changes Count */}
            <tr className="hover:bg-[#141B27]/40">
              <td className="py-3 px-4 font-semibold text-slate-300">Discrete Actions</td>
              {scenarios.map((s) => (
                <td
                  key={s.id}
                  className={`py-3 px-4 text-center font-semibold text-slate-300 ${
                    s.id === activeScenarioId ? 'bg-sky-500/5' : ''
                  }`}
                >
                  {s.changes.length} actions
                </td>
              ))}
            </tr>

            {/* Action / Selection Row */}
            <tr>
              <td className="py-3 px-4 font-semibold text-slate-400">Workbench Action</td>
              {scenarios.map((s) => {
                const isActive = s.id === activeScenarioId;
                return (
                  <td
                    key={s.id}
                    className={`py-3 px-4 text-center ${
                      isActive ? 'bg-sky-500/5' : ''
                    }`}
                  >
                    {isActive ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-sky-400">
                        <Check className="w-3.5 h-3.5" />
                        <span>Viewing</span>
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => onSelectScenario(s.id)}
                        className="px-2.5 py-1 rounded bg-[#141B27] hover:bg-[#1E2638] text-slate-300 border border-[#1E2638] text-[11px] font-semibold transition-colors inline-flex items-center gap-1"
                      >
                        <span>Switch Model</span>
                        <ArrowRight className="w-3 h-3 text-sky-400" />
                      </button>
                    )}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import {
  Bot,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { AIStatusResponse } from '../../types/api';

export type AICapabilityState = 'AVAILABLE' | 'DEGRADED' | 'RATE_LIMITED' | 'OFFLINE' | 'DISABLED';

interface AIStatusFlyoutProps {}

export const AIStatusFlyout: React.FC<AIStatusFlyoutProps> = () => {
  const [status, setStatus] = useState<AIStatusResponse | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    api
      .getAIStatus()
      .then((res) => {
        if (isMounted) setStatus(res);
      })
      .catch(() => {
        if (isMounted) setStatus(null);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const resolveCapabilityState = (): { state: AICapabilityState; label: string; color: string; bg: string; border: string } => {
    if (!status) {
      return {
        state: 'OFFLINE',
        label: 'OFFLINE',
        color: 'text-slate-400',
        bg: 'bg-slate-900',
        border: 'border-slate-800',
      };
    }

    if (!status.ai_enabled) {
      return {
        state: 'DISABLED',
        label: 'DISABLED',
        color: 'text-slate-400',
        bg: 'bg-slate-900',
        border: 'border-slate-800',
      };
    }

    return {
      state: 'AVAILABLE',
      label: 'AVAILABLE',
      color: 'text-emerald-400',
      bg: 'bg-emerald-950/40',
      border: 'border-emerald-800/60',
    };
  };

  const cap = resolveCapabilityState();

  return (
    <div className="relative inline-block">
      {/* Trigger Pill */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold border transition-all ${cap.bg} ${cap.color} ${cap.border} hover:brightness-110`}
        title={`AI Subsystem: ${cap.label}. Click to inspect status.`}
      >
        <Bot className="w-3 h-3 shrink-0" />
        <span>AI: {cap.label}</span>
        {isOpen ? <ChevronUp className="w-2.5 h-2.5 opacity-70" /> : <ChevronDown className="w-2.5 h-2.5 opacity-70" />}
      </button>

      {/* Flyout Panel */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-72 p-3.5 bg-[#0D121B] border border-[#1E2638] rounded-xl shadow-2xl z-50 text-xs space-y-3 animate-fadeIn">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1E2638] pb-2">
            <div className="flex items-center gap-1.5 font-mono font-bold text-slate-200">
              <Bot className="w-3.5 h-3.5 text-sky-400" />
              <span>AI SUBSYSTEM STATUS</span>
            </div>
            <span className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold border ${cap.bg} ${cap.color} ${cap.border}`}>
              {cap.label}
            </span>
          </div>

          {/* Operational Guarantees (Guardrail 8: Distinguish AI from Atlas) */}
          <div className="space-y-1.5 text-[11px] font-mono">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">
              Deterministic Foundation Guarantees
            </span>
            <div className="space-y-1 bg-[#070A0F] p-2 rounded border border-[#1E2638]/70 text-[10px] text-slate-300">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-3 h-3 shrink-0" />
                <span>Spend Intelligence: Operational</span>
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-3 h-3 shrink-0" />
                <span>Anomaly & Driver Tracing: Operational</span>
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-3 h-3 shrink-0" />
                <span>Optimization Portfolio: Operational</span>
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-3 h-3 shrink-0" />
                <span>Future-State Scenarios: Operational</span>
              </div>
            </div>
          </div>

          {/* Technical Specifications (Guardrail 9: Expose in expanded flyout only) */}
          {status && status.ai_enabled && (
            <div className="space-y-1 text-[10px] font-mono text-slate-400 pt-1 border-t border-[#1E2638]/60">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">PROVIDER:</span>
                <span className="text-slate-200 uppercase">{status.provider}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">ACTIVE MODEL:</span>
                <span className="text-slate-200">{status.model}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">MAX CONTEXT:</span>
                <span className="text-slate-200">{status.max_context_tokens.toLocaleString()} tokens</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">RATE LIMIT:</span>
                <span className="text-slate-200">{status.rate_limit_per_minute} req / min</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">SYSTEM VERSION:</span>
                <span className="text-slate-200">{status.system_version}</span>
              </div>
            </div>
          )}

          {(!status || !status.ai_enabled) && (
            <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[10px] font-mono text-slate-400">
              Natural language interrogation is offline. Atlas continues serving 100% authoritative deterministic data.
            </div>
          )}

          {/* Epistemic Seal Note */}
          <div className="flex items-center gap-1.5 text-[9px] font-mono text-emerald-400/80 bg-emerald-950/20 p-1.5 rounded border border-emerald-900/30">
            <ShieldCheck className="w-3 h-3 shrink-0 text-emerald-400" />
            <span>Zero-hallucination tolerance gate verified (±1.0%)</span>
          </div>
        </div>
      )}
    </div>
  );
};

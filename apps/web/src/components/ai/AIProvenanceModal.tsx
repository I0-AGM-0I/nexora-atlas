import React, { useEffect, useState } from 'react';
import {
  X,
  Hash,
  ShieldCheck,
  Cpu,
  Clock,
  DollarSign,
  Copy,
  Check,
  Layers,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { AIInteractionDetailResponse } from '../../types/api';
import { EpistemicBadge } from '../ui/EpistemicBadge';

interface AIProvenanceModalProps {
  interactionId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const AIProvenanceModal: React.FC<AIProvenanceModalProps> = ({
  interactionId,
  isOpen,
  onClose,
}) => {
  const [data, setData] = useState<AIInteractionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [activeTab, setActiveTab] = useState<'METRICS' | 'EVIDENCE_SAMPLE' | 'RAW_AUDIT'>('METRICS');

  useEffect(() => {
    if (!isOpen || !interactionId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    api
      .getAIInteraction(interactionId)
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) {
          setError(err?.message || 'Failed to retrieve interaction provenance record.');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, interactionId]);

  // Global Esc key listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleCopyHash = () => {
    if (data?.evidence_hash) {
      navigator.clipboard.writeText(data.evidence_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleCopyId = () => {
    if (data?.id) {
      navigator.clipboard.writeText(data.id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 select-none">
      {/* Backdrop */}
      <div className="fixed inset-0" onClick={onClose} />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-2xl bg-[#0F141C] border border-[#1E2638] rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-fadeIn">
        {/* Header */}
        <div className="h-14 px-6 border-b border-[#1E2638] flex items-center justify-between bg-[#141B27]/90">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-sky-500/15 border border-sky-500/40 flex items-center justify-center">
              <Hash className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-100">AI PROVENANCE & AUDIT LOG</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  GATE VERIFIED
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400">
                Cryptographic Evidence & Subsystem Accounting
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-[#1A2234] transition-colors"
            aria-label="Close Audit Modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="p-12 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin text-sky-400" />
            <span className="text-xs font-mono">Retrieving cryptographic audit record...</span>
          </div>
        )}

        {error && (
          <div className="p-6">
            <div className="p-4 rounded-lg bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300 flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">Provenance Retrieval Failed</div>
                <div className="text-slate-400 text-[11px] mt-0.5">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Content Body */}
        {data && !loading && (
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {/* 1. Evidence Tolerance & Verification Seal (Guardrail 2) */}
            <div className="p-3.5 rounded-lg bg-[#070A0F] border border-emerald-500/30 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <div>
                  <div className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wide">
                    NUMERIC CLAIMS VERIFIED
                  </div>
                  <div className="text-[10px] font-mono text-slate-400">
                    Evidence validation tolerance: <span className="text-emerald-400 font-semibold">±1.0%</span> against authoritative database records.
                  </div>
                </div>
              </div>
              <div className="text-[10px] font-mono text-slate-500 text-right">
                STATUS: <span className="text-emerald-400 font-bold uppercase">{data.response_status}</span>
              </div>
            </div>

            {/* 2. Cryptographic Digest (SHA-256) */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span className="font-semibold uppercase tracking-wider text-slate-300">Canonical Evidence Hash (SHA-256)</span>
                <button
                  onClick={handleCopyHash}
                  className="flex items-center gap-1 text-sky-400 hover:text-sky-300 transition-colors"
                >
                  {copiedHash ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedHash ? 'Copied' : 'Copy Digest'}</span>
                </button>
              </div>
              <div className="p-2.5 bg-[#070A0F] border border-[#1E2638] rounded-md font-mono text-xs text-sky-300 break-all select-all">
                {data.evidence_hash}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">
                Computed deterministically from sorted, budgeted evidence package items prior to model execution.
              </p>
            </div>

            {/* Tabs switcher */}
            <div className="flex items-center gap-2 border-b border-[#1E2638] pb-1 text-xs font-mono">
              <button
                onClick={() => setActiveTab('METRICS')}
                className={`px-3 py-1.5 rounded-t font-semibold transition-colors ${
                  activeTab === 'METRICS'
                    ? 'text-sky-400 border-b-2 border-sky-400 bg-[#141B27]/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                ACCOUNTING & VERSIONS
              </button>
              <button
                onClick={() => setActiveTab('EVIDENCE_SAMPLE')}
                className={`px-3 py-1.5 rounded-t font-semibold transition-colors ${
                  activeTab === 'EVIDENCE_SAMPLE'
                    ? 'text-sky-400 border-b-2 border-sky-400 bg-[#141B27]/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                SANITIZED EVIDENCE PREVIEW ({data.evidence_count} items)
              </button>
            </div>

            {/* Tab 1: Subsystem Accounting & Versions */}
            {activeTab === 'METRICS' && (
              <div className="space-y-4">
                {/* 4-card metric strip */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-[#070A0F] border border-[#1E2638] rounded-lg space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">EXECUTION LATENCY</span>
                    <div className="text-base font-mono font-bold text-slate-200 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-sky-400" />
                      <span>{data.latency_ms} ms</span>
                    </div>
                  </div>

                  <div className="p-3 bg-[#070A0F] border border-[#1E2638] rounded-lg space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">TOTAL TOKENS</span>
                    <div className="text-base font-mono font-bold text-slate-200 flex items-center gap-1">
                      <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{data.input_token_count + data.output_token_count}</span>
                    </div>
                    <div className="text-[9px] font-mono text-slate-500">
                      in: {data.input_token_count} · out: {data.output_token_count}
                    </div>
                  </div>

                  <div className="p-3 bg-[#070A0F] border border-[#1E2638] rounded-lg space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">QUERY COST (EST)</span>
                    <div className="text-base font-mono font-bold text-emerald-400 flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5" />
                      <span>${Number(data.estimated_cost_usd).toFixed(5)}</span>
                    </div>
                  </div>

                  <div className="p-3 bg-[#070A0F] border border-[#1E2638] rounded-lg space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">EVIDENCE ITEMS</span>
                    <div className="text-base font-mono font-bold text-slate-200 flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-amber-400" />
                      <span>{data.evidence_count}</span>
                    </div>
                  </div>
                </div>

                {/* Subsystem & Version Metadata Matrix */}
                <div className="p-3.5 bg-[#070A0F] border border-[#1E2638] rounded-lg space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#1E2638]">
                    <span className="text-slate-500">PROVIDER & MODEL:</span>
                    <span className="text-slate-200 font-semibold">{data.provider} / {data.model}</span>
                  </div>
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#1E2638]">
                    <span className="text-slate-500">PROMPT VERSION:</span>
                    <span className="text-slate-200">{data.prompt_version}</span>
                  </div>
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#1E2638]">
                    <span className="text-slate-500">CONTEXT VERSION:</span>
                    <span className="text-slate-200">{data.context_version}</span>
                  </div>
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#1E2638]">
                    <span className="text-slate-500">SCOPE BOUNDARY:</span>
                    <span className="text-sky-400 font-semibold">{data.scope_type} {data.scope_id ? `(${data.scope_id})` : ''}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">INTERACTION ID:</span>
                    <div className="flex items-center gap-2 text-slate-400">
                      <span className="truncate max-w-[200px]">{data.id}</span>
                      <button onClick={handleCopyId} className="text-sky-400 hover:text-sky-300">
                        {copiedId ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Sanitized Evidence Preview (Guardrail 3) */}
            {activeTab === 'EVIDENCE_SAMPLE' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Authoritative Backend Evidence Package Sample</span>
                  <span className="text-slate-500">{data.evidence_count} total items canonicalized</span>
                </div>

                {data.sanitized_evidence_preview?.items_sample ? (
                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {data.sanitized_evidence_preview.items_sample.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded bg-[#070A0F] border border-[#1E2638] text-xs font-mono space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sky-400 font-bold">{item.id}</span>
                          <EpistemicBadge classification={item.epistemic_class} size="xs" />
                        </div>
                        <p className="text-slate-300 text-[11px]">{item.statement}</p>
                        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-[#1E2638]/50">
                          <span>SOURCE: {item.source}</span>
                          {item.value !== undefined && item.value !== null && (
                            <span className="text-slate-300 font-semibold">
                              {item.unit === 'INR' ? '₹' : ''}
                              {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
                              {item.unit && item.unit !== 'INR' ? ` ${item.unit}` : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-[#070A0F] border border-[#1E2638] rounded text-xs font-mono text-slate-500 text-center">
                    {data.sanitized_evidence_preview?.note || 'No sanitized evidence items sample returned for this record.'}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="h-12 px-6 border-t border-[#1E2638] flex items-center justify-between bg-[#141B27]/50 text-xs font-mono text-slate-500">
          <span>Enterprise Audit Log Immutable Record</span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

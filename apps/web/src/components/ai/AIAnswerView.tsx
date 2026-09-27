import React, { useState } from 'react';
import {
  Clock,
  AlertCircle,
  Hash,
  Sparkles,
  ShieldCheck,
  Copy,
  Check,
  Layers,
  ChevronRight,
} from 'lucide-react';
import type { AIAskResponse, EpistemicClass } from '../../types/api';
import { InteractiveEvidenceCitation } from './InteractiveEvidenceCitation';
import { AIProvenanceModal } from './AIProvenanceModal';

interface AIAnswerViewProps {
  response: AIAskResponse;
  onNavigate?: () => void;
}

const EPISTEMIC_STYLES: Record<
  EpistemicClass,
  { bg: string; text: string; border: string; label: string }
> = {
  OBSERVED: {
    bg: 'bg-slate-900',
    text: 'text-slate-300',
    border: 'border-slate-700',
    label: 'OBSERVED FACT',
  },
  DERIVED: {
    bg: 'bg-blue-950/50',
    text: 'text-blue-300',
    border: 'border-blue-800',
    label: 'DERIVED CALCULATION',
  },
  INFERRED: {
    bg: 'bg-amber-950/50',
    text: 'text-amber-300',
    border: 'border-amber-800',
    label: 'RULE INFERENCE',
  },
  ASSUMED: {
    bg: 'bg-purple-950/50',
    text: 'text-purple-300',
    border: 'border-purple-800',
    label: 'BASELINE ASSUMPTION',
  },
  PROJECTED: {
    bg: 'bg-cyan-950/50',
    text: 'text-cyan-300',
    border: 'border-cyan-800',
    label: 'PROJECTED SCENARIO',
  },
  NOT_AVAILABLE: {
    bg: 'bg-rose-950/50',
    text: 'text-rose-300',
    border: 'border-rose-800',
    label: 'DATA NOT AVAILABLE',
  },
};

export const AIAnswerView: React.FC<AIAnswerViewProps> = ({ response, onNavigate }) => {
  const { answer, data_freshness, evidence_hash, latency_ms, token_count, estimated_cost_usd, evidence_count } = response;
  const [isProvenanceModalOpen, setIsProvenanceModalOpen] = useState(false);
  const [copiedFinding, setCopiedFinding] = useState(false);

  if (!answer) {
    return (
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-300 text-sm">
        {response.error_message || 'No explanation could be generated for this request.'}
      </div>
    );
  }

  // Guardrail 10: Copy sanitized finding only
  const handleCopyFinding = () => {
    const lines = [
      `[ATLAS VERIFIED RESEARCH FINDING]`,
      `Question: ${response.question}`,
      `Scope: ${response.scope_type}${response.scope_id ? ` (${response.scope_id})` : ''}`,
      ``,
      `Summary:`,
      answer.summary,
      ``,
      `Detailed Finding:`,
      answer.answer,
      ``,
      `Conclusions:`,
      ...answer.conclusions.map(
        (c, idx) => `${idx + 1}. [${c.epistemic_class}] ${c.statement}`
      ),
      ``,
      `Evidence Hash: ${response.evidence_hash}`,
      `Verification: Numeric claims verified within ±1.0% tolerance against authoritative Atlas records.`,
    ];

    navigator.clipboard.writeText(lines.join('\n'));
    setCopiedFinding(true);
    setTimeout(() => setCopiedFinding(false), 2000);
  };

  // Collect all unique cited evidence IDs across all conclusions
  const allCitedEvidenceIds = Array.from(
    new Set(answer.conclusions.flatMap((c) => c.evidence_ids || []))
  );

  return (
    <div className="space-y-5 text-slate-200">
      {/* 1. Header Toolbar with Copy Finding & Provenance Trigger */}
      <div className="flex items-center justify-between gap-2 border-b border-[#1E2638] pb-3 text-xs font-mono">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-semibold text-slate-200 uppercase tracking-wide">
            Verified Research Finding
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyFinding}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#141B27] hover:bg-[#1E2638] text-slate-300 hover:text-slate-100 border border-[#1E2638] text-[11px] transition-colors"
            title="Copy verified finding and conclusions to clipboard"
          >
            {copiedFinding ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copiedFinding ? 'Copied' : 'Copy Finding'}</span>
          </button>

          <button
            onClick={() => setIsProvenanceModalOpen(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-[11px] transition-colors"
            title="Inspect cryptographic hash, token accounting, and sanitized evidence preview"
          >
            <Hash className="w-3 h-3 text-sky-400" />
            <span>Inspect Provenance</span>
          </button>
        </div>
      </div>

      {/* 2. Data Freshness & Observation Horizon */}
      {data_freshness && (
        <div className="flex items-center justify-between gap-2 px-3 py-1.5 bg-[#070A0F] border border-[#1E2638] rounded-md text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-sky-400 shrink-0" />
            <span>{data_freshness.freshness_summary}</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold uppercase">
            ● {data_freshness.status}
          </span>
        </div>
      )}

      {/* 3. Executive Summary */}
      <div className="p-4 bg-[#0F141C] border border-[#1E2638] rounded-lg space-y-2">
        <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
          <span>01 · Executive Summary</span>
        </div>
        <p className="text-sm font-medium text-slate-100 leading-relaxed">
          {answer.summary}
        </p>
      </div>

      {/* 4. Detailed Explanation */}
      <div className="space-y-2">
        <h4 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
          02 · Detailed Analytical Explanation
        </h4>
        <div className="p-4 bg-[#0F141C]/80 border border-[#1E2638] rounded-lg text-xs leading-relaxed text-slate-300 whitespace-pre-line font-sans">
          {answer.answer}
        </div>
      </div>

      {/* 5. Interactive Evidence Citations Index (Guardrail 4) */}
      {allCitedEvidenceIds.length > 0 && (
        <div className="p-3.5 bg-[#070A0F] border border-[#1E2638] rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-sky-400" />
              <span>Cited Evidence Items ({allCitedEvidenceIds.length})</span>
            </span>
            <span className="text-[10px] font-mono text-slate-500">Click pill to inspect source</span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {allCitedEvidenceIds.map((eid, idx) => (
              <InteractiveEvidenceCitation
                key={eid}
                evidenceId={eid}
                index={idx}
                response={response}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        </div>
      )}

      {/* 6. Grounded Conclusions & Numeric Claims with Tolerance Seal (Guardrail 2) */}
      {answer.conclusions && answer.conclusions.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
              03 · Grounded Conclusions ({answer.conclusions.length})
            </h4>
            {/* Guardrail 2: Strict wording */}
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-800/40">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>NUMERIC CLAIMS VERIFIED · Tolerance: ±1.0%</span>
            </div>
          </div>

          <div className="space-y-2">
            {answer.conclusions.map((concl, idx) => {
              const style = EPISTEMIC_STYLES[concl.epistemic_class] || EPISTEMIC_STYLES.NOT_AVAILABLE;
              return (
                <div
                  key={idx}
                  className="p-3 bg-[#0F141C] border border-[#1E2638] rounded-lg space-y-2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-xs text-slate-200 leading-relaxed font-sans">{concl.statement}</p>
                    <span
                      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${style.bg} ${style.text} ${style.border} shrink-0`}
                    >
                      {style.label}
                    </span>
                  </div>

                  {/* Verified Numeric Claims */}
                  {concl.numeric_claims && concl.numeric_claims.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      {concl.numeric_claims.map((claim, cIdx) => (
                        <div
                          key={cIdx}
                          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#070A0F] text-slate-300 border border-[#1E2638] text-[11px] font-mono"
                          title={`Verified claim against evidence '${claim.evidence_id}' within ±1.0% tolerance.`}
                        >
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                          <span className="font-semibold text-slate-100">
                            {`${claim.unit === 'INR' ? '₹' : ''}${typeof claim.value === 'number' ? claim.value.toLocaleString() : claim.value}${claim.unit && claim.unit !== 'INR' ? ` ${claim.unit}` : ''}`}
                          </span>
                          <span className="text-[10px] text-slate-500 font-normal">({claim.evidence_id})</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Evidence Pills */}
                  {concl.evidence_ids && concl.evidence_ids.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[10px] font-mono text-slate-500">Grounding:</span>
                      {concl.evidence_ids.map((eid, eIdx) => (
                        <InteractiveEvidenceCitation
                          key={eid}
                          evidenceId={eid}
                          index={eIdx}
                          response={response}
                          onNavigate={onNavigate}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 7. Limitations & Caveats */}
      {answer.limitations && answer.limitations.length > 0 && (
        <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-lg space-y-1.5">
          <div className="flex items-center gap-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-amber-400">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Data Limitations & Boundary Caveats</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-amber-200/80 font-sans">
            {answer.limitations.map((lim, lIdx) => (
              <li key={lIdx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 8. Recommended Next Steps (Strictly Read-Only Analytical Investigations) */}
      {answer.recommended_next_steps && answer.recommended_next_steps.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
            04 · Recommended Investigative Paths
          </h4>
          <div className="space-y-1.5">
            {answer.recommended_next_steps.map((step, sIdx) => (
              <div
                key={sIdx}
                className="flex items-start gap-2 p-2 bg-[#0F141C] border border-[#1E2638] rounded-md text-xs text-slate-300 font-mono"
              >
                <ChevronRight className="w-3.5 h-3.5 text-sky-400 mt-0.5 shrink-0" />
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 9. Provenance Digest Footer */}
      <div className="pt-3 border-t border-[#1E2638] flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-slate-500">
        <button
          onClick={() => setIsProvenanceModalOpen(true)}
          className="flex items-center gap-1.5 hover:text-sky-400 transition-colors text-left"
          title="Click to view full cryptographic audit provenance"
        >
          <Hash className="w-3 h-3 text-slate-600" />
          <span>Digest: {evidence_hash.substring(0, 16)}...</span>
        </button>

        <div className="flex items-center gap-3">
          <span>{evidence_count} items</span>
          <span>{latency_ms} ms</span>
          <span>{token_count} tokens</span>
          {Number(estimated_cost_usd) > 0 && (
            <span>${Number(estimated_cost_usd).toFixed(5)}</span>
          )}
        </div>
      </div>

      {/* Provenance Audit Modal Dialog */}
      <AIProvenanceModal
        interactionId={response.interaction_id}
        isOpen={isProvenanceModalOpen}
        onClose={() => setIsProvenanceModalOpen(false)}
      />
    </div>
  );
};

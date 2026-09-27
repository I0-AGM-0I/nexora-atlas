import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Sparkles,
  ArrowRight,
  Loader2,
  AlertCircle,
  ShieldCheck,
  RotateCcw,
  MessageSquare,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { AIAskResponse } from '../../types/api';
import type { AskAtlasContextData } from '../../lib/AskAtlasContext';
import { AIAnswerView } from './AIAnswerView';
import { AIStatusFlyout } from './AIStatusFlyout';

interface AskAtlasDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  context?: AskAtlasContextData | null;
  onClearContext?: () => void;
}

interface ConversationEntry {
  id: string;
  question: string;
  response: AIAskResponse;
  timestamp: string;
}

const DEFAULT_GLOBAL_SUGGESTIONS = [
  'Why did technology spend increase over the last period?',
  'What are the primary cost drivers across services?',
  'Where is the largest addressable waste in the estate?',
  'Summarize the optimization portfolio compatibility and risk profile.',
  'Evaluate capacity headroom for production compute workloads.',
];

export const AskAtlasDrawer: React.FC<AskAtlasDrawerProps> = ({
  isOpen,
  onClose,
  context,
  onClearContext,
}) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('Analyzing query intent...');
  const [error, setError] = useState<string | null>(null);

  // Multi-turn thread state (Guardrail 5: session_id passed for entity disambiguation only)
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [history, setHistory] = useState<ConversationEntry[]>([]);
  const scrollEndRef = useRef<HTMLDivElement>(null);

  // Data-driven contextual suggestions generation (Guardrail 7)
  const getContextualSuggestions = (): string[] => {
    if (!context) return DEFAULT_GLOBAL_SUGGESTIONS;

    if (context.suggestedQueries && context.suggestedQueries.length > 0) {
      return context.suggestedQueries;
    }

    if (context.resourceId) {
      const name = context.resourceName || context.resourceId;
      return [
        `Evaluate capacity headroom and telemetry sufficiency for ${name}.`,
        `Why is this resource considered optimizable?`,
        `Compare downsizing alternatives and operational trade-offs for ${name}.`,
      ];
    }

    if (context.recommendationId) {
      return [
        `Explain the technical rationale and trade-offs for this recommendation.`,
        `Is this recommendation compatible with the rest of the optimization portfolio?`,
        `What are the pre-change and rollback operational considerations?`,
      ];
    }

    if (context.anomalyId) {
      return [
        `Analyze the root cause and contributing drivers for this cost change.`,
        `Trace the operational telemetry supporting this anomaly detection.`,
        `Is this cost increase expected to be sustained or transient?`,
      ];
    }

    if (context.scenarioId) {
      return [
        `What assumptions and change specifications produced these projected savings?`,
        `Explain the operational risk and complexity dimensions of this scenario.`,
        `How does this scenario trajectory compare to organic status-quo forecast?`,
      ];
    }

    if (context.serviceName) {
      return [
        `What is driving the spend trend for ${context.serviceName}?`,
        `Break down compute vs storage allocation for ${context.serviceName}.`,
        `Are there unmanaged resources or idle capacity in ${context.serviceName}?`,
      ];
    }

    return DEFAULT_GLOBAL_SUGGESTIONS;
  };

  // Sync initial question if contextual trigger provided one
  useEffect(() => {
    if (context?.initialQuestion) {
      setQuestion(context.initialQuestion);
    }
  }, [context]);

  // Platform-Safe Global Keyboard Handling (Guardrail 6)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Esc closes drawer
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Scroll to latest message on response
  useEffect(() => {
    if (history.length > 0 && !loading && scrollEndRef.current && typeof scrollEndRef.current.scrollIntoView === 'function') {
      scrollEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [history, loading]);

  if (!isOpen) return null;

  const handleResetSession = () => {
    setHistory([]);
    setSessionId(null);
    setQuestion('');
    setError(null);
    if (onClearContext) onClearContext();
  };

  const handleSubmit = async (queryToSubmit?: string) => {
    const q = (queryToSubmit || question).trim();
    if (!q || loading) return;

    setLoading(true);
    setError(null);
    setLoadingStep('Authorizing scope & classifying query intent...');

    const timer1 = setTimeout(() => {
      setLoadingStep('Retrieving authoritative Atlas evidence package...');
    }, 350);

    const timer2 = setTimeout(() => {
      setLoadingStep('Verifying numeric claims within ±1.0% tolerance...');
    }, 700);

    try {
      // Guardrail 1 & 5: Fresh backend retrieval with session_id for entity reference
      const res = await api.askAtlas({
        question: q,
        scope_type: context?.scopeType || 'DASHBOARD',
        scope_id: context?.resourceId || context?.recommendationId || context?.anomalyId || context?.scenarioId,
        session_id: sessionId || undefined,
      });

      // Update session ID from backend
      setSessionId(res.session_id);

      // Append to multi-turn thread
      const newEntry: ConversationEntry = {
        id: res.interaction_id,
        question: q,
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setHistory((prev) => [...prev, newEntry]);
      setQuestion('');
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve verified explanation from Atlas.');
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setLoading(false);
    }
  };

  const suggestions = getContextualSuggestions();

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs select-none">
      {/* Click outside backdrop to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Drawer Container */}
      <div className="w-full max-w-2xl h-full bg-[#0F141C] border-l border-[#1E2638] shadow-2xl flex flex-col animate-slide-left">
        {/* Header */}
        <div className="h-14 px-5 border-b border-[#1E2638] flex items-center justify-between bg-[#141B27]/90 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-sky-500/15 border border-sky-500/40 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-100 font-mono">ASK ATLAS</span>
                <AIStatusFlyout />
              </div>
              <p className="text-[10px] text-slate-400 font-mono">
                Technology Financial Economics Research Console
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={handleResetSession}
                className="flex items-center gap-1 px-2 py-1 rounded bg-[#1A2234] hover:bg-[#232D42] text-slate-400 hover:text-slate-200 text-[10px] font-mono transition-colors"
                title="Reset session and start a new inquiry thread"
              >
                <RotateCcw className="w-3 h-3" />
                <span>New Inquiry</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-[#1A2234] transition-colors"
              aria-label="Close Ask Atlas"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Active Context Banner (Guardrail 7) */}
        {context && (
          <div className="px-5 py-2 bg-[#070A0F] border-b border-[#1E2638] flex items-center justify-between text-[11px] font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 uppercase">ACTIVE CONTEXT:</span>
              <span className="text-sky-400 font-semibold uppercase">
                {context.scopeType || 'SCOPED'}
              </span>
              <span className="text-slate-300">
                · {context.scopeLabel || context.resourceName || context.resourceId || context.serviceName || 'Custom Scope'}
              </span>
            </div>
            {onClearContext && (
              <button
                onClick={onClearContext}
                className="text-[10px] text-slate-500 hover:text-slate-300 underline"
              >
                Clear Scope
              </button>
            )}
          </div>
        )}

        {/* Scrollable Conversation Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Welcome Screen & Suggestions (When no history yet) */}
          {history.length === 0 && !loading && (
            <div className="space-y-4 pt-2">
              <div className="p-4 bg-[#070A0F] border border-[#1E2638] rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Authoritative Technology Financial Intelligence</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed font-sans">
                  Ask Atlas is the natural-language interrogation interface over verified Atlas infrastructure telemetry, Cost Explorer billing records, and deterministic optimization models.
                </p>
                <div className="text-[10px] font-mono text-emerald-400/90 pt-1 border-t border-[#1E2638]/60">
                  ✓ 100% Grounded in authoritative DB evidence · ±1.0% numeric tolerance gate enforced
                </div>
              </div>

              {/* Data-Driven Suggestions */}
              <div className="space-y-2">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <MessageSquare className="w-3 h-3 text-sky-400" />
                  <span>Suggested Research Inquiries</span>
                </div>
                <div className="space-y-1.5">
                  {suggestions.map((sug, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setQuestion(sug);
                        handleSubmit(sug);
                      }}
                      className="w-full text-left p-2.5 rounded-lg bg-[#0F141C] hover:bg-[#141B27] border border-[#1E2638] hover:border-sky-500/50 text-xs text-slate-300 hover:text-sky-300 transition-all flex items-center justify-between group"
                    >
                      <span className="font-sans">{sug}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400 transition-transform group-hover:translate-x-0.5 shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Conversation Thread History */}
          {history.map((entry, index) => (
            <div key={`${entry.id}-${index}`} className="space-y-4 border-b border-[#1E2638]/70 pb-6 last:border-b-0">
              {/* User Question Bubble */}
              <div className="flex items-start gap-3 bg-[#141B27]/60 p-3.5 rounded-lg border border-[#1E2638]">
                <div className="w-6 h-6 rounded bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-mono font-bold shrink-0">
                  Q{index + 1}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span>INVESTIGATION QUERY</span>
                    <span>{entry.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-100 font-medium font-sans">
                    {entry.question}
                  </p>
                </div>
              </div>

              {/* Verified Finding Answer */}
              <AIAnswerView response={entry.response} onNavigate={onClose} />
            </div>
          ))}

          {/* Loading Indicator */}
          {loading && (
            <div className="p-6 bg-[#070A0F] border border-[#1E2638] rounded-xl flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-sky-400" />
              <div className="text-xs font-mono text-slate-300">{loadingStep}</div>
              <div className="text-[10px] font-mono text-slate-500">
                Checking empirical evidence packages & numeric tolerance gate...
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-lg bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold">Investigation Failed</div>
                <div className="text-slate-300 text-[11px] font-mono">{error}</div>
              </div>
            </div>
          )}

          <div ref={scrollEndRef} />
        </div>

        {/* Query Input Box Footer (Guardrail 6: Platform-Safe Ctrl/Cmd+Enter) */}
        <div className="p-4 border-t border-[#1E2638] bg-[#141B27]/80 shrink-0 space-y-2">
          <div className="relative">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder={
                context
                  ? `Ask about ${context.scopeLabel || context.resourceName || context.serviceName || 'active context'}...`
                  : 'Ask about cost deltas, driver attribution, capacity headroom, or scenario trade-offs...'
              }
              rows={2}
              className="w-full bg-[#070A0F] border border-[#1E2638] rounded-lg p-3 pr-24 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500 transition-all resize-none font-sans"
            />
            <button
              onClick={() => handleSubmit()}
              disabled={loading || !question.trim()}
              className="absolute bottom-3 right-3 px-3 py-1.5 rounded bg-sky-500 hover:bg-sky-400 disabled:opacity-40 disabled:hover:bg-sky-500 text-black text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Investigate</span>
                  <ArrowRight className="w-3 h-3" />
                </>
              )}
            </button>
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>
              Press <kbd className="px-1 py-0.5 bg-[#070A0F] rounded text-slate-300 border border-[#1E2638]">Ctrl</kbd> + <kbd className="px-1 py-0.5 bg-[#070A0F] rounded text-slate-300 border border-[#1E2638]">Enter</kbd> to submit
            </span>
            <span>Zero Hallucination Tolerance (±1.0%)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

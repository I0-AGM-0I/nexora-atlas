import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  Loader2,
  RefreshCw,
  RotateCcw,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { ScopeType, AIAskResponse } from '../../types/api';
import { AIAnswerView } from './AIAnswerView';
import { AIStatusIndicator } from './AIStatusIndicator';

interface AskAtlasPanelProps {
  defaultScopeType?: ScopeType;
  defaultScopeId?: string;
  scopeLabel?: string;
  placeholder?: string;
  compact?: boolean;
}

const DASHBOARD_PROMPTS = [
  'Why did spend increase last month?',
  'What are the primary cost drivers across services?',
  'What can I optimize right now?',
  'Are there any unresolved spending anomalies?',
];

const RESOURCE_PROMPTS = [
  'Explain operational telemetry for this resource',
  'Is this resource safe to downsize based on CPU and memory?',
  'What optimization opportunities apply to this instance?',
];

const RECOMMENDATION_PROMPTS = [
  'Explain the technical rationale for this recommendation',
  'What are the risks and workload constraints of this change?',
];

const SCENARIO_PROMPTS = [
  'Explain the tradeoffs and simulation assumptions of this scenario',
  'How do these projected savings compare to actual historical spend?',
];

export const AskAtlasPanel: React.FC<AskAtlasPanelProps> = ({
  defaultScopeType = 'DASHBOARD',
  defaultScopeId,
  scopeLabel,
  placeholder,
  compact = false,
}) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('Analyzing query intent...');
  const [response, setResponse] = useState<AIAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const getSuggestedPrompts = () => {
    switch (defaultScopeType) {
      case 'RESOURCE':
        return RESOURCE_PROMPTS;
      case 'RECOMMENDATION':
        return RECOMMENDATION_PROMPTS;
      case 'SCENARIO':
        return SCENARIO_PROMPTS;
      default:
        return DASHBOARD_PROMPTS;
    }
  };

  const handleAsk = async (queryToAsk?: string) => {
    const q = (queryToAsk || question).trim();
    if (!q || loading) return;

    setLoading(true);
    setError(null);
    setLoadingStep('Retrieving authoritative Atlas evidence...');

    const stepTimer1 = setTimeout(() => {
      setLoadingStep('Evaluating epistemic & numeric contracts...');
    }, 400);

    const stepTimer2 = setTimeout(() => {
      setLoadingStep('Verifying zero-hallucination tolerance...');
    }, 800);

    try {
      const res = await api.askAtlas({
        question: q,
        scope_type: defaultScopeType,
        scope_id: defaultScopeId,
        session_id: sessionId || undefined,
      });

      setResponse(res);
      setSessionId(res.session_id);
      if (queryToAsk) {
        setQuestion(queryToAsk);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate AI explanation.');
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQuestion('');
    setResponse(null);
    setError(null);
    setSessionId(null);
  };

  const inputPlaceholder =
    placeholder ||
    (defaultScopeType === 'RESOURCE'
      ? 'Ask about this resource\'s CPU, memory, or cost...'
      : defaultScopeType === 'RECOMMENDATION'
      ? 'Ask about recommendation rationale or risk...'
      : 'Ask Atlas anything about cloud spend, drivers, or waste...');

  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg transition-all ${compact ? 'border-slate-800/80' : ''}`}>
      {/* Header */}
      <div className="px-5 py-3.5 bg-slate-900/80 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800/80 text-cyan-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <span>Ask Atlas</span>
              {scopeLabel && (
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-normal border border-slate-700">
                  {scopeLabel}
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              Deterministic, evidence-grounded natural language explanations
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <AIStatusIndicator />
          {response && (
            <button
              onClick={handleReset}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
              title="Start a new conversation"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      {!response && (
        <div className="px-5 pt-3 flex flex-wrap gap-2">
          {getSuggestedPrompts().map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleAsk(prompt)}
              disabled={loading}
              className="text-left px-3 py-1.5 rounded-lg bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 hover:border-cyan-700/60 text-xs text-slate-300 hover:text-cyan-300 transition-colors disabled:opacity-50"
            >
              "{prompt}"
            </button>
          ))}
        </div>
      )}

      {/* Query Input Box */}
      <div className="p-5 space-y-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={inputPlaceholder}
            disabled={loading}
            className="w-full pl-4 pr-24 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 disabled:opacity-50 transition-all font-sans"
          />
          <div className="absolute right-1.5 flex items-center gap-1">
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-3.5 py-1.5 rounded-md bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-40 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing</span>
                </>
              ) : (
                <>
                  <span>Ask</span>
                  <Send className="w-3 h-3" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Loading Indicator */}
        {loading && (
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg flex items-center gap-3 text-xs text-cyan-400 font-mono">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400 shrink-0" />
            <span>{loadingStep}</span>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-lg text-xs text-rose-300 flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => handleAsk()}
              className="ml-3 px-2 py-1 bg-rose-900/60 hover:bg-rose-900 rounded text-rose-200 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Explanation Response View */}
        {response && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <AIAnswerView response={response} />
          </div>
        )}
      </div>
    </div>
  );
};

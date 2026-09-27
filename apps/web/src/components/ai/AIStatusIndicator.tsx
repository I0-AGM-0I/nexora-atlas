import React, { useEffect, useState } from 'react';
import { Bot, ShieldCheck, Lock } from 'lucide-react';
import { api } from '../../lib/api';
import type { AIStatusResponse } from '../../types/api';

export const AIStatusIndicator: React.FC = () => {
  const [status, setStatus] = useState<AIStatusResponse | null>(null);

  useEffect(() => {
    api.getAIStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  if (!status) {
    return null;
  }

  if (!status.ai_enabled) {
    return (
      <div
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700"
        title="AI Explanations are disabled. Operating in 100% deterministic offline mode."
      >
        <Lock className="w-3 h-3 text-slate-400" />
        <span>AI: Offline Mode</span>
      </div>
    );
  }

  const isMock = status.provider.toLowerCase() === 'mock';

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
        isMock
          ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
          : 'bg-indigo-950/40 text-indigo-300 border-indigo-800/60'
      }`}
      title={`AI Provider: ${status.provider} (${status.model})`}
    >
      <Bot className="w-3 h-3 text-emerald-400" />
      <span>AI: {isMock ? 'Deterministic Mock' : status.model}</span>
      <span title="Protected by Epistemic & Numeric Hallucination Validator">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
      </span>
    </div>
  );
};

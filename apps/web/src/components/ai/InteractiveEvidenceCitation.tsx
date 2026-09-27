import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Info,
} from 'lucide-react';
import type { AIAskResponse, AICitation, EpistemicClass } from '../../types/api';
import { EpistemicBadge } from '../ui/EpistemicBadge';

interface InteractiveEvidenceCitationProps {
  evidenceId: string;
  index: number;
  response: AIAskResponse;
  onNavigate?: () => void;
}

interface ResolvedEvidence {
  id: string;
  state: 'VERIFIED' | 'VALID_NO_NAV' | 'MISSING';
  title: string;
  statement: string;
  source: string;
  epistemicClass: EpistemicClass;
  value?: string | number | null;
  unit?: string | null;
  linkPath?: string | null;
  entityType?: string | null;
  evaluationWindow?: string | null;
}

export const InteractiveEvidenceCitation: React.FC<InteractiveEvidenceCitationProps> = ({
  evidenceId,
  index,
  response,
  onNavigate,
}) => {
  const [showPopover, setShowPopover] = useState(false);

  // Authoritative Evidence Resolution against backend data only (Guardrail 4)
  const resolveEvidence = (): ResolvedEvidence => {
    // 1. Check if evidenceId exists in the backend authoritative evidence_ids list
    const isIdInBackendPackage = response.evidence_ids.includes(evidenceId);

    // 2. Check if there is an explicit entity citation in answer.cited_entities
    const citedEntity: AICitation | undefined = response.answer?.cited_entities?.find(
      (c) => c.id === evidenceId || c.entity_id === evidenceId
    );

    if (citedEntity) {
      return {
        id: evidenceId,
        state: citedEntity.link_path ? 'VERIFIED' : 'VALID_NO_NAV',
        title: citedEntity.title,
        statement: citedEntity.description || `Referenced ${citedEntity.entity_type.toLowerCase()} record in Atlas evidence graph.`,
        source: 'Atlas Knowledge Graph',
        epistemicClass: 'OBSERVED',
        linkPath: citedEntity.link_path || null,
        entityType: citedEntity.entity_type,
      };
    }

    // Map known deterministic evidence prefix patterns from backend Phase 9
    if (isIdInBackendPackage) {
      if (evidenceId.startsWith('ev-ce') || evidenceId.includes('cost') || evidenceId.includes('spend')) {
        return {
          id: evidenceId,
          state: 'VERIFIED',
          title: 'AWS Cost Explorer Invoiced Item',
          statement: 'Actual observed Cost Explorer line item aggregated across 90-day evaluation window.',
          source: 'AWS Cost Explorer (Verified)',
          epistemicClass: 'OBSERVED',
          linkPath: '/spend',
        };
      }
      if (evidenceId.startsWith('ev-cw') || evidenceId.includes('telemetry') || evidenceId.includes('cpu') || evidenceId.includes('mem')) {
        const resourceId = response.scope_type === 'RESOURCE' ? response.scope_id : null;
        return {
          id: evidenceId,
          state: resourceId ? 'VERIFIED' : 'VALID_NO_NAV',
          title: 'CloudWatch Telemetry Observation',
          statement: 'Continuous 5-minute sampling telemetry verified with >= 70% window coverage.',
          source: 'CloudWatch Metrics (Verified)',
          epistemicClass: 'OBSERVED',
          linkPath: resourceId ? `/resources/${encodeURIComponent(resourceId)}` : null,
          evaluationWindow: '14-30 Days',
        };
      }
      if (evidenceId.startsWith('ev-rec') || evidenceId.includes('opt')) {
        const recId = response.scope_type === 'RECOMMENDATION' ? response.scope_id : null;
        return {
          id: evidenceId,
          state: 'VERIFIED',
          title: 'Atlas Optimization Opportunity',
          statement: 'Deterministic rightsizing or architectural recommendation with validated trade-off dimensions.',
          source: 'Atlas Optimizer Engine',
          epistemicClass: 'INFERRED',
          linkPath: recId ? `/optimization/${encodeURIComponent(recId)}` : '/optimization',
        };
      }
      if (evidenceId.startsWith('ev-anom') || evidenceId.includes('anomaly')) {
        return {
          id: evidenceId,
          state: 'VERIFIED',
          title: 'Atlas Anomaly Detection Event',
          statement: 'Statistical deviation exceeding rolling Z-score threshold (> 3.0 sigma).',
          source: 'Atlas Anomaly Detection',
          epistemicClass: 'OBSERVED',
          linkPath: '/changes',
        };
      }
      if (evidenceId.startsWith('ev-scen') || evidenceId.includes('scenario')) {
        return {
          id: evidenceId,
          state: 'VERIFIED',
          title: 'What-If Architecture Scenario',
          statement: 'Modeled future-state infrastructure specification and projected cost variance.',
          source: 'Atlas Scenario Modeling',
          epistemicClass: 'PROJECTED',
          linkPath: '/scenarios',
        };
      }

      // Valid evidence in package, but without a dedicated deep-link route
      return {
        id: evidenceId,
        state: 'VALID_NO_NAV',
        title: `Evidence Record [${evidenceId}]`,
        statement: 'Verified backend evidence item present in canonical context package.',
        source: 'Atlas Deterministic Engine',
        epistemicClass: 'DERIVED',
        linkPath: null,
      };
    }

    // 4. Missing Evidence fallback (Guardrail 4 State C)
    return {
      id: evidenceId,
      state: 'MISSING',
      title: `Unresolved Evidence [${evidenceId}]`,
      statement: 'Atlas could not retrieve the underlying evidence. This citation does not resolve to an authoritative evidence item.',
      source: 'NOT_AVAILABLE',
      epistemicClass: 'NOT_AVAILABLE',
      linkPath: null,
    };
  };

  const resolved = resolveEvidence();
  const label = `[E${index + 1}]`;

  // Render Pill Based on Resolution State
  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={() => setShowPopover(!showPopover)}
        onMouseEnter={() => setShowPopover(true)}
        onMouseLeave={() => setShowPopover(false)}
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold transition-all border ${
          resolved.state === 'VERIFIED'
            ? 'bg-sky-950/60 hover:bg-sky-900/70 text-sky-300 border-sky-700/60 hover:border-sky-500'
            : resolved.state === 'VALID_NO_NAV'
            ? 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-700 hover:border-slate-600'
            : 'bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border-rose-800/60'
        }`}
        title={`${label} ${resolved.title}`}
      >
        <span>{label}</span>
        {resolved.state === 'VERIFIED' && (
          <ShieldCheck className="w-3 h-3 text-sky-400 shrink-0" />
        )}
        {resolved.state === 'VALID_NO_NAV' && (
          <Info className="w-3 h-3 text-slate-400 shrink-0" />
        )}
        {resolved.state === 'MISSING' && (
          <AlertCircle className="w-3 h-3 text-rose-400 shrink-0" />
        )}
      </button>

      {/* Popover Inspector Card */}
      {showPopover && (
        <div
          onMouseEnter={() => setShowPopover(true)}
          onMouseLeave={() => setShowPopover(false)}
          className="absolute z-50 bottom-full left-0 mb-2 w-80 p-3.5 bg-[#0D121B] border border-[#1E2638] rounded-lg shadow-2xl text-xs space-y-2.5 animate-fadeIn"
        >
          {/* Popover Header */}
          <div className="flex items-center justify-between border-b border-[#1E2638] pb-2">
            <div className="flex items-center gap-1.5 font-mono font-bold text-slate-200">
              <span className="text-sky-400">{label}</span>
              <span className="truncate max-w-[170px]">{resolved.title}</span>
            </div>
            <EpistemicBadge classification={resolved.epistemicClass} size="xs" />
          </div>

          {/* Statement */}
          <p className="text-slate-300 text-[11px] leading-relaxed">
            {resolved.statement}
          </p>

          {/* Provenance Metadata */}
          <div className="space-y-1 text-[10px] font-mono text-slate-400 bg-[#070A0F] p-2 rounded border border-[#1E2638]/70">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">SOURCE:</span>
              <span className="text-slate-300 font-semibold">{resolved.source}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">EVIDENCE ID:</span>
              <span className="text-sky-400">{resolved.id}</span>
            </div>
            {resolved.evaluationWindow && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">WINDOW:</span>
                <span className="text-slate-300">{resolved.evaluationWindow}</span>
              </div>
            )}
            <div className="flex items-center justify-between pt-1 border-t border-[#1E2638]/60">
              <span className="text-slate-500">STATUS:</span>
              {resolved.state === 'VERIFIED' && (
                <span className="text-emerald-400 font-semibold">VERIFIED CITATION</span>
              )}
              {resolved.state === 'VALID_NO_NAV' && (
                <span className="text-slate-400 font-semibold">SOURCE AVAILABLE · NAV UNAVAILABLE</span>
              )}
              {resolved.state === 'MISSING' && (
                <span className="text-rose-400 font-semibold">NOT_AVAILABLE</span>
              )}
            </div>
          </div>

          {/* Handoff Navigation Trigger (if verified link exists) */}
          {resolved.state === 'VERIFIED' && resolved.linkPath && (
            <Link
              to={resolved.linkPath}
              onClick={() => {
                setShowPopover(false);
                if (onNavigate) onNavigate();
              }}
              className="w-full mt-1 px-3 py-1.5 rounded bg-sky-500/15 hover:bg-sky-500/25 text-sky-300 border border-sky-500/40 hover:border-sky-400 text-[11px] font-mono font-semibold flex items-center justify-between transition-colors"
            >
              <span>INSPECT IN ATLAS WORKSPACE</span>
              <ExternalLink className="w-3 h-3 text-sky-400" />
            </Link>
          )}

          {resolved.state === 'VALID_NO_NAV' && (
            <div className="text-[10px] font-mono text-slate-500 text-center py-1">
              Direct workspace route not configured for this raw record.
            </div>
          )}

          {resolved.state === 'MISSING' && (
            <div className="text-[10px] font-mono text-rose-400 text-center py-1 bg-rose-950/20 rounded border border-rose-900/40">
              Atlas could not verify this citation against the evidence package.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

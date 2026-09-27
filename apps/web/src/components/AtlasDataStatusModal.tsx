import React from 'react';
import { X, ShieldCheck, CheckCircle2, Server, Clock, Activity, Cpu } from 'lucide-react';

interface AtlasDataStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AtlasDataStatusModal: React.FC<AtlasDataStatusModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg bg-[#0F141C] border border-[#1E2638] rounded-xl shadow-2xl p-6 space-y-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#1E2638] pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              <h3 className="font-semibold text-sm text-atlas-text tracking-wide">
                ATLAS DATA STATUS & TRUST BOUNDARY
              </h3>
            </div>
            <p className="text-xs text-atlas-muted font-mono">
              Live provenance, synchronization health, and isolation verification
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-atlas-muted hover:text-atlas-text hover:bg-atlas-elevated transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section 1: Cloud Connection */}
        <div className="space-y-2">
          <div className="text-[10px] font-mono uppercase tracking-wider text-atlas-muted">
            01 · Cloud Connection & Inventory
          </div>
          <div className="bg-[#141B27] rounded-lg p-3 border border-[#1E2638] space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-atlas-secondary flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-atlas-primary" />
                Amazon Web Services
              </span>
              <span className="font-mono text-emerald-400 text-[11px] font-semibold">● Connected</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1 text-atlas-muted border-t border-[#1E2638]/60">
              <div>Accounts: <span className="text-atlas-text font-semibold">3 Active</span></div>
              <div>Monitored Resources: <span className="text-atlas-text font-semibold">58 Assets</span></div>
              <div className="col-span-2 text-[11px] text-atlas-muted">
                Auth: <span className="text-slate-300">sts:AssumeRole (Ephemeral 1-hr TTL)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Ingestion Provenance */}
        <div className="space-y-2">
          <div className="text-[10px] font-mono uppercase tracking-wider text-atlas-muted">
            02 · Ingestion Provenance & Freshness
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="bg-[#141B27] p-2.5 rounded border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-atlas-muted flex items-center gap-1">
                  <Clock className="w-3 h-3 text-atlas-primary" />
                  Cost Data
                </span>
                <span className="text-[10px] text-emerald-400">Current</span>
              </div>
              <div className="text-atlas-text text-[11px]">Last sync: 8 min ago</div>
              <div className="text-[10px] text-atlas-muted">90D daily history</div>
            </div>

            <div className="bg-[#141B27] p-2.5 rounded border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-atlas-muted flex items-center gap-1">
                  <Activity className="w-3 h-3 text-atlas-primary" />
                  Telemetry
                </span>
                <span className="text-[10px] text-emerald-400">Healthy</span>
              </div>
              <div className="text-atlas-text text-[11px]">Coverage: 94%</div>
              <div className="text-[10px] text-atlas-muted">CloudWatch 5m metrics</div>
            </div>

            <div className="bg-[#141B27] p-2.5 rounded border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-atlas-muted flex items-center gap-1">
                  <Cpu className="w-3 h-3 text-atlas-primary" />
                  Intelligence
                </span>
                <span className="text-[10px] text-emerald-400">Evaluated</span>
              </div>
              <div className="text-atlas-text text-[11px]">Run: 12 min ago</div>
              <div className="text-[10px] text-atlas-muted">4 changes · 7 opps</div>
            </div>

            <div className="bg-[#141B27] p-2.5 rounded border border-[#1E2638] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-atlas-muted flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-atlas-primary" />
                  AI Verification
                </span>
                <span className="text-[10px] text-emerald-400">Active</span>
              </div>
              <div className="text-atlas-text text-[11px]">Gate: ±1.0% tolerance</div>
              <div className="text-[10px] text-atlas-muted">SHA-256 context hashing</div>
            </div>
          </div>
        </div>

        {/* Section 3: Trust Boundary Enforcement */}
        <div className="rounded-lg bg-emerald-950/20 border border-emerald-500/30 p-3.5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Read-Only Trust Boundary Enforced</span>
          </div>
          <div className="text-[11px] text-slate-300 font-mono space-y-1 pl-6">
            <div>✓ Zero mutating AWS SDK calls in codebase (AST verified)</div>
            <div>✓ Temporary in-memory credentials; 0 secrets stored</div>
            <div>✓ Financial data strictly decoupled from hardware telemetry</div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2 border-t border-[#1E2638]">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md bg-atlas-elevated hover:bg-atlas-surface border border-atlas-border text-xs font-medium text-atlas-text transition-colors"
          >
            Close Status
          </button>
        </div>
      </div>
    </div>
  );
};

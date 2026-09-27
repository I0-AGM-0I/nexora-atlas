import React from 'react';
import { ClipboardList, ShieldCheck, ArrowRight, Activity, RotateCcw, AlertCircle } from 'lucide-react';

export interface ImplementationConsiderationsProps {
  currentConfig?: string;
  proposedConfig?: string;
  className?: string;
}

export const ImplementationConsiderations: React.FC<ImplementationConsiderationsProps> = ({
  currentConfig = 'm5.4xlarge (16 vCPU, 64 GB)',
  proposedConfig = 'm5.large (2 vCPU, 8 GB)',
  className = '',
}) => {
  const steps = [
    {
      phase: 'PRE-CHANGE',
      title: 'Workload & Telemetry Validation',
      icon: <ShieldCheck className="w-4 h-4 text-sky-400" />,
      items: [
        'Validate workload compatibility against proposed vCPU / memory thresholds.',
        'Confirm current CloudWatch telemetry coverage and agent health on target instance.',
        'Verify zero active dependency blockers or concurrent release freezes.',
        'Confirm existence of recent snapshot or AMI backup before maintenance window.',
      ],
    },
    {
      phase: 'CHANGE',
      title: 'Configuration Transition',
      icon: <ArrowRight className="w-4 h-4 text-emerald-400" />,
      items: [
        `Drain active requests or step down cluster replica before instance stop.`,
        `Modify instance attribute from ${currentConfig} to ${proposedConfig}.`,
        'Preserve Elastic IP attachments, security groups, and root EBS volume bindings.',
        'Restart instance and verify hypervisor initialization state.',
      ],
    },
    {
      phase: 'POST-CHANGE',
      title: 'Health & Cost Trajectory Verification',
      icon: <Activity className="w-4 h-4 text-amber-400" />,
      items: [
        'Monitor CPU and memory utilization at 5-minute intervals for first 4 hours.',
        'Compare application P95 request latency against 14-day pre-change baseline.',
        'Verify target cost trajectory reflects lower run rate in subsequent billing records.',
        'Ensure error rate (HTTP 5xx) remains within normal operational bounds (< 0.05%).',
      ],
    },
    {
      phase: 'ROLLBACK',
      title: 'Contingency Reversal Procedure',
      icon: <RotateCcw className="w-4 h-4 text-rose-400" />,
      items: [
        `If P95 CPU exceeds 75% or memory pressure triggers, initiate rollback.`,
        `Revert instance type back to ${currentConfig}.`,
        'Re-attach original volume attachments if modified.',
        'Estimated restoration duration: < 5 minutes with minimal service interruption.',
      ],
    },
  ];

  return (
    <div className={`rounded-lg border border-[#1E2638] bg-[#0F141C] p-4 space-y-4 select-none ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E2638]/70 pb-3">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
            Implementation Considerations
          </h4>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 bg-[#141B27] px-2 py-0.5 rounded border border-[#1E2638]">
          <AlertCircle className="w-3 h-3 text-sky-400" />
          <span>READ-ONLY DECISION GUIDANCE · NON-EXECUTABLE</span>
        </div>
      </div>

      <p className="text-[11px] font-mono text-atlas-muted leading-relaxed">
        Engineering considerations for operational planning. Operational execution occurs via standard CI/CD, Terraform, or AWS pipelines outside Atlas.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
        {steps.map((s, idx) => (
          <div
            key={idx}
            className="bg-[#141B27]/50 rounded p-3 border border-[#1E2638]/70 flex flex-col justify-between space-y-2.5"
          >
            <div>
              <div className="flex items-center justify-between border-b border-[#1E2638]/50 pb-2">
                <div className="flex items-center gap-2">
                  {s.icon}
                  <span className="text-[11px] font-mono font-bold text-slate-200">
                    {s.title}
                  </span>
                </div>
                <span className="text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded bg-[#0B0F17] text-slate-400 border border-[#1E2638]">
                  {s.phase}
                </span>
              </div>

              <ul className="mt-2.5 space-y-1.5 text-[11px] font-mono text-slate-300">
                {s.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start gap-2 leading-relaxed">
                    <span className="text-slate-500 select-none">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

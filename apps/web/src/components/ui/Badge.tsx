import React from 'react';

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'critical'
  | 'info'
  | 'outline'
  | 'observed'
  | 'derived'
  | 'inferred'
  | 'assumed'
  | 'projected'
  | 'spike'
  | 'recovery'
  | 'elevated'
  | 'normal';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
}) => {
  const sizeStyles = {
    xs: 'text-[9px] px-1.5 py-0.2 font-mono font-semibold',
    sm: 'text-[10px] px-2 py-0.5 font-mono font-medium',
    md: 'text-xs px-2.5 py-1 font-mono font-medium',
  };

  const variantStyles: Record<BadgeVariant, string> = {
    default: 'bg-atlas-elevated text-atlas-secondary border border-atlas-border',
    success: 'bg-emerald-400/10 text-emerald-400 border border-emerald-400/30',
    warning: 'bg-amber-400/10 text-amber-400 border border-amber-400/30',
    critical: 'bg-rose-500/10 text-rose-400 border border-rose-500/30',
    info: 'bg-sky-400/10 text-sky-400 border border-sky-400/30',
    outline: 'border border-atlas-border text-atlas-secondary bg-transparent',

    // Epistemic Classification Badges (Restrained palette)
    observed: 'bg-[#1E293B] text-[#94A3B8] border border-[#334155]',
    derived: 'bg-[#0C2A4A] text-[#7DD3FC] border border-[#0284C7]/40',
    inferred: 'bg-[#3D2206] text-[#FCD34D] border border-[#D97706]/40',
    assumed: 'bg-[#281347] text-[#C4B5FD] border border-[#7C3AED]/40',
    projected: 'bg-[#082F49] text-[#38BDF8] border border-[#0284C7]',

    // Spend Behavioral Regimes
    spike: 'bg-rose-950/40 text-rose-400 border border-rose-500/40',
    recovery: 'bg-sky-950/40 text-sky-300 border border-sky-500/40',
    elevated: 'bg-amber-950/40 text-amber-400 border border-amber-500/40',
    normal: 'bg-emerald-950/30 text-emerald-400 border border-emerald-500/30',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded tracking-wide uppercase ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

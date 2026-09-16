import React from 'react';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'critical' | 'info' | 'outline';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 font-mono font-medium',
    md: 'text-xs px-2.5 py-1 font-mono font-medium',
  };

  const variantStyles = {
    default: 'bg-atlas-elevated text-atlas-secondary border border-atlas-border',
    success: 'bg-atlas-success/15 text-atlas-success border border-atlas-success/30',
    warning: 'bg-atlas-warning/15 text-atlas-warning border border-atlas-warning/30',
    critical: 'bg-atlas-critical/15 text-atlas-critical border border-atlas-critical/30',
    info: 'bg-atlas-primary/15 text-atlas-primary border border-atlas-primary/30',
    outline: 'border border-atlas-border text-atlas-secondary bg-transparent',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded tracking-wide uppercase ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

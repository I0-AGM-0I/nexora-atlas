import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-atlas-primary disabled:opacity-50 disabled:pointer-events-none rounded-md select-none';

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-sm px-3.5 py-2 gap-2',
    lg: 'text-base px-4 py-2.5 gap-2.5',
  };

  const variantStyles = {
    primary: 'bg-atlas-primary text-atlas-bg hover:bg-sky-400 font-semibold shadow-subtle',
    secondary: 'bg-atlas-elevated text-atlas-text border border-atlas-border hover:bg-slate-800',
    outline: 'border border-atlas-border text-atlas-secondary hover:text-atlas-text hover:bg-atlas-surface',
    ghost: 'text-atlas-secondary hover:text-atlas-text hover:bg-atlas-surface',
    danger: 'bg-atlas-critical/20 text-atlas-critical border border-atlas-critical/40 hover:bg-atlas-critical/30',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

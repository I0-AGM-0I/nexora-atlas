import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  elevated?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  elevated = false,
  ...props
}) => {
  return (
    <div
      className={`rounded-lg border border-atlas-border ${
        elevated ? 'bg-atlas-elevated' : 'bg-atlas-surface'
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

import React from 'react';
import { Inbox, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ComponentType<{ className?: string }>;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  message,
  actionLabel,
  onAction,
  icon: Icon = Inbox,
}) => {
  return (
    <div className="py-12 px-6 flex flex-col items-center justify-center text-center rounded-lg border border-dashed border-atlas-border bg-atlas-surface/40">
      <div className="w-10 h-10 rounded-full bg-atlas-elevated border border-atlas-border flex items-center justify-center text-atlas-muted mb-3">
        <Icon className="w-5 h-5" />
      </div>
      <h4 className="text-sm font-semibold text-atlas-text mb-1">{title}</h4>
      <p className="text-xs text-atlas-secondary max-w-sm mb-4">{message}</p>
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction}>
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

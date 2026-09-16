import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './ui/Button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'System Encountered an Issue',
  message = 'Unable to load resources. Verify network status and server availability.',
  onRetry,
  className = '',
}) => {
  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-atlas-critical/30 bg-atlas-surface/60 ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-atlas-critical/15 text-atlas-critical flex items-center justify-center mb-4">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-atlas-text mb-1">{title}</h3>
      <p className="text-sm text-atlas-secondary max-w-md mb-6">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={<RefreshCw className="w-4 h-4" />} onClick={onRetry}>
          Retry Connection
        </Button>
      )}
    </div>
  );
};

import React from 'react';
import { Badge, BadgeVariant } from './Badge';

export type EpistemicClassification =
  | 'OBSERVED'
  | 'DERIVED'
  | 'INFERRED'
  | 'ASSUMED'
  | 'PROJECTED'
  | 'NOT_AVAILABLE';

interface EpistemicBadgeProps {
  classification: EpistemicClassification | string;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

export const EpistemicBadge: React.FC<EpistemicBadgeProps> = ({
  classification,
  size = 'xs',
  className = '',
}) => {
  const norm = classification.toUpperCase() as EpistemicClassification;

  const variantMap: Record<EpistemicClassification, BadgeVariant> = {
    OBSERVED: 'observed',
    DERIVED: 'derived',
    INFERRED: 'inferred',
    ASSUMED: 'assumed',
    PROJECTED: 'projected',
    NOT_AVAILABLE: 'outline',
  };

  const variant = variantMap[norm] || 'default';

  return (
    <Badge variant={variant} size={size} className={className}>
      {norm.replace('_', ' ')}
    </Badge>
  );
};

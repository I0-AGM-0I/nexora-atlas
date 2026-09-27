import React from 'react';

interface AtlasMarkProps {
  size?: number;
  className?: string;
  active?: boolean;
}

/**
 * AtlasMark - Technical geometric coordinate compass glyph.
 * Restrained, analytical mark symbolizing spatial/coordinate intelligence.
 */
export const AtlasMark: React.FC<AtlasMarkProps> = ({
  size = 28,
  className = '',
  active = false,
}) => {
  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${className}`}
      style={{ width: size, height: size }}
      aria-label="Atlas Mark"
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="transition-transform duration-200"
      >
        {/* Outer reticle circle */}
        <circle
          cx="16"
          cy="16"
          r="10"
          stroke={active ? '#38BDF8' : '#475569'}
          strokeWidth="1.2"
          strokeDasharray="2 3"
          className="transition-colors duration-200"
        />

        {/* Inner core circle */}
        <circle
          cx="16"
          cy="16"
          r="4.5"
          stroke={active ? '#0EA5E9' : '#64748B'}
          strokeWidth="1.2"
          className="transition-colors duration-200"
        />

        {/* Center coordinate dot */}
        <circle
          cx="16"
          cy="16"
          r="1.5"
          fill={active ? '#38BDF8' : '#94A3B8'}
        />

        {/* Coordinate crosshair lines */}
        {/* Top tick */}
        <line
          x1="16"
          y1="2"
          x2="16"
          y2="6"
          stroke={active ? '#0EA5E9' : '#475569'}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        {/* Bottom tick */}
        <line
          x1="16"
          y1="26"
          x2="16"
          y2="30"
          stroke={active ? '#0EA5E9' : '#475569'}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        {/* Left tick */}
        <line
          x1="2"
          y1="16"
          x2="6"
          y2="16"
          stroke={active ? '#0EA5E9' : '#475569'}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        {/* Right tick */}
        <line
          x1="26"
          y1="16"
          x2="30"
          y2="16"
          stroke={active ? '#0EA5E9' : '#475569'}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
};

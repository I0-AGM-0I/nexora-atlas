import React, { useState, useMemo, useRef } from 'react';
import { SpendTrendPoint } from '../../types/api';
import { formatCurrency, formatDate, parseNumber } from '../../lib/format';
import { Zap } from 'lucide-react';

interface SpendTrendChartProps {
  points: SpendTrendPoint[];
  currency?: string;
  height?: number;
}

export const SpendTrendChart: React.FC<SpendTrendChartProps> = ({
  points,
  currency = 'INR',
  height = 280,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const viewBoxWidth = 860;
  const viewBoxHeight = height;
  const padLeft = 65;
  const padRight = 20;
  const padTop = 25;
  const padBottom = 35;

  const chartWidth = viewBoxWidth - padLeft - padRight;
  const chartHeight = viewBoxHeight - padTop - padBottom;

  const { coords, xLabels, yGridLines } = useMemo(() => {
    if (!points || points.length === 0) {
      return { coords: [], xLabels: [], yGridLines: [] };
    }

    const spends = points.map((p) => parseNumber(p.spend));
    const rawMax = Math.max(...spends, 1000);
    // Add 15% head room for markers & tooltips
    const maxVal = Math.ceil(rawMax * 1.15);

    const stepX = chartWidth / Math.max(1, points.length - 1);

    const mappedCoords = points.map((p, idx) => {
      const val = parseNumber(p.spend);
      const x = padLeft + idx * stepX;
      const y = padTop + chartHeight - (val / maxVal) * chartHeight;
      return { x, y, point: p, val };
    });

    // Generate 5 Y-axis grid ticks
    const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
      const val = maxVal * ratio;
      const y = padTop + chartHeight - ratio * chartHeight;
      return { val, y };
    });

    // Generate ~6 evenly spaced X-axis labels
    const labelStep = Math.max(1, Math.floor((points.length - 1) / 5));
    const xTicks = [];
    for (let i = 0; i < points.length; i += labelStep) {
      xTicks.push({
        idx: i,
        x: padLeft + i * stepX,
        date: points[i].date,
      });
    }
    // Ensure last point is included if not close
    const lastIdx = points.length - 1;
    if (xTicks[xTicks.length - 1]?.idx !== lastIdx) {
      xTicks.push({
        idx: lastIdx,
        x: padLeft + lastIdx * stepX,
        date: points[lastIdx].date,
      });
    }

    return {
      maxSpend: maxVal,
      coords: mappedCoords,
      xLabels: xTicks,
      yGridLines: yTicks,
    };
  }, [points, chartWidth, chartHeight, padLeft, padTop]);

  if (!points || points.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-atlas-muted font-mono">
        No spend trend data available
      </div>
    );
  }

  // Create SVG path strings
  const polylinePoints = coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ');
  const areaPolygonPoints = `${padLeft},${padTop + chartHeight} ${polylinePoints} ${
    coords[coords.length - 1]?.x.toFixed(1) || padLeft
  },${padTop + chartHeight}`;

  const activeCoord = hoverIndex !== null ? coords[hoverIndex] : null;

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!containerRef.current || coords.length === 0) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const scale = viewBoxWidth / rect.width;
    const svgX = clientX * scale;

    // Find nearest point
    let nearestIdx = 0;
    let minDist = Infinity;
    for (let i = 0; i < coords.length; i++) {
      const dist = Math.abs(coords[i].x - svgX);
      if (dist < minDist) {
        minDist = dist;
        nearestIdx = i;
      }
    }
    setHoverIndex(nearestIdx);
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
  };

  return (
    <div className="relative w-full select-none" ref={containerRef}>
      <svg
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        className="w-full h-auto overflow-visible cursor-crosshair"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        aria-label="Spend trend 90-day interactive area chart"
        role="img"
      >
        <defs>
          <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.28" />
            <stop offset="85%" stopColor="#38BDF8" stopOpacity="0.02" />
            <stop offset="100%" stopColor="#38BDF8" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Y Gridlines & Labels */}
        {yGridLines.map((grid, i) => (
          <g key={i}>
            <line
              x1={padLeft}
              y1={grid.y}
              x2={viewBoxWidth - padRight}
              y2={grid.y}
              stroke="#1E293B"
              strokeDasharray={i === 0 ? undefined : '2 4'}
              strokeWidth="1"
            />
            <text
              x={padLeft - 10}
              y={grid.y + 3.5}
              textAnchor="end"
              className="text-[10px] font-mono fill-slate-500 select-none"
            >
              {formatCurrency(grid.val, currency, true)}
            </text>
          </g>
        ))}

        {/* Area fill */}
        <polygon points={areaPolygonPoints} fill="url(#spendGradient)" />

        {/* Primary curve */}
        <polyline
          points={polylinePoints}
          fill="none"
          stroke="#38BDF8"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Event Marker Pins */}
        {coords.map((c, i) => {
          if (!c.point.events || c.point.events.length === 0) return null;
          const ev = c.point.events[0];
          const isIncident = ev.category === 'INCIDENT';
          const markerColor = isIncident ? '#EF4444' : '#F59E0B';

          return (
            <g key={`evt-${i}`} className="cursor-pointer">
              {/* Event vertical guideline */}
              <line
                x1={c.x}
                y1={c.y}
                x2={c.x}
                y2={padTop + chartHeight}
                stroke={markerColor}
                strokeWidth="1"
                strokeDasharray="2 3"
                opacity="0.6"
              />
              {/* Pulse circle */}
              <circle cx={c.x} cy={c.y} r="6" fill={markerColor} fillOpacity="0.2" />
              <circle cx={c.x} cy={c.y} r="3.5" fill={markerColor} stroke="#080B10" strokeWidth="1.5" />
            </g>
          );
        })}

        {/* X Axis Date Labels */}
        {xLabels.map((tick, i) => (
          <text
            key={i}
            x={tick.x}
            y={viewBoxHeight - 10}
            textAnchor="middle"
            className="text-[10px] font-mono fill-slate-500 select-none"
          >
            {formatDate(tick.date, 'short')}
          </text>
        ))}

        {/* Active Hover Crosshair Line & Point */}
        {activeCoord && (
          <g>
            <line
              x1={activeCoord.x}
              y1={padTop}
              x2={activeCoord.x}
              y2={padTop + chartHeight}
              stroke="#64748B"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
            <circle
              cx={activeCoord.x}
              cy={activeCoord.y}
              r="4.5"
              fill="#38BDF8"
              stroke="#080B10"
              strokeWidth="2"
            />
          </g>
        )}
      </svg>

      {/* Interactive Tooltip Card */}
      {activeCoord && (
        <div
          className="absolute pointer-events-none z-20 transition-all duration-75"
          style={{
            left: `${(activeCoord.x / viewBoxWidth) * 100}%`,
            top: `${Math.max(10, (activeCoord.y / viewBoxHeight) * 100 - 30)}%`,
            transform: `translate(${activeCoord.x > viewBoxWidth * 0.7 ? '-105%' : '15px'}, -50%)`,
          }}
        >
          <div className="bg-[#0E131F]/95 backdrop-blur border border-atlas-border rounded-md p-3 shadow-2xl min-w-[190px] text-xs space-y-1.5 font-sans">
            <div className="flex items-center justify-between border-b border-atlas-border pb-1.5 text-atlas-muted">
              <span className="font-mono text-[11px]">{formatDate(activeCoord.point.date, 'medium')}</span>
              <span className="text-[10px] text-atlas-secondary uppercase font-mono">Day {(hoverIndex ?? 0) + 1}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-atlas-secondary">Daily Spend:</span>
              <span className="font-mono font-semibold text-atlas-text text-sm">
                {formatCurrency(activeCoord.point.spend, currency)}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-atlas-muted">Cumulative:</span>
              <span className="font-mono text-atlas-secondary">
                {formatCurrency(activeCoord.point.cumulative_spend, currency, true)}
              </span>
            </div>

            {/* Embedded Events in Tooltip */}
            {activeCoord.point.events && activeCoord.point.events.length > 0 && (
              <div className="mt-2 pt-2 border-t border-atlas-border space-y-1">
                {activeCoord.point.events.map((ev) => (
                  <div key={ev.id} className="bg-atlas-elevated/80 p-2 rounded border border-amber-500/30 text-[11px]">
                    <div className="flex items-center gap-1.5 font-medium text-amber-400 mb-0.5">
                      <Zap className="w-3 h-3 flex-shrink-0" />
                      <span>{ev.title}</span>
                    </div>
                    <p className="text-[10px] text-slate-300 leading-tight">{ev.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

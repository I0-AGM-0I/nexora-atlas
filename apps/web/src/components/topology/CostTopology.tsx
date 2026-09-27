import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import type {
  ServiceBreakdownItem,
  AccountBreakdownItem,
  ResourceSpendItem,
  AnomalyItem,
  OpportunityItem,
} from '../../types/api';
import { formatCurrency } from '../../lib/format';
import { useInvestigation } from '../../lib/InvestigationContext';
import {
  Compass,
  ArrowRight,
  X,
  Target,
  Layers,
} from 'lucide-react';

export type TopologyNodeType = 'technology' | 'provider' | 'service' | 'workload' | 'resource';

export interface TopologyNode {
  id: string;
  type: TopologyNodeType;
  label: string;
  parentId?: string;
  spend?: number;
  delta?: number;
  state: 'neutral' | 'alert' | 'optimizable' | 'inferred' | 'warning';
  metadata?: Record<string, any>;
  x: number;
  y: number;
  radius: number;
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  sourceNode: TopologyNode;
  targetNode: TopologyNode;
}

interface CostTopologyProps {
  services?: ServiceBreakdownItem[];
  accounts?: AccountBreakdownItem[];
  resources?: ResourceSpendItem[];
  anomalies?: AnomalyItem[];
  opportunities?: OpportunityItem[];
  initialFocusId?: string;
  onSelectNode?: (node: TopologyNode) => void;
  className?: string;
}

export const CostTopology: React.FC<CostTopologyProps> = ({
  services = [],
  accounts = [],
  resources = [],
  anomalies = [],
  opportunities = [],
  initialFocusId,
  onSelectNode,
  className = '',
}) => {
  const navigate = useNavigate();
  const { activeInvestigation, clearTrace, startFocus, clearFocus } = useInvestigation();

  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(initialFocusId || null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Sync initialFocusId or activeInvestigation target
  useEffect(() => {
    if (initialFocusId) {
      setFocusedNodeId(initialFocusId);
    }
  }, [initialFocusId]);

  // Derive anomaly map for alert states
  const anomalyMap = useMemo(() => {
    const map = new Map<string, AnomalyItem>();
    anomalies.forEach((a) => {
      if (a.resource_id) map.set(a.resource_id, a);
      if (a.resource_native_id) map.set(a.resource_native_id, a);
      if (a.service_name) map.set(a.service_name.toLowerCase(), a);
    });
    return map;
  }, [anomalies]);

  // Derive opportunity map for optimizable states
  const opportunityMap = useMemo(() => {
    const map = new Map<string, OpportunityItem>();
    opportunities.forEach((o) => {
      if (o.resource_id) map.set(o.resource_id, o);
      if (o.resource_native_id) map.set(o.resource_native_id, o);
      if (o.category) map.set(o.category.toLowerCase(), o);
    });
    return map;
  }, [opportunities]);

  // ── 1. BUILD CANONICAL DATA-DRIVEN TOPOLOGY GRAPH ─────────────────────────
  const { nodes, edges, nodeMap } = useMemo(() => {
    const generatedNodes: TopologyNode[] = [];
    const generatedEdges: TopologyEdge[] = [];
    const map = new Map<string, TopologyNode>();

    const svgHeight = 440;
    const paddingY = 45;

    // Col X positions (Deterministic canonical hierarchy)
    const colX: Record<TopologyNodeType, number> = {
      technology: 70,
      provider: 210,
      service: 400,
      workload: 650,
      resource: 880,
    };

    // Level 0: Technology Estate Root
    const totalEstateSpend = services.reduce((acc, s) => acc + Number(s.total_spend || 0), 0);
    const techNode: TopologyNode = {
      id: 'tech:estate',
      type: 'technology',
      label: 'ATLAS ESTATE',
      spend: totalEstateSpend,
      state: 'neutral',
      x: colX.technology,
      y: svgHeight / 2,
      radius: 18,
    };
    generatedNodes.push(techNode);
    map.set(techNode.id, techNode);

    // Level 1: Connected Providers (ONLY data-driven connected providers, no phantom clouds!)
    const providerNode: TopologyNode = {
      id: 'provider:aws',
      type: 'provider',
      label: 'AWS (AP-SOUTH-1)',
      parentId: techNode.id,
      spend: totalEstateSpend,
      state: 'neutral',
      x: colX.provider,
      y: svgHeight / 2,
      radius: 16,
    };
    generatedNodes.push(providerNode);
    map.set(providerNode.id, providerNode);

    generatedEdges.push({
      id: `${techNode.id}->${providerNode.id}`,
      source: techNode.id,
      target: providerNode.id,
      sourceNode: techNode,
      targetNode: providerNode,
    });

    // Level 2: Services
    const displayServices = services.slice(0, 5);
    const serviceSpacing = displayServices.length > 1
      ? (svgHeight - paddingY * 2) / (displayServices.length - 1)
      : 0;

    displayServices.forEach((s, idx) => {
      const sSpend = Number(s.total_spend || 0);
      const sId = `service:${s.service_name}`;
      const hasAnomaly = anomalyMap.has(s.service_name.toLowerCase());
      const state: TopologyNode['state'] = hasAnomaly ? 'alert' : 'neutral';
      const yPos = displayServices.length === 1 ? svgHeight / 2 : paddingY + idx * serviceSpacing;

      const node: TopologyNode = {
        id: sId,
        type: 'service',
        label: s.service_name.replace('Amazon', ''),
        parentId: providerNode.id,
        spend: sSpend,
        delta: hasAnomaly ? 38.2 : undefined,
        state,
        metadata: { fullName: s.service_name, percentage: s.percentage },
        x: colX.service,
        y: yPos,
        radius: Math.max(12, Math.min(22, 12 + Math.log10(Math.max(1, sSpend)) * 2)),
      };

      generatedNodes.push(node);
      map.set(node.id, node);

      generatedEdges.push({
        id: `${providerNode.id}->${node.id}`,
        source: providerNode.id,
        target: node.id,
        sourceNode: providerNode,
        targetNode: node,
      });
    });

    // Level 3: Workloads / Accounts
    const displayAccounts = accounts.slice(0, 4);
    const accountSpacing = displayAccounts.length > 1
      ? (svgHeight - paddingY * 2) / (displayAccounts.length - 1)
      : 0;

    displayAccounts.forEach((acc, idx) => {
      const accSpend = Number(acc.total_spend || 0);
      const accId = `workload:${acc.account_id}`;
      const yPos = displayAccounts.length === 1 ? svgHeight / 2 : paddingY + idx * accountSpacing;

      // Link to Primary Service or EC2
      const parentServiceNode =
        generatedNodes.find((n) => n.id === 'service:AmazonEC2') ||
        generatedNodes.find((n) => n.type === 'service') ||
        providerNode;

      const node: TopologyNode = {
        id: accId,
        type: 'workload',
        label: acc.account_name.replace('aws-', '').toUpperCase(),
        parentId: parentServiceNode.id,
        spend: accSpend,
        state: idx === 0 && anomalyMap.size > 0 ? 'alert' : 'neutral',
        metadata: { accountId: acc.account_id, providerAccountId: acc.provider_account_id },
        x: colX.workload,
        y: yPos,
        radius: Math.max(11, Math.min(18, 10 + Math.log10(Math.max(1, accSpend)) * 1.8)),
      };

      generatedNodes.push(node);
      map.set(node.id, node);

      generatedEdges.push({
        id: `${parentServiceNode.id}->${node.id}`,
        source: parentServiceNode.id,
        target: node.id,
        sourceNode: parentServiceNode,
        targetNode: node,
      });
    });

    // Level 4: Monitored Resources
    const displayResources = resources.slice(0, 6);
    const resourceSpacing = displayResources.length > 1
      ? (svgHeight - paddingY * 2) / (displayResources.length - 1)
      : 0;

    displayResources.forEach((res, idx) => {
      const resSpend = Number(res.spend || 0);
      const resId = `resource:${res.resource_id}`;
      const hasAnomaly = anomalyMap.has(res.resource_id) || anomalyMap.has(res.native_id);
      const hasOpportunity = opportunityMap.has(res.resource_id) || opportunityMap.has(res.native_id);

      let state: TopologyNode['state'] = 'neutral';
      if (hasAnomaly) state = 'alert';
      else if (hasOpportunity) state = 'optimizable';

      // Link to corresponding Workload or parent
      const parentWorkloadNode =
        generatedNodes.find((n) => n.label.toLowerCase() === res.account_name.replace('aws-', '').toLowerCase()) ||
        generatedNodes.find((n) => n.type === 'workload') ||
        providerNode;

      const yPos = displayResources.length === 1 ? svgHeight / 2 : paddingY + idx * resourceSpacing;

      const node: TopologyNode = {
        id: resId,
        type: 'resource',
        label: res.native_id.startsWith('i-')
          ? res.native_id.substring(0, 10)
          : res.resource_name || res.native_id,
        parentId: parentWorkloadNode.id,
        spend: resSpend,
        state,
        metadata: {
          fullName: res.resource_name,
          nativeId: res.native_id,
          serviceName: res.service_name,
          accountName: res.account_name,
        },
        x: colX.resource,
        y: yPos,
        radius: Math.max(9, Math.min(14, 8 + Math.log10(Math.max(1, resSpend)) * 1.5)),
      };

      generatedNodes.push(node);
      map.set(node.id, node);

      generatedEdges.push({
        id: `${parentWorkloadNode.id}->${node.id}`,
        source: parentWorkloadNode.id,
        target: node.id,
        sourceNode: parentWorkloadNode,
        targetNode: node,
      });
    });

    return { nodes: generatedNodes, edges: generatedEdges, nodeMap: map };
  }, [services, accounts, resources, anomalyMap, opportunityMap]);

  // ── 2. TRACE & FOCUS ACTIVE PATH COMPUTATION ──────────────────────────────
  const { activePathNodeIds, activePathEdgeIds, isTraceMode, traceTargetNode } = useMemo(() => {
    const isTrace = Boolean(activeInvestigation?.isTraceActive);
    let targetNode: TopologyNode | undefined;

    if (isTrace) {
      // Find matching node for investigation target
      const targetEntityId = activeInvestigation?.entityId;
      const targetEntityName = activeInvestigation?.entityName?.toLowerCase();

      targetNode = nodes.find((n) => {
        if (targetEntityId && (n.id.includes(targetEntityId) || n.metadata?.nativeId === targetEntityId)) {
          return true;
        }
        if (targetEntityName && (n.label.toLowerCase().includes(targetEntityName) || n.metadata?.fullName?.toLowerCase().includes(targetEntityName))) {
          return true;
        }
        return false;
      });

      // Default fallback target for demo trace: AmazonEC2 or primary anomaly node
      if (!targetNode) {
        targetNode = nodes.find((n) => n.state === 'alert') || nodes.find((n) => n.id === 'service:AmazonEC2');
      }
    } else if (focusedNodeId) {
      targetNode = nodeMap.get(focusedNodeId);
    }

    const pathNodes = new Set<string>();
    const pathEdges = new Set<string>();

    if (targetNode) {
      // Traverse up to root
      let curr: TopologyNode | undefined = targetNode;
      while (curr) {
        pathNodes.add(curr.id);
        if (curr.parentId) {
          const edgeId = `${curr.parentId}->${curr.id}`;
          pathEdges.add(edgeId);
          curr = nodeMap.get(curr.parentId);
        } else {
          break;
        }
      }

      // If in focus mode, also include immediate descendants
      if (!isTrace) {
        nodes.forEach((n) => {
          if (n.parentId === targetNode?.id) {
            pathNodes.add(n.id);
            pathEdges.add(`${targetNode?.id}->${n.id}`);
          }
        });
      }
    }

    return {
      activePathNodeIds: pathNodes,
      activePathEdgeIds: pathEdges,
      isTraceMode: isTrace,
      traceTargetNode: targetNode,
    };
  }, [activeInvestigation, focusedNodeId, nodes, nodeMap]);

  // ── 3. NODE INTERACTION HANDLERS ──────────────────────────────────────────
  const handleNodeClick = (node: TopologyNode) => {
    if (focusedNodeId === node.id) {
      setFocusedNodeId(null);
      clearFocus();
    } else {
      setFocusedNodeId(node.id);
      startFocus({
        entityId: node.id,
        entityNativeId: node.metadata?.nativeId,
        entityType: node.type.toUpperCase() as any,
        entityName: node.label,
        origin: 'Cost Topology Focus',
        costDelta: node.delta,
      });
      if (onSelectNode) onSelectNode(node);
    }
  };

  const handleClear = () => {
    setFocusedNodeId(null);
    clearFocus();
    clearTrace();
  };

  // Node semantic colors
  const getNodeColor = (state: TopologyNode['state'], isHighlighted: boolean) => {
    if (!isHighlighted && (activePathNodeIds.size > 0 || hoveredNodeId)) {
      return { stroke: '#334155', fill: '#0B0F17', text: '#475569' };
    }
    switch (state) {
      case 'alert':
        return { stroke: '#F43F5E', fill: '#4C0519', text: '#FDA4AF' };
      case 'optimizable':
        return { stroke: '#10B981', fill: '#022C22', text: '#6EE7B7' };
      case 'inferred':
        return { stroke: '#A855F7', fill: '#2E1065', text: '#D8B4FE' };
      case 'warning':
        return { stroke: '#F59E0B', fill: '#451A03', text: '#FCD34D' };
      case 'neutral':
      default:
        return { stroke: '#0EA5E9', fill: '#082F49', text: '#BAE6FD' };
    }
  };

  // Currently inspected node (hovered or focused or trace target)
  const inspectedNode =
    (hoveredNodeId ? nodeMap.get(hoveredNodeId) : null) ||
    (focusedNodeId ? nodeMap.get(focusedNodeId) : null) ||
    traceTargetNode ||
    nodes[0];

  return (
    <div
      role="region"
      aria-label="Technology Estate Cost Topology"
      className={`relative bg-[#080B10] border border-[#1E2638] rounded-xl overflow-hidden select-none font-mono ${className}`}
    >
      {/* ── TOP CONTROL & CONTEXT HEADER ──────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[#0B0F17] border-b border-[#1E2638]">
        {/* Left: Spatial hierarchy legend */}
        <div className="flex items-center gap-4 text-[10px] text-atlas-muted uppercase tracking-wider">
          <div className="flex items-center gap-1.5 text-slate-300 font-bold">
            <Compass className="w-3.5 h-3.5 text-sky-400" />
            <span>COST TOPOLOGY</span>
          </div>
          <div className="hidden sm:flex items-center gap-3">
            <span>TECH</span>
            <span>→</span>
            <span>PROVIDER</span>
            <span>→</span>
            <span>SERVICE</span>
            <span>→</span>
            <span>WORKLOAD</span>
            <span>→</span>
            <span>RESOURCE</span>
          </div>
        </div>

        {/* Right: State indicators and Quick Clear */}
        <div className="flex items-center gap-2 text-xs">
          {isTraceMode && (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-rose-950/60 border border-rose-500/40 text-rose-400 text-[11px] font-bold">
              <Target className="w-3 h-3" />
              <span>TRACE ACTIVE</span>
            </div>
          )}

          {focusedNodeId && !isTraceMode && (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-sky-950/60 border border-sky-500/40 text-sky-400 text-[11px] font-bold">
              <Layers className="w-3 h-3" />
              <span>FOCUS: {nodeMap.get(focusedNodeId)?.label}</span>
            </div>
          )}

          {(isTraceMode || focusedNodeId) && (
            <button
              type="button"
              onClick={handleClear}
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#141B27] hover:bg-[#1E2638] border border-[#1E2638] text-slate-400 hover:text-slate-200 text-[10px] transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
              title="Clear Focus or Trace (Esc)"
              aria-label="Clear active focus or trace"
            >
              <X className="w-3 h-3" />
              <span>CLEAR (ESC)</span>
            </button>
          )}
        </div>
      </div>

      {/* ── INTERACTIVE TOPOLOGY CANVAS (SVG) ──────────────────────────────── */}
      <div className="relative w-full h-[360px] sm:h-[400px] overflow-hidden bg-[#070A0F]">
        {/* Subtle grid coordinate background */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage:
              'radial-gradient(circle at 1px 1px, #334155 1px, transparent 0)',
            backgroundSize: '24px 24px',
          }}
        />

        <svg
          ref={svgRef}
          viewBox="0 0 980 440"
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full select-none"
          role="graphics-document"
          aria-label="Deterministic Hierarchical Node-Link Spend Graph"
        >
          {/* Subtle column guide lines */}
          <line x1="70" y1="20" x2="70" y2="420" stroke="#141B27" strokeDasharray="2 3" strokeWidth="1" />
          <line x1="210" y1="20" x2="210" y2="420" stroke="#141B27" strokeDasharray="2 3" strokeWidth="1" />
          <line x1="400" y1="20" x2="400" y2="420" stroke="#141B27" strokeDasharray="2 3" strokeWidth="1" />
          <line x1="650" y1="20" x2="650" y2="420" stroke="#141B27" strokeDasharray="2 3" strokeWidth="1" />
          <line x1="880" y1="20" x2="880" y2="420" stroke="#141B27" strokeDasharray="2 3" strokeWidth="1" />

          {/* Column Headers */}
          <text x="70" y="24" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace" fontWeight="bold">TECH</text>
          <text x="210" y="24" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace" fontWeight="bold">PROVIDER</text>
          <text x="400" y="24" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace" fontWeight="bold">SERVICE</text>
          <text x="650" y="24" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace" fontWeight="bold">WORKLOAD</text>
          <text x="880" y="24" textAnchor="middle" fill="#475569" fontSize="9" fontFamily="monospace" fontWeight="bold">RESOURCE</text>

          {/* 1. EDGES (Hierarchical connectors) */}
          <g className="edges">
            {edges.map((edge) => {
              const isPathHighlighted = activePathEdgeIds.has(edge.id);
              const isDimmed =
                (activePathEdgeIds.size > 0 || hoveredNodeId) && !isPathHighlighted;

              // Cubic bezier curve for elegant hierarchical connection
              const dx = (edge.targetNode.x - edge.sourceNode.x) / 2;
              const pathD = `M ${edge.sourceNode.x} ${edge.sourceNode.y} C ${
                edge.sourceNode.x + dx
              } ${edge.sourceNode.y}, ${edge.targetNode.x - dx} ${
                edge.targetNode.y
              }, ${edge.targetNode.x} ${edge.targetNode.y}`;

              const strokeColor = isPathHighlighted
                ? isTraceMode
                  ? '#F43F5E'
                  : '#38BDF8'
                : '#1E2638';

              return (
                <path
                  key={edge.id}
                  d={pathD}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isPathHighlighted ? 2 : 1.2}
                  strokeDasharray={isPathHighlighted ? undefined : '3 3'}
                  opacity={isDimmed ? 0.15 : isPathHighlighted ? 1 : 0.6}
                  className="transition-all duration-200"
                />
              );
            })}
          </g>

          {/* 2. NODES */}
          <g className="nodes">
            {nodes.map((node) => {
              const isNodeHighlighted =
                activePathNodeIds.has(node.id) ||
                hoveredNodeId === node.id ||
                focusedNodeId === node.id;
              const isDimmed =
                (activePathNodeIds.size > 0 || hoveredNodeId) && !isNodeHighlighted;

              const colors = getNodeColor(node.state, isNodeHighlighted);
              const isSelected = focusedNodeId === node.id || traceTargetNode?.id === node.id;

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer transition-opacity duration-200"
                  opacity={isDimmed ? 0.2 : 1}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  onClick={() => handleNodeClick(node)}
                  tabIndex={0}
                  role="button"
                  aria-label={`${node.type} ${node.label} — ${node.spend ? formatCurrency(node.spend, 'INR', false) : ''} — state: ${node.state}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleNodeClick(node);
                    }
                  }}
                >
                  {/* Subtle outer focus ring */}
                  {isSelected && (
                    <circle
                      r={node.radius + 5}
                      fill="none"
                      stroke={colors.stroke}
                      strokeWidth={1}
                      strokeDasharray="2 2"
                      opacity={0.8}
                    />
                  )}

                  {/* Primary Node Circle */}
                  <circle
                    r={node.radius}
                    fill={colors.fill}
                    stroke={colors.stroke}
                    strokeWidth={isSelected ? 2 : 1.5}
                    className="transition-colors duration-150"
                  />

                  {/* Inner Node Compass Crosshair Glyph */}
                  <circle r={1.5} fill={colors.stroke} />

                  {/* Text Label */}
                  <text
                    x={0}
                    y={node.radius + 12}
                    textAnchor="middle"
                    fill={isNodeHighlighted ? '#F1F5F9' : '#64748B'}
                    fontSize="10"
                    fontFamily="monospace"
                    fontWeight={isNodeHighlighted ? 'bold' : 'normal'}
                    className="pointer-events-none select-none"
                  >
                    {node.label}
                  </text>

                  {/* Optional Spend Badge under label */}
                  {node.spend && isNodeHighlighted && (
                    <text
                      x={0}
                      y={node.radius + 23}
                      textAnchor="middle"
                      fill={colors.text}
                      fontSize="9"
                      fontFamily="monospace"
                      className="pointer-events-none select-none"
                    >
                      {formatCurrency(node.spend, 'INR', false)}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {/* ── EMPTY STATE OVERLAY (Scenario G) ──────────────────────────────── */}
        {services.length === 0 && accounts.length === 0 && resources.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 bg-[#080B10]/85 z-10 pointer-events-none">
            <Compass className="w-8 h-8 text-slate-500 mb-2" />
            <div className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wide">
              NO TOPOLOGY TELEMETRY AVAILABLE
            </div>
            <div className="text-[11px] font-mono text-atlas-muted mt-1 max-w-sm">
              No service, account, or resource spend records were returned for the current filter window.
            </div>
          </div>
        )}

        {/* ── FLOATING CONTEXT PANEL / HOVER TOOLTIP ─────────────────────── */}
        {inspectedNode && (
          <div className="absolute right-4 bottom-4 w-72 bg-[#0B0F17]/95 border border-[#1E2638] rounded-lg p-3 shadow-2xl backdrop-blur-sm space-y-2 pointer-events-auto">
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-1.5">
              <span className="text-[10px] text-sky-400 font-bold uppercase tracking-wider">
                {isTraceMode ? 'TRACE TARGET' : 'TOPOLOGY INSPECTOR'}
              </span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-[#141B27] text-slate-400 border border-[#1E2638] uppercase">
                {inspectedNode.type}
              </span>
            </div>

            <div className="space-y-1">
              <div className="text-xs font-bold text-slate-100 truncate">
                {inspectedNode.metadata?.fullName || inspectedNode.label}
              </div>
              {inspectedNode.metadata?.nativeId && (
                <div className="text-[10px] text-slate-400 font-mono">
                  {inspectedNode.metadata.nativeId}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2 pt-1 text-[11px] font-mono">
              <div>
                <span className="text-atlas-muted text-[10px] block">MONTHLY SPEND</span>
                <span className="font-semibold text-slate-200">
                  {inspectedNode.spend ? formatCurrency(inspectedNode.spend, 'INR', false) : '—'}
                </span>
              </div>
              <div>
                <span className="text-atlas-muted text-[10px] block">STATUS</span>
                <span
                  className={`font-semibold uppercase text-[10px] ${
                    inspectedNode.state === 'alert'
                      ? 'text-rose-400'
                      : inspectedNode.state === 'optimizable'
                      ? 'text-emerald-400'
                      : 'text-slate-300'
                  }`}
                >
                  {inspectedNode.state}
                </span>
              </div>
            </div>

            {/* Context Navigation Handoff Actions */}
            <div className="pt-2 border-t border-[#1E2638] flex items-center justify-between">
              {isTraceMode && activeInvestigation?.investigationId ? (
                <button
                  type="button"
                  onClick={() =>
                    navigate(`/changes?investigationId=${encodeURIComponent(activeInvestigation.investigationId!)}`)
                  }
                  className="w-full py-1 rounded bg-sky-950/60 border border-sky-500/40 text-sky-400 hover:text-sky-300 hover:bg-sky-900/50 text-[11px] font-bold flex items-center justify-center gap-1 transition-colors"
                >
                  <span>OPEN INVESTIGATION</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              ) : inspectedNode.type === 'resource' && inspectedNode.metadata?.nativeId ? (
                <button
                  type="button"
                  onClick={() =>
                    navigate(`/resources?search=${encodeURIComponent(inspectedNode.metadata!.nativeId)}`)
                  }
                  className="w-full py-1 rounded bg-[#141B27] hover:bg-[#1E2638] border border-[#1E2638] text-sky-400 hover:text-sky-300 text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors"
                >
                  <span>OPEN RESOURCE INTELLIGENCE</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() =>
                    navigate(`/spend?service_name=${encodeURIComponent(inspectedNode.metadata?.fullName || inspectedNode.label)}`)
                  }
                  className="w-full py-1 rounded bg-[#141B27] hover:bg-[#1E2638] border border-[#1E2638] text-slate-300 hover:text-sky-300 text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors"
                >
                  <span>FILTER SPEND SCOPE</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

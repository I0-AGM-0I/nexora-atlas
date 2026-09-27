import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Database, Server, DollarSign, AlertTriangle, GitCompare } from 'lucide-react';
import type { AICitation } from '../../types/api';

interface AIEvidenceCitationProps {
  citation: AICitation;
}

export const AIEvidenceCitation: React.FC<AIEvidenceCitationProps> = ({ citation }) => {
  const getIcon = () => {
    switch (citation.entity_type) {
      case 'RESOURCE':
        return <Server className="w-3 h-3 text-cyan-400" />;
      case 'RECOMMENDATION':
        return <Database className="w-3 h-3 text-emerald-400" />;
      case 'COST':
        return <DollarSign className="w-3 h-3 text-amber-400" />;
      case 'ANOMALY':
        return <AlertTriangle className="w-3 h-3 text-rose-400" />;
      case 'SCENARIO':
        return <GitCompare className="w-3 h-3 text-purple-400" />;
      default:
        return <ExternalLink className="w-3 h-3 text-slate-400" />;
    }
  };

  return (
    <Link
      to={citation.link_path}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-slate-600 text-xs font-mono transition-colors"
      title={citation.description || `View ${citation.entity_type} in Atlas`}
    >
      {getIcon()}
      <span className="truncate max-w-[180px]">{citation.title}</span>
      <ExternalLink className="w-2.5 h-2.5 text-slate-500" />
    </Link>
  );
};

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, LayoutDashboard, BarChart3, AlertTriangle, Zap, GitFork, TrendingUp, Server, CloudCog, Settings, X, ArrowRight } from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

interface CommandItem {
  id: string;
  title: string;
  category: 'Navigation' | 'Resource' | 'Recommendation';
  path?: string;
  icon: React.ComponentType<{ className?: string }>;
  detail?: string;
}

const DEFAULT_COMMANDS: CommandItem[] = [
  { id: 'nav-overview', title: 'Overview Dashboard', category: 'Navigation', path: '/dashboard', icon: LayoutDashboard },
  { id: 'nav-spend', title: 'Spend Explorer', category: 'Navigation', path: '/spend', icon: BarChart3 },
  { id: 'nav-anomalies', title: 'Changes & Anomalies', category: 'Navigation', path: '/changes', icon: AlertTriangle },
  { id: 'nav-optimization', title: 'Optimization Center', category: 'Navigation', path: '/optimization', icon: Zap },
  { id: 'nav-scenarios', title: 'Scenario Simulator', category: 'Navigation', path: '/scenarios', icon: GitFork },
  { id: 'nav-forecast', title: 'Cost Forecast', category: 'Navigation', path: '/forecast', icon: TrendingUp },
  { id: 'nav-resources', title: 'Resource Inventory', category: 'Navigation', path: '/resources', icon: Server },
  { id: 'nav-integrations', title: 'Cloud Integrations', category: 'Navigation', path: '/integrations', icon: CloudCog },
  { id: 'nav-settings', title: 'Settings', category: 'Navigation', path: '/settings', icon: Settings },
  { id: 'res-ec2-1', title: 'i-0a8b9c1d2e (m5.4xlarge)', category: 'Resource', path: '/resources', icon: Server, detail: 'us-east-1 • ₹34,200/mo' },
  { id: 'rec-rightsize', title: 'Right-size EC2 to m5.large', category: 'Recommendation', path: '/optimization', icon: Zap, detail: 'Potential: ₹34,200/mo' },
];

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const filteredCommands = DEFAULT_COMMANDS.filter((cmd) =>
    cmd.title.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase()) ||
    (cmd.detail && cmd.detail.toLowerCase().includes(query.toLowerCase()))
  );

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
      setQuery('');
    }
  }, [isOpen]);

  // Keyboard navigation inside the palette
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filteredCommands.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + (filteredCommands.length || 1)) % (filteredCommands.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        executeCommand(filteredCommands[selectedIndex]);
      }
    }
  };

  const executeCommand = (cmd: CommandItem) => {
    if (cmd.path) {
      navigate(cmd.path);
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/70 backdrop-blur-sm p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
    >
      <div
        className="w-full max-w-2xl bg-[#0E131F] border border-atlas-border rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-100"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Header */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-atlas-border bg-[#0B0F19]">
          <Search className="w-5 h-5 text-atlas-primary flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command, resource name, or search path..."
            className="w-full bg-transparent text-sm text-atlas-text placeholder-atlas-muted focus:outline-none"
            aria-label="Search command input"
          />
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded text-atlas-muted hover:text-atlas-text focus:outline-none"
            aria-label="Close command palette"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1" role="listbox">
          {filteredCommands.length === 0 ? (
            <div className="p-8 text-center text-xs text-atlas-muted">
              No results found matching &quot;{query}&quot;
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => executeCommand(cmd)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-atlas-elevated text-atlas-text border border-atlas-primary/40'
                      : 'text-atlas-secondary hover:bg-atlas-surface border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-1.5 rounded ${
                        isSelected ? 'bg-atlas-primary/20 text-atlas-primary' : 'bg-atlas-surface text-atlas-muted'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-medium text-atlas-text">{cmd.title}</div>
                      {cmd.detail && <div className="text-[11px] text-atlas-muted font-mono">{cmd.detail}</div>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase bg-atlas-surface px-1.5 py-0.5 rounded border border-atlas-border text-atlas-muted">
                      {cmd.category}
                    </span>
                    {isSelected && <ArrowRight className="w-3.5 h-3.5 text-atlas-primary" />}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Shortcut Hints */}
        <div className="px-4 py-2 border-t border-atlas-border bg-[#0A0E17] flex items-center justify-between text-[11px] text-atlas-muted font-mono">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>Esc Close</span>
          </div>
          <span>NEXORA ATLAS</span>
        </div>
      </div>
    </div>
  );
};

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

export interface InvestigationState {
  investigationId?: string | null;
  entityId?: string | null;
  entityNativeId?: string | null;
  entityType?: 'SERVICE' | 'WORKLOAD' | 'RESOURCE' | 'ANOMALY' | 'OPPORTUNITY';
  entityName?: string | null;
  origin?: string | null;
  costDelta?: string | number | null;
  percentageChange?: string | number | null;
  timestamp?: string | null;
  isTraceActive?: boolean;
  isFocusActive?: boolean;
}

export interface RecentInvestigation {
  id: string;
  title: string;
  subtitle: string;
  path: string;
  timestamp: string;
}

interface InvestigationContextType {
  activeInvestigation: InvestigationState | null;
  startTrace: (target: InvestigationState, navigateTo?: string) => void;
  clearTrace: () => void;
  startFocus: (target: InvestigationState) => void;
  clearFocus: () => void;
  resetAll: () => void;
  recentInvestigations: RecentInvestigation[];
  addRecentInvestigation: (item: Omit<RecentInvestigation, 'timestamp'>) => void;
}

const InvestigationContext = createContext<InvestigationContextType | undefined>(undefined);

const STORAGE_KEY = 'atlas_recent_investigations';

export const InvestigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const [activeInvestigation, setActiveInvestigation] = useState<InvestigationState | null>(() => {
    // Initialize from URL parameters if present
    const id = searchParams.get('investigationId') || undefined;
    const entityId = searchParams.get('entityId') || undefined;
    const trace = searchParams.get('trace') === 'true';
    if (id || entityId || trace) {
      return {
        investigationId: id,
        entityId: entityId,
        isTraceActive: trace,
      };
    }
    return null;
  });

  const [recentInvestigations, setRecentInvestigations] = useState<RecentInvestigation[]>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Sync recent investigations to sessionStorage
  const saveRecent = (items: RecentInvestigation[]) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 5)));
    } catch {
      // storage unavailable
    }
  };

  const addRecentInvestigation = useCallback((item: Omit<RecentInvestigation, 'timestamp'>) => {
    const newItem: RecentInvestigation = {
      ...item,
      timestamp: new Date().toISOString(),
    };
    setRecentInvestigations((prev) => {
      const filtered = prev.filter((r) => r.id !== item.id);
      const updated = [newItem, ...filtered].slice(0, 5);
      saveRecent(updated);
      return updated;
    });
  }, []);

  // Global Escape key listener (Directive #8)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (activeInvestigation?.isTraceActive || activeInvestigation?.isFocusActive) {
          e.preventDefault();
          setActiveInvestigation((prev) =>
            prev ? { ...prev, isTraceActive: false, isFocusActive: false } : null
          );
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeInvestigation]);

  const startTrace = useCallback(
    (target: InvestigationState, navigateTo?: string) => {
      const updated: InvestigationState = {
        ...target,
        isTraceActive: true,
        isFocusActive: false,
      };
      setActiveInvestigation(updated);

      if (target.entityName || target.investigationId) {
        addRecentInvestigation({
          id: target.investigationId || target.entityId || String(Date.now()),
          title: target.entityName || target.entityNativeId || 'Investigation Target',
          subtitle: target.origin || `${target.entityType || 'Entity'} Trace`,
          path: navigateTo || location.pathname,
        });
      }

      if (navigateTo) {
        const url = new URL(navigateTo, window.location.origin);
        if (target.investigationId) url.searchParams.set('investigationId', target.investigationId);
        if (target.entityId) url.searchParams.set('entityId', target.entityId);
        url.searchParams.set('trace', 'true');
        navigate(url.pathname + url.search);
      }
    },
    [addRecentInvestigation, location.pathname, navigate]
  );

  const clearTrace = useCallback(() => {
    setActiveInvestigation((prev) => (prev ? { ...prev, isTraceActive: false } : null));
  }, []);

  const startFocus = useCallback((target: InvestigationState) => {
    setActiveInvestigation({
      ...target,
      isFocusActive: true,
      isTraceActive: false,
    });
  }, []);

  const clearFocus = useCallback(() => {
    setActiveInvestigation((prev) => (prev ? { ...prev, isFocusActive: false } : null));
  }, []);

  const resetAll = useCallback(() => {
    setActiveInvestigation(null);
  }, []);

  return (
    <InvestigationContext.Provider
      value={{
        activeInvestigation,
        startTrace,
        clearTrace,
        startFocus,
        clearFocus,
        resetAll,
        recentInvestigations,
        addRecentInvestigation,
      }}
    >
      {children}
    </InvestigationContext.Provider>
  );
};

export const useInvestigation = (): InvestigationContextType => {
  const context = useContext(InvestigationContext);
  if (!context) {
    throw new Error('useInvestigation must be used within an InvestigationProvider');
  }
  return context;
};

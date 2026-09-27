import React, { createContext, useContext, useState, ReactNode } from 'react';
import type { ScopeType } from '../types/api';

export interface AskAtlasContextData {
  scopeType?: ScopeType;
  scopeLabel?: string;
  initialQuestion?: string;
  resourceId?: string;
  resourceName?: string;
  recommendationId?: string;
  anomalyId?: string;
  scenarioId?: string;
  serviceName?: string;
  accountId?: string;
  suggestedQueries?: string[];
}

interface AskAtlasContextValue {
  isAskAtlasOpen: boolean;
  activeContext: AskAtlasContextData | null;
  openAskAtlas: (context?: AskAtlasContextData) => void;
  closeAskAtlas: () => void;
  clearActiveContext: () => void;
}

const AskAtlasContext = createContext<AskAtlasContextValue | undefined>(undefined);

export const AskAtlasProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAskAtlasOpen, setIsAskAtlasOpen] = useState(false);
  const [activeContext, setActiveContext] = useState<AskAtlasContextData | null>(null);

  const openAskAtlas = (context?: AskAtlasContextData) => {
    setActiveContext(context || null);
    setIsAskAtlasOpen(true);
  };

  const closeAskAtlas = () => {
    setIsAskAtlasOpen(false);
  };

  const clearActiveContext = () => {
    setActiveContext(null);
  };

  return (
    <AskAtlasContext.Provider
      value={{
        isAskAtlasOpen,
        activeContext,
        openAskAtlas,
        closeAskAtlas,
        clearActiveContext,
      }}
    >
      {children}
    </AskAtlasContext.Provider>
  );
};

export const useAskAtlas = (): AskAtlasContextValue => {
  const context = useContext(AskAtlasContext);
  if (!context) {
    throw new Error('useAskAtlas must be used within an AskAtlasProvider');
  }
  return context;
};

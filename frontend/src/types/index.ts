export interface AgentStatus {
  name: string;
  description: string;
  progress: number;
  status: 'pending' | 'active' | 'completed' | 'error';
  icon: string;
}

export interface ProcessingState {
  isProcessing: boolean;
  currentAgent: AgentStatus | null;
  agents: AgentStatus[];
  progress: number;
  startTime?: Date;
}

export interface SourceInfo {
  type: 'local_knowledge_base' | 'web_search' | 'twitter' | 'llm_reasoning';
  title: string;
  content: string;
  citation: string;
  relevanceScore: number;
  date?: string;
}

export interface QueryResult {
  sessionId: string;
  query: string;
  response: string;
  confidence: number;
  requiresEscalation: boolean;
  processingTime: number;
  sources: {
    localCount: number;
    webCount: number;
    twitterCount: number;
    llmCount: number;
    totalCount: number;
  };
  detailedSources: {
    localSources: SourceInfo[];
    webSources: SourceInfo[];
    twitterSources: SourceInfo[];
    llmSources: SourceInfo[];
  };
  resolutionStats: {
    overallConfidence: number;
    requiresEscalation: boolean;
  };
  errors: string[];
  timestamp: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface QueryHistory {
  id: string;
  query: string;
  category: string;
  result?: QueryResult;
  timestamp: string;
  processingTime?: number;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface SystemStatus {
  initialized: boolean;
  agentsReady: boolean;
  agentCount: number;
  lastHealthCheck: Date;
  errors: string[];
}

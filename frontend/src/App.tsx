import React from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  Shield,
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react';

import { QueryForm } from '@/components/QueryForm';
import { AgentStatusDisplay } from '@/components/AgentStatusDisplay';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { QueryHistorySidebar } from '@/components/QueryHistory';
import { QueryHistory, QueryResult, SystemStatus } from '@/types';
import { apiClient, handleApiError } from '@/lib/api';
import {
  useWebSocket,
  AgentStatusPayload,
  QueryResultPayload,
  WebSocketErrorPayload
} from '@/hooks/useWebSocket';
import { useAgentProgress } from '@/hooks/useAgentProgress';

export const App: React.FC = () => {
  const [systemStatus, setSystemStatus] = React.useState<SystemStatus | null>(null);
  const [isInitialized, setIsInitialized] = React.useState(false);
  const [currentResult, setCurrentResult] = React.useState<QueryResult | null>(null);
  const [queryHistory, setQueryHistory] = React.useState<QueryHistory[]>([]);
  const [currentSessionId, setCurrentSessionId] = React.useState<string | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const {
    processingState,
    startProcessing,
    updateAgentStatus,
    setAgentError,
    completeProcessing,
    resetProcessing
  } = useAgentProgress();

  const currentSessionRef = React.useRef<string | null>(null);
  const completedSessionsRef = React.useRef<Set<string>>(new Set());
  const processingStateRef = React.useRef(processingState);
  const startTimeRef = React.useRef<Date | undefined>(processingState.startTime);

  React.useEffect(() => {
    currentSessionRef.current = currentSessionId;
  }, [currentSessionId]);

  React.useEffect(() => {
    processingStateRef.current = processingState;
    startTimeRef.current = processingState.startTime;
  }, [processingState]);

  React.useEffect(() => {
    const bootstrap = async () => {
      await initializeSystem();
      await fetchSystemStatus();
      await fetchQueryHistory();
    };

    bootstrap();
  }, []);

  const initializeSystem = async () => {
    try {
      const status = await apiClient.getSystemStatus();
      setSystemStatus(status);
      if (status.initialized && status.agentsReady) {
        setIsInitialized(true);
      } else {
        setError('System is not ready. Please wait a moment and refresh.');
      }
    } catch (err) {
      const message = handleApiError(err);
      setError(message);
      console.error('Failed to initialize system:', err);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const status = await apiClient.getSystemStatus();
      setSystemStatus(status);
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    }
  };

  const fetchQueryHistory = async () => {
    try {
      const history = await apiClient.getQueryHistory();
      setQueryHistory(history);
    } catch (err) {
      console.error('Failed to fetch query history:', err);
    }
  };

  const handleAgentStatusMessage = React.useCallback(
    (payload: AgentStatusPayload) => {
      if (payload.session_id !== currentSessionRef.current) {
        return;
      }
      updateAgentStatus(payload.agent_name, payload.description, payload.progress);
      setQueryHistory(prev =>
        prev.map(item =>
          item.id === payload.session_id
            ? { ...item, status: 'processing', timestamp: payload.timestamp }
            : item
        )
      );
    },
    [updateAgentStatus]
  );

  const handleQueryResultMessage = React.useCallback(
    (payload: QueryResultPayload) => {
      if (payload.session_id !== currentSessionRef.current) {
        return;
      }

      if (completedSessionsRef.current.has(payload.session_id)) {
        return;
      }
      completedSessionsRef.current.add(payload.session_id);
      completeProcessing();
      setCurrentResult(payload.result);

      const explicitProcessingTime =
        payload.result?.processingTime ?? payload.result?.processing_time;
      let processingTime = typeof explicitProcessingTime === 'number' ? explicitProcessingTime : undefined;

      if (processingTime === undefined && startTimeRef.current) {
        processingTime = (Date.now() - startTimeRef.current.getTime()) / 1000;
      }

      setQueryHistory(prev =>
        prev.map(item =>
          item.id === payload.session_id
            ? {
                ...item,
                status: 'completed',
                result: payload.result,
                processingTime,
                timestamp: payload.timestamp
              }
            : item
        )
      );

      setCurrentSessionId(null);
      setError(null);
    },
    [completeProcessing]
  );

  const handleWebSocketErrorMessage = React.useCallback(
    (payload: WebSocketErrorPayload) => {
      if (payload.session_id !== currentSessionRef.current) {
        return;
      }

      if (completedSessionsRef.current.has(payload.session_id)) {
        return;
      }
      completedSessionsRef.current.add(payload.session_id);
      const failingAgent =
        processingStateRef.current.currentAgent?.name ?? '✍️ Agent 5: Response Generation';
      setAgentError(failingAgent, payload.error);
      setError(payload.error);

      setQueryHistory(prev =>
        prev.map(item =>
          item.id === payload.session_id
            ? { ...item, status: 'error', timestamp: payload.timestamp }
            : item
        )
      );

      setCurrentSessionId(null);
    },
    [setAgentError]
  );

  const { isConnected: isWebSocketConnected, error: webSocketError } = useWebSocket({
    sessionId: currentSessionId,
    onAgentStatus: handleAgentStatusMessage,
    onQueryResult: handleQueryResultMessage,
    onError: handleWebSocketErrorMessage,
    onConnection: () => setError(null),
    onDisconnect: () => {
      if (processingStateRef.current.isProcessing) {
        setError(prev => prev ?? 'WebSocket connection lost. Attempting to reconnect...');
      }
    }
  });

  const handleQuerySubmit = async (query: string, category: string) => {
    if (processingState.isProcessing) {
      return;
    }

    setError(null);
    setCurrentResult(null);
    startProcessing();

    try {
      const response = await apiClient.submitQuery(query, category);
      const sessionId = response.sessionId;

      completedSessionsRef.current.delete(sessionId);
      currentSessionRef.current = sessionId;
      setCurrentSessionId(sessionId);

      setQueryHistory(prev => [
        {
          id: sessionId,
          query,
          category,
          status: 'processing',
          timestamp: new Date().toISOString()
        },
        ...prev.filter(item => item.id !== sessionId)
      ]);
    } catch (err) {
      const message = handleApiError(err);
      setAgentError('🔍 Agent 1: Preprocessing', message);
      setError(message);
      resetProcessing();
    }
  };

  const handleNewQuery = () => {
    setCurrentResult(null);
    setCurrentSessionId(null);
    setError(null);
    resetProcessing();
  };

  const handleSelectHistoryQuery = (item: QueryHistory) => {
    if (item.result) {
      setCurrentResult(item.result);
    } else {
      handleQuerySubmit(item.query, item.category);
    }
    setIsHistoryOpen(false);
  };

  const handleClearHistory = async () => {
    try {
      await apiClient.clearHistory();
      setQueryHistory([]);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  const handleRefreshStatus = () => {
    fetchSystemStatus();
  };

  const effectiveError = error ?? webSocketError ?? null;

  return (
    <div className="min-h-screen gradient-bg">
      <div className="flex h-screen">
        {/* Sidebar - Query History */}
        <div
          className={`${isHistoryOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-white/80 backdrop-blur-xl border-r border-accent-200 overflow-hidden`}
        >
          <QueryHistorySidebar
            history={queryHistory}
            onSelectQuery={handleSelectHistoryQuery}
            onClearHistory={handleClearHistory}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <header className="bg-white/80 backdrop-blur-xl border-b border-accent-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold gradient-text">
                    GST Grievance Resolution System
                  </h1>
                  <p className="text-accent-600 text-sm">
                    Multi-Agent RAG System with Real-time Processing
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {processingState.isProcessing && currentSessionId && (
                  <div
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${
                      isWebSocketConnected
                        ? 'bg-success-50 border-success-200 text-success-700'
                        : 'bg-warning-50 border-warning-200 text-warning-700'
                    }`}
                  >
                    {isWebSocketConnected ? (
                      <>
                        <Wifi className="w-4 h-4" />
                        <span className="text-sm font-medium">Real-time Updates</span>
                      </>
                    ) : (
                      <>
                        <WifiOff className="w-4 h-4" />
                        <span className="text-sm font-medium">Connecting...</span>
                      </>
                    )}
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  {systemStatus ? (
                    <>
                      <div
                        className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${
                          systemStatus.initialized && systemStatus.agentsReady
                            ? 'bg-success-50 border-success-200 text-success-700'
                            : 'bg-warning-50 border-warning-200 text-warning-700'
                        }`}
                      >
                        {systemStatus.initialized && systemStatus.agentsReady ? (
                          <>
                            <CheckCircle2 className="w-4 h-4" />
                            <span className="text-sm font-medium">System Ready</span>
                          </>
                        ) : (
                          <>
                            <Activity className="w-4 h-4 animate-spin" />
                            <span className="text-sm font-medium">Initializing...</span>
                          </>
                        )}
                      </div>
                      <span className="text-xs text-accent-500">
                        {systemStatus.agentCount || 0} agents active
                      </span>
                    </>
                  ) : (
                    <div className="flex items-center space-x-2 px-3 py-2 rounded-lg border border-accent-200 bg-accent-50 text-accent-700">
                      <Activity className="w-4 h-4 animate-spin" />
                      <span className="text-sm font-medium">Loading...</span>
                    </div>
                  )}
                  <button
                    onClick={handleRefreshStatus}
                    className="p-2 text-accent-600 hover:text-accent-800 hover:bg-accent-100 rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>

                <button
                  onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isHistoryOpen
                      ? 'bg-accent-100 text-accent-700 hover:bg-accent-200'
                      : 'bg-white border border-accent-200 text-accent-700 hover:bg-accent-50'
                  }`}
                >
                  <Activity className="w-4 h-4 inline mr-2" />
                  {isHistoryOpen ? 'Hide History' : 'Show History'}
                </button>
              </div>
            </div>

            {effectiveError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-4"
              >
                <div className="bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-lg flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">{effectiveError}</span>
                </div>
              </motion.div>
            )}
          </header>

          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
              {!processingState.isProcessing && !currentResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <QueryForm
                    onSubmit={handleQuerySubmit}
                    isDisabled={!isInitialized || processingState.isProcessing}
                  />
                </motion.div>
              )}

              {(processingState.isProcessing || processingState.progress > 0) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <AgentStatusDisplay
                    agents={processingState.agents}
                    isProcessing={processingState.isProcessing}
                  />
                </motion.div>
              )}

              {currentResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <ResultsDisplay result={currentResult} onNewQuery={handleNewQuery} />
                </motion.div>
              )}

              {!processingState.isProcessing && !currentResult && isInitialized && !effectiveError && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="text-center py-20"
                >
                  <div className="max-w-2xl mx-auto">
                    <div className="mb-8">
                      <Brain className="w-16 h-16 mx-auto text-primary-600 mb-4" />
                      <h2 className="text-3xl font-bold gradient-text mb-4">
                        Welcome to GST Grievance Resolution
                      </h2>
                      <p className="text-lg text-accent-600 mb-8">
                        Our AI-powered multi-agent system is ready to help resolve your GST-related queries with expert precision.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                      <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 border border-accent-200">
                        <div className="text-center">
                          <Shield className="w-8 h-8 mx-auto text-primary-600 mb-3" />
                          <h3 className="font-semibold text-accent-900 mb-2">
                            Secure & Private
                          </h3>
                          <p className="text-sm text-accent-600">
                            Your queries are processed securely with enterprise-grade privacy protection.
                          </p>
                        </div>
                      </div>

                      <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 border border-accent-200">
                        <div className="text-center">
                          <Wifi className="w-8 h-8 mx-auto text-primary-600 mb-3" />
                          <h3 className="font-semibold text-accent-900 mb-2">
                            WebSocket Live Updates
                          </h3>
                          <p className="text-sm text-accent-600">
                            Experience real-time agent progress tracking with instant WebSocket communication.
                          </p>
                        </div>
                      </div>

                      <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 border border-accent-200">
                        <div className="text-center">
                          <CheckCircle2 className="w-8 h-8 mx-auto text-primary-600 mb-3" />
                          <h3 className="font-semibold text-accent-900 mb-2">
                            Expert Accuracy
                          </h3>
                          <p className="text-sm text-accent-600">
                            Get precise, reliable solutions backed by comprehensive GST knowledge bases.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

import { useCallback, useEffect, useRef, useState } from 'react';

type WebSocketMessageType =
  | 'connection'
  | 'agent_status'
  | 'query_result'
  | 'error'
  | 'pong'
  | 'system_status'
  | 'ping';

interface WebSocketMessage<T = any> {
  type: WebSocketMessageType;
  data?: T;
  timestamp?: string;
}

export interface AgentStatusPayload {
  session_id: string;
  agent_name: string;
  description: string;
  progress: number;
  timestamp: string;
}

export interface QueryResultPayload {
  session_id: string;
  status: string;
  result: any;
  timestamp: string;
}

export interface WebSocketErrorPayload {
  session_id: string;
  error: string;
  timestamp: string;
}

interface UseWebSocketOptions {
  sessionId: string | null;
  onAgentStatus?: (payload: AgentStatusPayload) => void;
  onQueryResult?: (payload: QueryResultPayload) => void;
  onError?: (payload: WebSocketErrorPayload) => void;
  onConnection?: (sessionId: string) => void;
  onDisconnect?: (sessionId: string | null) => void;
}

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '');

const deriveWebSocketUrl = (sessionId: string): string => {
  const explicitBase = import.meta.env.VITE_WS_URL as string | undefined;

  if (explicitBase) {
    if (explicitBase.includes('{sessionId}')) {
      return explicitBase.replace('{sessionId}', sessionId);
    }

    const trimmed = trimTrailingSlash(explicitBase);

    if (trimmed.startsWith('ws://') || trimmed.startsWith('wss://')) {
      if (trimmed.endsWith('/ws')) {
        return `${trimmed}/${sessionId}`;
      }
      return `${trimmed}/ws/${sessionId}`;
    }

    try {
      const url = new URL(trimmed);
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${url.host}/ws/${sessionId}`;
    } catch {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const host = trimmed.replace(/^\/+/, '');
      return `${protocol}://${host}/ws/${sessionId}`;
    }
  }

  const apiBase = import.meta.env.VITE_API_URL as string | undefined;
  let base = apiBase ?? 'http://localhost:8000';

  if (!/^https?:\/\//i.test(base)) {
    base = `http://${base.replace(/^\/+/, '')}`;
  }

  if (base.startsWith('/')) {
    base = `${window.location.origin}${base}`;
  }

  try {
    const url = new URL(base);
    const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${url.host}/ws/${sessionId}`;
  } catch {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/${sessionId}`;
  }
};

export const useWebSocket = ({
  sessionId,
  onAgentStatus,
  onQueryResult,
  onError,
  onConnection,
  onDisconnect
}: UseWebSocketOptions) => {
  const logPrefix = '[WS]';
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const activeSessionRef = useRef<string | null>(null);
  const shouldReconnectRef = useRef(false);
  const maxReconnectAttempts = 5;

  const callbacksRef = useRef({
    onAgentStatus,
    onQueryResult,
    onError,
    onConnection,
    onDisconnect
  });

  useEffect(() => {
    callbacksRef.current = {
      onAgentStatus,
      onQueryResult,
      onError,
      onConnection,
      onDisconnect
    };
  }, [onAgentStatus, onQueryResult, onError, onConnection, onDisconnect]);

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  const closeSocket = useCallback((code: number = 1000, reason?: string) => {
    if (socketRef.current) {
      try {
        socketRef.current.close(code, reason);
      } catch {
        // no-op
      }
      socketRef.current = null;
    }
    setIsConnected(false);
    clearTimers();
  }, [clearTimers]);

  const connect = useCallback(() => {
    if (!sessionId) {
      console.debug(`${logPrefix} no sessionId provided, skipping WebSocket connection`);
      return;
    }

    // Avoid duplicate connections for the same session
    if (
      socketRef.current &&
      activeSessionRef.current === sessionId &&
      (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    closeSocket(1000, 'Re-establishing connection');

    const wsUrl = deriveWebSocketUrl(sessionId);
    console.debug(`${logPrefix} connecting to ${wsUrl}`);

    try {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;
      activeSessionRef.current = sessionId;
      shouldReconnectRef.current = true;

      socket.onopen = () => {
        console.debug(`${logPrefix} connected`, { sessionId });
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        pingIntervalRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'ping', session_id: sessionId }));
          }
        }, 30000);

        callbacksRef.current.onConnection?.(sessionId);
      };

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.debug(`${logPrefix} message`, message);
          setLastMessage(message);

          switch (message.type) {
            case 'agent_status':
              if (message.data) {
                callbacksRef.current.onAgentStatus?.(message.data as AgentStatusPayload);
              }
              break;
            case 'query_result':
              if (message.data) {
                callbacksRef.current.onQueryResult?.(message.data as QueryResultPayload);
              }
              break;
            case 'error':
              if (message.data) {
                callbacksRef.current.onError?.(message.data as WebSocketErrorPayload);
              } else {
                callbacksRef.current.onError?.({
                  session_id: activeSessionRef.current ?? sessionId,
                  error: 'Unknown WebSocket error',
                  timestamp: new Date().toISOString()
                });
              }
              break;
            case 'ping':
              if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'pong', session_id: sessionId }));
              }
              break;
            default:
              // Ignore other system messages
              break;
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      socket.onclose = (event) => {
        console.debug(`${logPrefix} closed`, { sessionId: activeSessionRef.current, code: event.code, reason: event.reason });
        setIsConnected(false);
        clearTimers();
        callbacksRef.current.onDisconnect?.(activeSessionRef.current);

        const shouldAttemptReconnect =
          shouldReconnectRef.current &&
          activeSessionRef.current === sessionId &&
          event.code !== 1000 &&
          reconnectAttemptsRef.current < maxReconnectAttempts;

        if (shouldAttemptReconnect) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Failed to maintain WebSocket connection. Please refresh the page.');
        }
      };

      socket.onerror = (event) => {
        console.error(`${logPrefix} encountered an error`, event);
        setError('WebSocket connection error');
        callbacksRef.current.onError?.({
          session_id: activeSessionRef.current ?? sessionId,
          error: 'WebSocket connection error',
          timestamp: new Date().toISOString()
        });
      };
    } catch (err) {
      console.error(`${logPrefix} failed to establish connection`, err);
      setError('Failed to establish WebSocket connection');
      callbacksRef.current.onError?.({
        session_id: sessionId,
        error: 'Failed to create WebSocket connection',
        timestamp: new Date().toISOString()
      });
    }
  }, [clearTimers, sessionId]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    reconnectAttemptsRef.current = 0;
    clearTimers();
    closeSocket(1000, 'User disconnected');
    activeSessionRef.current = null;
  }, [clearTimers, closeSocket]);

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    if (sessionId) {
      shouldReconnectRef.current = true;
      activeSessionRef.current = sessionId;
      connect();
    } else {
      disconnect();
    }
  }, [sessionId, connect, disconnect]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    error,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect
  };
};

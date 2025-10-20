import axios, { AxiosResponse, AxiosError } from 'axios';
import { QueryResult, QueryHistory, SystemStatus, ApiResponse } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 10 minutes timeout (600 seconds)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error: AxiosError) => {
    console.error('❌ Response error:', error);

    if (error.code === 'ECONNABORTED') {
      error.message = 'Request timeout. Please try again.';
    } else if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      if (status === 401) {
        error.message = 'Unauthorized. Please check your credentials.';
      } else if (status === 403) {
        error.message = 'Forbidden. You do not have permission to perform this action.';
      } else if (status === 404) {
        error.message = 'Resource not found.';
      } else if (status === 500) {
        error.message = 'Internal server error. Please try again later.';
      } else if (status >= 500) {
        error.message = 'Server error. Please try again later.';
      }
    } else if (error.code === 'ERR_NETWORK') {
      error.message = 'Network error. Please check your connection.';
    }

    return Promise.reject(error);
  }
);

export const apiClient = {
  // System status
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await api.get<ApiResponse<SystemStatus>>('/api/status');
    return response.data.data!;
  },

  // Query submission
  async submitQuery(query: string, category: string): Promise<{ sessionId: string }> {
    const response = await api.post<ApiResponse<{ sessionId: string }>>('/api/query', {
      query,
      category
    });
    return response.data.data!;
  },

  // Get query result
  async getQueryResult(sessionId: string): Promise<QueryResult> {
    const response = await api.get<ApiResponse<QueryResult>>(`/api/query/${sessionId}/result`);
    return response.data.data!;
  },

  // Get query progress
  async getQueryProgress(sessionId: string): Promise<any> {
    const response = await api.get<ApiResponse<any>>(`/api/query/${sessionId}/progress`);
    return response.data.data;
  },

  // Cancel query
  async cancelQuery(sessionId: string): Promise<void> {
    await api.post(`/api/query/${sessionId}/cancel`);
  },

  // Get query history
  async getQueryHistory(): Promise<QueryHistory[]> {
    const response = await api.get<ApiResponse<QueryHistory[]>>('/api/history');
    return response.data.data || [];
  },

  // Clear history
  async clearHistory(): Promise<void> {
    await api.delete('/api/history');
  },

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get('/api/health');
    return response.data;
  }
};

// Error handling utility
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    return error.message || 'An unexpected error occurred';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

// Retry utility
export const retryApiCall = async <T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: unknown;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        // Wait with exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  }

  throw lastError;
};

export default api;

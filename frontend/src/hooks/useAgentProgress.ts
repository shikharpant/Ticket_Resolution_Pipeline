import { useState, useCallback } from 'react';
import { AgentStatus, ProcessingState } from '@/types';

const initialAgents: AgentStatus[] = [
  {
    name: '🔍 Agent 1: Preprocessing',
    description: 'Cleaning and analyzing your query...',
    progress: 0,
    status: 'pending',
    icon: '🔍'
  },
  {
    name: '📊 Agent 2: Classification',
    description: 'Categorizing your GST issue...',
    progress: 0,
    status: 'pending',
    icon: '📊'
  },
  {
    name: '🔎 Agent 3: Multi-Source Retrieval',
    description: 'Searching knowledge bases and web...',
    progress: 0,
    status: 'pending',
    icon: '🔎'
  },
  {
    name: '🤖 Agent 4: Resolution',
    description: 'Analyzing information and generating resolution...',
    progress: 0,
    status: 'pending',
    icon: '🤖'
  },
  {
    name: '✍️ Agent 5: Response Generation',
    description: 'Formatting final response...',
    progress: 0,
    status: 'pending',
    icon: '✍️'
  }
];

export const useAgentProgress = () => {
  const [processingState, setProcessingState] = useState<ProcessingState>({
    isProcessing: false,
    currentAgent: null,
    agents: initialAgents,
    progress: 0
  });

  const startProcessing = useCallback(() => {
    setProcessingState({
      isProcessing: true,
      currentAgent: null,
      agents: initialAgents.map(agent => ({
        ...agent,
        status: 'pending' as const,
        progress: 0
      })),
      progress: 0,
      startTime: new Date()
    });
  }, []);

  const updateAgentStatus = useCallback((agentName: string, description: string, progress: number) => {
    setProcessingState(prev => {
      let agentIndex = prev.agents.findIndex(agent => agent.name === agentName);
      let updatedAgents = [...prev.agents];

      if (agentIndex === -1) {
        const icon = agentName.trim().charAt(0) || '🤖';
        updatedAgents = [
          ...updatedAgents,
          {
            name: agentName,
            description,
            progress: 0,
            status: 'pending',
            icon
          }
        ];
        agentIndex = updatedAgents.length - 1;
      }

      // Update previous agent to completed
      for (let i = 0; i < agentIndex; i++) {
        if (updatedAgents[i].status === 'pending' || updatedAgents[i].status === 'active') {
          updatedAgents[i] = {
            ...updatedAgents[i],
            status: 'completed',
            progress: 1
          };
        }
      }

      // Update current agent
      const isComplete = progress >= 1;
      updatedAgents[agentIndex] = {
        ...updatedAgents[agentIndex],
        status: isComplete ? 'completed' : 'active',
        progress,
        description
      };

      const overallProgress = updatedAgents.reduce((sum, agent) => sum + agent.progress, 0) / updatedAgents.length;

      return {
        ...prev,
        agents: updatedAgents,
        currentAgent: updatedAgents[agentIndex],
        progress: overallProgress,
        isProcessing: !isComplete || agentIndex < updatedAgents.length - 1
      };
    });
  }, []);

  const setAgentError = useCallback((agentName: string, error: string) => {
    setProcessingState(prev => {
      let agentIndex = prev.agents.findIndex(agent => agent.name === agentName);
      let updatedAgents = [...prev.agents];

      if (agentIndex === -1) {
        const icon = agentName.trim().charAt(0) || '⚠️';
        updatedAgents = [
          ...updatedAgents,
          {
            name: agentName,
            description: `Error: ${error}`,
            progress: 0,
            status: 'error',
            icon
          }
        ];
        agentIndex = updatedAgents.length - 1;
      }

      updatedAgents[agentIndex] = {
        ...updatedAgents[agentIndex],
        status: 'error',
        description: `Error: ${error}`
      };

      return {
        ...prev,
        agents: updatedAgents,
        currentAgent: updatedAgents[agentIndex],
        isProcessing: false
      };
    });
  }, []);

  const completeProcessing = useCallback(() => {
    setProcessingState(prev => ({
      ...prev,
      isProcessing: false,
      progress: 1,
      agents: prev.agents.map(agent => ({
        ...agent,
        status: 'completed' as const,
        progress: 1
      }))
    }));
  }, []);

  const resetProcessing = useCallback(() => {
    setProcessingState({
      isProcessing: false,
      currentAgent: null,
      agents: initialAgents.map(agent => ({
        ...agent,
        status: 'pending' as const,
        progress: 0
      })),
      progress: 0
    });
  }, []);

  return {
    processingState,
    startProcessing,
    updateAgentStatus,
    setAgentError,
    completeProcessing,
    resetProcessing
  };
};

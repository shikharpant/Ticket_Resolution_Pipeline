import React from 'react';
import { motion } from 'framer-motion';
import { AgentStatus } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { CheckCircle, Circle, XCircle } from 'lucide-react';

interface AgentStatusDisplayProps {
  agents: AgentStatus[];
  isProcessing: boolean;
}

const getStatusIcon = (status: AgentStatus['status']) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-success-600" />;
    case 'active':
      return <LoadingSpinner size="sm" color="primary" />;
    case 'error':
      return <XCircle className="w-5 h-5 text-error-600" />;
    default:
      return <Circle className="w-5 h-5 text-accent-400" />;
  }
};

const getStatusColor = (status: AgentStatus['status']) => {
  switch (status) {
    case 'completed':
      return 'text-success-600 bg-success-50 border-success-200';
    case 'active':
      return 'text-primary-600 bg-primary-50 border-primary-200';
    case 'error':
      return 'text-error-600 bg-error-50 border-error-200';
    default:
      return 'text-accent-600 bg-accent-50 border-accent-200';
  }
};

export const AgentStatusDisplay: React.FC<AgentStatusDisplayProps> = ({ agents, isProcessing }) => {
  const currentAgentIndex = agents.findIndex(agent => agent.status === 'active');

  return (
    <Card variant="glass" className="agent-progress">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-accent-900">Multi-Agent Processing</h3>
          {isProcessing && (
            <div className="flex items-center space-x-2">
              <LoadingSpinner size="sm" />
              <span className="text-sm text-accent-600">Processing...</span>
            </div>
          )}
        </div>

        <div className="space-y-4">
          {agents.map((agent, index) => (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{
                opacity: 1,
                x: 0,
                transition: { delay: index * 0.1, duration: 0.3 }
              }}
              className={`
                relative overflow-hidden rounded-xl border p-4 transition-all duration-300
                ${getStatusColor(agent.status)}
                ${agent.status === 'active' ? 'ring-2 ring-primary-500 ring-offset-2' : ''}
              `}
            >
              {agent.status === 'active' && (
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-accent-500/10"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0.3, 0.6, 0.3] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}

              <div className="relative flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{agent.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-accent-900">{agent.name}</h4>
                      {getStatusIcon(agent.status)}
                    </div>
                    <p className="text-sm text-accent-700 mt-1">{agent.description}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="text-sm font-medium text-accent-900">
                    {Math.round(agent.progress * 100)}%
                  </div>
                </div>
              </div>

              {agent.progress > 0 && (
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${agent.progress * 100}%` }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                  className="mt-3"
                >
                  <Progress
                    value={agent.progress * 100}
                    size="sm"
                    variant={agent.status === 'error' ? 'error' : 'default'}
                  />
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>

        {isProcessing && currentAgentIndex >= 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 text-center"
          >
            <div className="typing-indicator justify-center">
              <span style={{ '--i': 0 } as React.CSSProperties} />
              <span style={{ '--i': 1 } as React.CSSProperties} />
              <span style={{ '--i': 2 } as React.CSSProperties} />
            </div>
            <p className="text-sm text-accent-600 mt-2">
              {agents[currentAgentIndex]?.description || 'Processing...'}
            </p>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
};

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  ExternalLink,
  Copy,
  Calendar,
  BarChart3,
  Check
} from 'lucide-react';
import { QueryResult } from '@/types';
import { formatProcessingTime, formatTimestamp, getConfidenceColor, copyToClipboard } from '@/lib/utils';

interface ResultsDisplayProps {
  result: QueryResult;
  onNewQuery: () => void;
}

const SourceCard: React.FC<{ title: string; count: number; icon: React.ReactNode; color: string }> = ({
  title,
  count,
  icon,
  color
}) => (
  <Card variant="outlined" className={`${color} border-2`}>
    <CardContent className="p-4 text-center">
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-2xl font-bold text-accent-900">{count}</div>
      <div className="text-sm text-accent-600">{title}</div>
    </CardContent>
  </Card>
);

const SourceDetails: React.FC<{ sources: any[], title: string, icon: React.ReactNode }> = ({
  sources,
  title,
  icon
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [expandedSources, setExpandedSources] = React.useState<Set<number>>(new Set());

  if (sources.length === 0) return null;

  const toggleSourceExpansion = (index: number) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  return (
    <Card variant="glass" className="mt-4">
      <CardContent className="p-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between text-left hover:bg-accent-50 rounded-lg p-2 transition-colors"
        >
          <div className="flex items-center space-x-2">
            {icon}
            <span className="font-medium text-accent-900">{title}</span>
            <span className="text-sm text-accent-600">({sources.length} items)</span>
          </div>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            className="text-accent-400"
          >
            ▼
          </motion.div>
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-4 space-y-3"
            >
              {sources.map((source, index) => {
                const isSourceExpanded = expandedSources.has(index);
                const shouldTruncate = source.content && source.content.length > 300;

                return (
                  <Card key={index} variant="outlined" className="bg-white/50">
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-accent-900 text-sm flex-1 pr-2">
                          {source.title || 'Untitled Source'}
                        </h4>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-accent-500">
                            Score: {(source.relevanceScore * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      <div className="text-sm text-accent-700">
                        {shouldTruncate && !isSourceExpanded ? (
                          <>
                            <p className="line-clamp-3">{source.content}</p>
                            <button
                              onClick={() => toggleSourceExpansion(index)}
                              className="text-primary-600 hover:text-primary-700 text-xs font-medium mt-2 transition-colors"
                            >
                              Show more →
                            </button>
                          </>
                        ) : (
                          <>
                            <p className="whitespace-pre-wrap">{source.content}</p>
                            {shouldTruncate && (
                              <button
                                onClick={() => toggleSourceExpansion(index)}
                                className="text-primary-600 hover:text-primary-700 text-xs font-medium mt-2 transition-colors"
                              >
                                Show less ←
                              </button>
                            )}
                          </>
                        )}
                      </div>

                      {source.citation && (
                        <div className="mt-3 flex items-start space-x-1 text-xs text-accent-500">
                          <ExternalLink className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          <span className="break-all">{source.citation}</span>
                        </div>
                      )}

                      {source.date && (
                        <div className="mt-1 text-xs text-accent-500">
                          Date: {new Date(source.date).toLocaleDateString()}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
};

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result, onNewQuery }) => {
  const [isCopied, setIsCopied] = React.useState(false);

  const handleCopyResponse = async () => {
    try {
      await copyToClipboard(result.response);
      setIsCopied(true);

      // Reset after 2 seconds
      setTimeout(() => {
        setIsCopied(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const getStatusIcon = () => {
    if (result.requiresEscalation) {
      return <AlertTriangle className="w-5 h-5 text-warning-600" />;
    }
    return <CheckCircle className="w-5 h-5 text-success-600" />;
  };

  const getStatusText = () => {
    if (result.requiresEscalation) {
      return 'Requires Escalation';
    }
    return 'Resolved';
  };

  const getStatusColor = () => {
    if (result.requiresEscalation) {
      return 'text-warning-600 bg-warning-50 border-warning-200';
    }
    return 'text-success-600 bg-success-50 border-success-200';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Header with Status */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {getStatusIcon()}
              <span>Resolution Result</span>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor()}`}>
              {getStatusText()}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className={`text-2xl font-bold ${getConfidenceColor(result.confidence)}`}>
                {result.confidence}%
              </div>
              <div className="text-sm text-accent-600">Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-accent-900">
                {result.sources.totalCount}
              </div>
              <div className="text-sm text-accent-600">Total Sources</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-accent-900">
                {formatProcessingTime(result.processingTime)}
              </div>
              <div className="text-sm text-accent-600">Processing Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-accent-900 flex items-center justify-center">
                <Calendar className="w-5 h-5 mr-1" />
                {formatTimestamp(result.timestamp).split(' ')[0]}
              </div>
              <div className="text-sm text-accent-600">Date</div>
            </div>
          </div>

          {/* Confidence Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-accent-700">Overall Confidence</span>
              <span className={getConfidenceColor(result.confidence)}>{result.confidence}%</span>
            </div>
            <Progress
              value={result.confidence}
              max={100}
              variant={result.confidence >= 90 ? 'success' : result.confidence >= 70 ? 'warning' : 'error'}
              className="h-3"
            />
          </div>
        </CardContent>
      </Card>

      {/* Source Overview */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5" />
            <span>Source Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SourceCard
              title="Local Knowledge Base"
              count={result.sources.localCount}
              icon="📚"
              color="border-primary-200"
            />
            <SourceCard
              title="Web Search"
              count={result.sources.webCount}
              icon="🌐"
              color="border-accent-200"
            />
            <SourceCard
              title="Twitter Updates"
              count={result.sources.twitterCount}
              icon="📱"
              color="border-success-200"
            />
            <SourceCard
              title="LLM Reasoning"
              count={result.sources.llmCount}
              icon="🤖"
              color="border-warning-200"
            />
          </div>
        </CardContent>
      </Card>

      {/* Main Response */}
      <Card variant="glass">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>AI Resolution</span>
            </CardTitle>
            <motion.div
              animate={{ scale: isCopied ? [1, 1.1, 1] : 1 }}
              transition={{ duration: 0.3 }}
            >
              <Button
                variant={isCopied ? "success" : "outline"}
                size="sm"
                onClick={handleCopyResponse}
                className={`flex items-center space-x-2 transition-all duration-300 ${
                  isCopied
                    ? 'bg-success-600 text-white border-success-600 hover:bg-success-700'
                    : 'hover:bg-accent-100'
                }`}
              >
                {isCopied ? (
                  <>
                    <motion.div
                      initial={{ rotate: -180, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Check className="w-4 h-4" />
                    </motion.div>
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy</span>
                  </>
                )}
              </Button>
            </motion.div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.response}
            </ReactMarkdown>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Sources */}
      <div className="space-y-4">
        <SourceDetails
          sources={result.detailedSources?.localSources || []}
          title="📚 Local Knowledge Base Sources"
          icon="📚"
        />
        <SourceDetails
          sources={result.detailedSources?.webSources || []}
          title="🌐 Web Search Results"
          icon="🌐"
        />
        <SourceDetails
          sources={result.detailedSources?.twitterSources || []}
          title="📱 Twitter Updates"
          icon="📱"
        />
        <SourceDetails
          sources={result.detailedSources?.llmSources || []}
          title="🤖 LLM Reasoning Analysis"
          icon="🤖"
        />
      </div>

      {/* Errors */}
      {result.errors && result.errors.length > 0 && (
        <Card variant="outlined" className="border-error-200 bg-error-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-error-700">
              <XCircle className="w-5 h-5" />
              <span>Processing Warnings</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {result.errors.map((error, index) => (
                <div key={index} className="flex items-start space-x-2 text-sm text-error-700">
                  <span className="text-error-500 mt-0.5">•</span>
                  <span>{error}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-center">
        <Button onClick={onNewQuery} size="lg" className="min-w-[200px]">
          Submit New Query
        </Button>
      </div>
    </motion.div>
  );
};

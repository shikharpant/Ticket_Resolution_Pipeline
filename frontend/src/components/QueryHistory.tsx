import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  Clock,
  History,
  Trash2,
  Search,
  ChevronDown,
  ChevronRight,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { QueryHistory, QueryResult } from '@/types';
import { formatTimestamp } from '@/lib/utils';

interface QueryHistoryProps {
  history: QueryHistory[];
  onSelectQuery: (query: QueryHistory) => void;
  onClearHistory: () => void;
}

const QueryHistoryItem: React.FC<{
  query: QueryHistory;
  result?: QueryResult;
  isSelected: boolean;
  onSelect: () => void;
}> = ({ query, result, isSelected, onSelect }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        variant={isSelected ? "elevated" : "glass"}
        className={`cursor-pointer transition-all duration-200 ${
          isSelected ? 'ring-2 ring-primary-500' : 'hover:shadow-lg'
        }`}
        onClick={onSelect}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-accent-900 truncate mb-1">
                {query.query}
              </h4>
              <div className="flex items-center space-x-4 text-sm text-accent-600">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3" />
                  <span>{formatTimestamp(query.timestamp)}</span>
                </div>
                {query.processingTime && (
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{query.processingTime}s</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {query.status === 'completed' && result && (
                <div className={`text-xs px-2 py-1 rounded-full ${
                  result.confidence >= 90
                    ? 'bg-success-100 text-success-700'
                    : result.confidence >= 70
                    ? 'bg-warning-100 text-warning-700'
                    : 'bg-error-100 text-error-700'
                }`}>
                  {result.confidence}% confidence
                </div>
              )}
              {query.status === 'error' && (
                <div className="text-xs px-2 py-1 rounded-full bg-error-100 text-error-700">
                  Error
                </div>
              )}
              {query.status === 'processing' && (
                <div className="text-xs px-2 py-1 rounded-full bg-primary-100 text-primary-700">
                  Processing
                </div>
              )}
            </div>
          </div>

          <div className="text-sm text-accent-600 mb-2">
            Category: {query.category}
          </div>

          {query.status === 'completed' && result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{
                opacity: isExpanded ? 1 : 0,
                height: isExpanded ? 'auto' : 0
              }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-2 mt-2 border-t border-accent-200">
                <p className="text-sm text-accent-700 line-clamp-3">
                  {result.response}
                </p>
                <div className="flex items-center justify-between mt-2 text-xs text-accent-500">
                  <span>
                    {result.sources.totalCount} sources used
                  </span>
                  <span>
                    Processing time: {result.processingTime}s
                  </span>
                </div>
              </div>
            </motion.div>
          )}

          {query.status === 'error' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{
                opacity: isExpanded ? 1 : 0,
                height: isExpanded ? 'auto' : 0
              }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-2 mt-2 border-t border-error-200">
                <div className="flex items-center space-x-2 text-error-700 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>This query encountered an error during processing.</span>
                </div>
              </div>
            </motion.div>
          )}

          {(query.status === 'completed' || query.status === 'error') && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium mt-2 flex items-center space-x-1"
            >
              {isExpanded ? (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronRight className="w-4 h-4" />
                  Show More
                </>
              )}
            </button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export const QueryHistorySidebar: React.FC<QueryHistoryProps> = ({
  history,
  onSelectQuery,
  onClearHistory
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'confidence'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filter and sort history
  const filteredHistory = history
    .filter(query =>
      query.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      query.category.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let comparison = 0;

      if (sortBy === 'date') {
        comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      } else if (sortBy === 'confidence' && a.result && b.result) {
        comparison = a.result.confidence - b.result.confidence;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });

  const handleSort = (field: 'date' | 'confidence') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-accent-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-accent-900 flex items-center space-x-2">
            <History className="w-5 h-5" />
            <span>Query History</span>
          </h2>
          {history.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onClearHistory}
              className="text-error-600 hover:text-error-700"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-accent-400" />
          <input
            type="text"
            placeholder="Search queries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-accent-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* Sort Controls */}
        <div className="flex items-center justify-between mt-3">
          <span className="text-sm text-accent-600">
            {filteredHistory.length} {filteredHistory.length === 1 ? 'query' : 'queries'}
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleSort('date')}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                sortBy === 'date'
                  ? 'bg-accent-100 text-accent-700'
                  : 'hover:bg-accent-50 text-accent-600'
              }`}
            >
              Date
              {sortBy === 'date' && (
                <span className="ml-1">{sortOrder === 'desc' ? '↓' : '↑'}</span>
              )}
            </button>
            <button
              onClick={() => handleSort('confidence')}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                sortBy === 'confidence'
                  ? 'bg-accent-100 text-accent-700'
                  : 'hover:bg-accent-50 text-accent-600'
              }`}
            >
              Confidence
              {sortBy === 'confidence' && (
                <span className="ml-1">{sortOrder === 'desc' ? '↓' : '↑'}</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <AnimatePresence>
          {filteredHistory.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8"
            >
              <History className="w-12 h-12 mx-auto text-accent-400 mb-4" />
              <p className="text-accent-600">No queries yet</p>
              <p className="text-sm text-accent-500 mt-2">
                Submit your first GST query to see it here
              </p>
            </motion.div>
          ) : (
            filteredHistory.map((query) => (
              <QueryHistoryItem
                key={query.id}
                query={query}
                result={query.result}
                isSelected={false}
                onSelect={() => onSelectQuery(query)}
              />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

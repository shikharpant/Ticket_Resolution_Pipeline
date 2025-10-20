import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Send, FileText, HelpCircle } from 'lucide-react';

const GST_CATEGORIES = [
  'Account Aggregators (AA) - FIU',
  'Annual Aggregate Turnover (AATO)',
  'Assessment and Adjudication - determination of tax - DRC06',
  'Assessment and Adjudication - DRC03',
  'Assessment and Adjudication - DRC07',
  'Assessment and Adjudication - Penalty',
  'Assessment and Adjudication - Rectification',
  'Assessment and Adjudication - Restoration of Provisional Attachment',
  'Assessment and Adjudication - Summary Assessment - ASMT10',
  'Assessment and Adjudication - Summary Assessment - ASMT17',
  'CMP-08',
  'DCR',
  'DRC-03A - filing',
  'Enforcement-FO',
  'Form GST SRM-1',
  'GSP-API-Refunds',
  'GSP-API-Registration',
  'GSP-API-Returns-GSTR1',
  'GSP-API-Returns-GSTR4',
  'GSP-API-Returns-IMS',
  'GSP-API-Sandbox',
  'GSTN-MCA Integration',
  'ICEGATE',
  'Issues related to Waiver Scheme',
  'Online Filing of Annexure V',
  'Online Refund-RFD01',
  'Payments',
  'Payments - PMT09',
  'Refund - Exports',
  'Refunds - RFD01A',
  'Refunds - RFD10',
  'Registration - Amendment of core fields',
  'Registration - Amendment of non-core fields',
  'Registration - Amendment of non-core fields - Maps',
  'Registration - Cancellation application',
  'Registration - Composition',
  'Registration - Migration',
  'Registration - New Registration',
  'Registration - New Registration - Maps',
  'Registration - Register_Update DSC',
  'Registration - Search Taxpayer',
  'Registration - SRM I / SRM II - Pan Masala',
  'Registration - TDS application',
  'Registration- Revocation of cancellation',
  'Registration- Suspension of GSTIN',
  'Returns - GSTR1 Offline Filing',
  'Returns - GSTR1 Online Filing',
  'Returns - GSTR10',
  'Returns - GSTR2A',
  'Returns - GSTR3B',
  'Returns - GSTR4',
  'Returns - GSTR4 Annual',
  'Returns - GSTR4A',
  'Returns - GSTR5',
  'Returns - GSTR6',
  'Returns - GSTR7',
  'Returns - GSTR8',
  'Returns - GSTR9',
  'Returns - GSTR9C Offline Filing',
  'Returns - ITC01',
  'Returns - ITC02',
  'Returns - ITC03',
  'Returns - ITC04 Offline Filing',
  'Returns - Tran1',
  'Returns - Tran2',
  'Returns GSTR1',
  'Returns GSTR7',
  'Returns IMPORTS',
  'Returns-GSTR-2B',
  'Returns-IMS',
  'Returns-Tax Liabilities and ITC Comparison',
  'SMS related issue',
  'Others'
];

interface QueryFormProps {
  onSubmit: (query: string, category: string) => void;
  isDisabled?: boolean;
}

export const QueryForm: React.FC<QueryFormProps> = ({ onSubmit, isDisabled = false }) => {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      return;
    }

    if (!category) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(query.trim(), category);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setQuery('');
    setCategory('');
  };

  return (
    <Card variant="glass" className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <FileText className="w-5 h-5" />
          <span>Submit Your GST Query</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="category" className="block text-sm font-medium text-accent-700">
              Select Category <span className="text-error-500">*</span>
            </label>
            <Select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={isDisabled || isSubmitting}
              error={!category && isSubmitting}
            >
              <option value="">Choose a category...</option>
              {GST_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <label htmlFor="query" className="block text-sm font-medium text-accent-700">
              Your Query <span className="text-error-500">*</span>
            </label>
            <Textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Example: How do I file GSTR-1 for quarterly filing? What are the due dates? Include relevant details about your GST issue..."
              rows={4}
              disabled={isDisabled || isSubmitting}
              error={!query.trim() && isSubmitting}
              className="resize-none"
            />
            <p className="text-xs text-accent-500">
              Be specific about your GST issue. Include relevant dates, error messages, or specific context for better resolution.
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-accent-600">
              <HelpCircle className="w-4 h-4" />
              <span>All fields marked with * are required</span>
            </div>

            <div className="flex items-center space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleReset}
                disabled={isDisabled || isSubmitting}
              >
                Clear
              </Button>

              <Button
                type="submit"
                disabled={isDisabled || isSubmitting || !query.trim() || !category}
                loading={isSubmitting}
                className="min-w-[120px]"
              >
                <Send className="w-4 h-4 mr-2" />
                Submit Query
              </Button>
            </div>
          </div>
        </form>

        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-6 p-4 bg-primary-50 rounded-lg border border-primary-200"
        >
          <h4 className="font-medium text-primary-900 mb-2">💡 Tips for Better Results:</h4>
          <ul className="text-sm text-primary-700 space-y-1">
            <li>• Include specific GST form numbers (GSTR-1, GSTR-3B, etc.)</li>
            <li>• Mention relevant dates and timeframes</li>
            <li>• Include any error messages you're seeing</li>
            <li>• Specify your taxpayer type if relevant</li>
            <li>• Provide context about your business activities if applicable</li>
          </ul>
        </motion.div>
      </CardContent>
    </Card>
  );
};

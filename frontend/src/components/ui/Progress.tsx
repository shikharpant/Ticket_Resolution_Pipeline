import React from 'react';
import { cn } from '@/lib/utils';

export interface ProgressProps {
  value?: number;
  max?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'error';
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, size = 'md', variant = 'default', ...props }, ref) => {
    const sizeClasses = {
        sm: 'h-1',
        md: 'h-2',
        lg: 'h-3'
    };

    const variantClasses = {
        default: 'bg-primary-200',
        success: 'bg-success-200',
        warning: 'bg-warning-200',
        error: 'bg-error-200'
    };

    const progressVariantClasses = {
        default: 'bg-primary-600',
        success: 'bg-success-600',
        warning: 'bg-warning-600',
        error: 'bg-error-600'
    };

    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
        <div
            ref={ref}
            className={cn(
                'relative w-full overflow-hidden rounded-full',
                sizeClasses[size],
                variantClasses[variant],
                className
            )}
            {...props}
        >
            <div
                className={cn(
                    'h-full transition-all duration-500 ease-out rounded-full',
                    progressVariantClasses[variant]
                )}
                style={{ width: `${percentage}%` }}
            />
        </div>
    );
  }
);

Progress.displayName = 'Progress';

export { Progress };
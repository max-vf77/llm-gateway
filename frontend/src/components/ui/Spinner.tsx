import React from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ 
  size = 'md', 
  className,
  text 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-2">
        <Loader2 
          className={clsx(
            'animate-spin text-primary-600',
            sizeClasses[size]
          )} 
        />
        {text && (
          <p className="text-sm text-gray-600">{text}</p>
        )}
      </div>
    </div>
  );
};

// Компонент для полноэкранной загрузки
export const FullScreenSpinner: React.FC<{ text?: string }> = ({ text }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white bg-opacity-75">
      <Spinner size="xl" text={text} />
    </div>
  );
};

// Компонент для загрузки в контейнере
export const ContainerSpinner: React.FC<{ 
  text?: string; 
  className?: string;
  minHeight?: string;
}> = ({ text, className, minHeight = 'h-32' }) => {
  return (
    <div className={clsx('flex items-center justify-center', minHeight, className)}>
      <Spinner size="lg" text={text} />
    </div>
  );
};

export default Spinner;
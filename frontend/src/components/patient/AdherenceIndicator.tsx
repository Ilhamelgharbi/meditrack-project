import React from 'react';

interface AdherenceIndicatorProps {
  adherence: number;
  className?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md';
}

const AdherenceIndicator: React.FC<AdherenceIndicatorProps> = ({
  adherence,
  className = '',
  showPercentage = true,
  size = 'md'
}) => {
  const getAdherenceColor = (adherence: number) => {
    if (adherence >= 80) return 'text-emerald-600';
    if (adherence >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getBarColor = (adherence: number) => {
    if (adherence >= 80) return 'bg-emerald-500';
    if (adherence >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const barHeight = size === 'sm' ? 'h-1.5' : 'h-2';

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`w-16 ${barHeight} bg-slate-200 rounded-full overflow-hidden`}>
        <div
          className={`${barHeight} rounded-full transition-all duration-300 ${getBarColor(adherence)}`}
          style={{ width: `${Math.min(adherence, 100)}%` }}
        ></div>
      </div>
      {showPercentage && (
        <span className={`text-sm font-semibold ${getAdherenceColor(adherence)}`}>
          {Math.round(adherence)}%
        </span>
      )}
    </div>
  );
};

export default AdherenceIndicator;
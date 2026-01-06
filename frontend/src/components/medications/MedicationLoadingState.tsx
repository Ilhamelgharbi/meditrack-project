// src/components/medications/MedicationLoadingState.tsx
import React from 'react';
import { Loader, Pill } from 'lucide-react';

interface MedicationLoadingStateProps {
  type?: 'spinner' | 'skeleton';
  count?: number;
  className?: string;
}

export const MedicationLoadingState: React.FC<MedicationLoadingStateProps> = ({
  type = 'spinner',
  count = 3,
  className = ''
}) => {
  if (type === 'spinner') {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  // Skeleton loading
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-white border border-slate-100 rounded-lg p-4 animate-pulse">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-slate-200 rounded-lg flex items-center justify-center">
              <Pill className="text-slate-300" size={20} />
            </div>
            <div className="flex-1">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-slate-200 rounded w-1/2"></div>
            </div>
            <div className="w-16 h-6 bg-slate-200 rounded-full"></div>
          </div>
        </div>
      ))}
    </div>
  );
};
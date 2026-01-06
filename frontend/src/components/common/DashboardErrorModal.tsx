// src/components/common/DashboardErrorModal.tsx
import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Card } from './Card';

interface DashboardErrorModalProps {
  title?: string;
  subtitle?: string;
  error: string;
  onRetry: () => void;
  retryButtonText?: string;
  className?: string;
}

export const DashboardErrorModal: React.FC<DashboardErrorModalProps> = ({
  title = "Doctor Dashboard",
  subtitle = "Error loading analytics",
  error,
  onRetry,
  retryButtonText = "Try Again",
  className = ''
}) => {
  return (
    <div className={`space-y-8 animate-fadeIn ${className}`}>
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        <p className="text-slate-500 mt-1">{subtitle}</p>
      </div>
      <Card className="p-8 text-center">
        <AlertTriangle size={48} className="text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          {retryButtonText}
        </button>
      </Card>
    </div>
  );
};
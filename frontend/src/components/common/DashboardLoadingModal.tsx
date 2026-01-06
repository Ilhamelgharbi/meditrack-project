// src/components/common/DashboardLoadingModal.tsx
import React from 'react';
import { Card } from './Card';

interface DashboardLoadingModalProps {
  title?: string;
  subtitle?: string;
  className?: string;
}

export const DashboardLoadingModal: React.FC<DashboardLoadingModalProps> = ({
  title = "Doctor Dashboard",
  subtitle = "Loading analytics...",
  className = ''
}) => {
  return (
    <div className={`space-y-8 animate-fadeIn ${className}`}>
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        <p className="text-slate-500 mt-1">{subtitle}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-4 bg-slate-200 rounded w-20"></div>
                <div className="h-8 bg-slate-200 rounded w-16"></div>
                <div className="h-3 bg-slate-200 rounded w-24"></div>
              </div>
              <div className="w-12 h-12 bg-slate-200 rounded-xl"></div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
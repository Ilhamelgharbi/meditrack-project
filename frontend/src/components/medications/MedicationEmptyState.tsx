// src/components/medications/MedicationEmptyState.tsx
import React from 'react';
import { Pill } from 'lucide-react';

interface MedicationEmptyStateProps {
  title?: string;
  message?: string;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  className?: string;
}

export const MedicationEmptyState: React.FC<MedicationEmptyStateProps> = ({
  title = 'No medications found',
  message = 'Medications will appear here once prescribed',
  icon: Icon = Pill,
  className = ''
}) => {
  return (
    <div className={`text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200 ${className}`}>
      <Icon size={48} className="mx-auto mb-4 text-slate-300" />
      <p className="font-medium text-slate-900 mb-2">{title}</p>
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
};
// UNUSED COMPONENT - This component is not used anywhere in the codebase
// src/components/medications/MedicationList.tsx
import React from 'react';
import { Pill, Loader } from 'lucide-react';
import type { MedicationListProps } from './types';
import { MedicationCard } from './MedicationCard';

export const MedicationList: React.FC<MedicationListProps> = ({
  medications,
  onView,
  onEdit,
  onDelete,
  loading = false,
  emptyMessage = 'No medications found',
  showActions = true,
  compact = false,
  className = ''
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  if (medications.length === 0) {
    return (
      <div className={`text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200 ${className}`}>
        <Pill size={48} className="mx-auto mb-4 text-slate-300" />
        <p className="font-medium text-slate-900 mb-2">{emptyMessage}</p>
        <p className="text-sm text-slate-500">Medications will appear here once prescribed</p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className={`space-y-3 ${className}`}>
        {medications.map((medication) => (
          <MedicationCard
            key={medication.id}
            medication={medication}
            onView={onView}
            onEdit={onEdit}
            onDelete={onDelete}
            showActions={showActions}
            compact={true}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
      {medications.map((medication) => (
        <MedicationCard
          key={medication.id}
          medication={medication}
          onView={onView}
          onEdit={onEdit}
          onDelete={onDelete}
          showActions={showActions}
          compact={false}
        />
      ))}
    </div>
  );
};
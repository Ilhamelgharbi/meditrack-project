// UNUSED COMPONENT - This component is not used anywhere in the codebase
// src/components/medications/MedicationStats.tsx
import React from 'react';
import { StatCard } from '../common/StatCard';
import { Pill, CheckCircle, Clock, XCircle } from 'lucide-react';
import type { MedicationStatsProps } from './types';
import type { PatientMedicationDetailed } from '../../types/medications.types';

const statConfigs = [
  {
    key: 'total',
    title: 'Total Medications',
    icon: Pill,
    color: 'bg-blue-500',
    getValue: (medications: PatientMedicationDetailed[]) => medications.length,
    getTrend: (value: number) => `${value} total`
  },
  {
    key: 'active',
    title: 'Active',
    icon: CheckCircle,
    color: 'bg-emerald-500',
    getValue: (medications: PatientMedicationDetailed[]) => medications.filter(m => m.status === 'active').length,
    getTrend: (value: number) => `${value} currently active`
  },
  {
    key: 'pending',
    title: 'Pending',
    icon: Clock,
    color: 'bg-amber-500',
    getValue: (medications: PatientMedicationDetailed[]) => medications.filter(m => m.status === 'pending').length,
    getTrend: (value: number) => `${value} awaiting start`
  },
  {
    key: 'stopped',
    title: 'Stopped',
    icon: XCircle,
    color: 'bg-slate-500',
    getValue: (medications: PatientMedicationDetailed[]) => medications.filter(m => m.status === 'stopped').length,
    getTrend: (value: number) => `${value} completed`
  }
];

export const MedicationStats: React.FC<MedicationStatsProps> = ({
  medications,
  className = ''
}) => {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-4 gap-6 ${className}`}>
      {statConfigs.map((stat) => {
        const value = stat.getValue(medications);
        const trend = stat.getTrend(value);

        return (
          <StatCard
            key={stat.key}
            title={stat.title}
            value={value}
            icon={stat.icon}
            color={stat.color}
            trend={trend}
          />
        );
      })}
    </div>
  );
};
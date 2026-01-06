// src/components/medications/MedicationStatusBadge.tsx
import React from 'react';
import { CheckCircle, Clock, XCircle } from 'lucide-react';
import type { MedicationStatusBadgeProps } from './types';

const statusConfig = {
  active: {
    label: 'Active',
    icon: CheckCircle,
    className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    iconClass: 'text-emerald-600'
  },
  pending: {
    label: 'PENDING',
    icon: Clock,
    className: 'bg-amber-50 text-amber-700 border-amber-200',
    iconClass: 'text-amber-600'
  },
  stopped: {
    label: 'Stopped',
    icon: XCircle,
    className: 'bg-red-50 text-red-700 border-red-200',
    iconClass: 'text-red-600'
  }
};

export const MedicationStatusBadge: React.FC<MedicationStatusBadgeProps> = ({
  status,
  className = ''
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${config.className} ${className}`}>
      <Icon size={12} className={config.iconClass} />
      {config.label}
    </span>
  );
};
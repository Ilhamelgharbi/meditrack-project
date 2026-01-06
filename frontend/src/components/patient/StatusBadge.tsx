import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'stable': return 'bg-emerald-50 text-emerald-700 border-emerald-100';
      case 'critical': return 'bg-red-50 text-red-700 border-red-100';
      case 'under_observation': return 'bg-amber-50 text-amber-700 border-amber-100';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'stable': return 'Stable';
      case 'critical': return 'Critical';
      case 'under_observation': return 'Under Observation';
      default: return status;
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusColor(status)} ${className}`}>
      {getStatusDisplay(status)}
    </span>
  );
};

export default StatusBadge;
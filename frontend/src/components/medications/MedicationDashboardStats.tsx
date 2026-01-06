// src/components/medications/MedicationDashboardStats.tsx
import React from 'react';
import { StatCard } from '../common/StatCard';
import { Pill, CheckCircle, Clock, XCircle } from 'lucide-react';

interface MedicationDashboardStatsProps {
  total: number;
  active: number;
  pending: number;
  stopped: number;
  className?: string;
}

export const MedicationDashboardStats: React.FC<MedicationDashboardStatsProps> = ({
  total,
  active,
  pending,
  stopped,
  className = ''
}) => {
  const stats = [
    {
      title: 'Total Medications',
      value: total,
      icon: Pill,
      color: 'bg-blue-500',
      trend: `${active} active`
    },
    {
      title: 'Active',
      value: active,
      icon: CheckCircle,
      color: 'bg-emerald-500',
      trend: 'Currently taken'
    },
    {
      title: 'Pending',
      value: pending,
      icon: Clock,
      color: 'bg-amber-500',
      trend: 'Awaiting start'
    },
    {
      title: 'Stopped',
      value: stopped,
      icon: XCircle,
      color: 'bg-slate-500',
      trend: 'Completed'
    }
  ];

  return (
    <div className={`grid grid-cols-2 md:grid-cols-4 gap-6 ${className}`}>
      {stats.map((stat, index) => (
        <StatCard
          key={index}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          color={stat.color}
          trend={stat.trend}
        />
      ))}
    </div>
  );
};
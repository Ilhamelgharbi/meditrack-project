// src/components/common/StatCard.tsx
import React from 'react';
import { Card } from './Card';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
  trend?: string;
  subtitle?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  color,
  trend,
  subtitle,
  className = ''
}) => {
  return (
    <Card
      variant="elevated"
      className={`hover:shadow-md transition-shadow duration-200 border-l-4 border-l-transparent hover:border-l-[#2A7EF0] ${className}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-slate-900">{value}</h3>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
          )}
          {trend && (
            <span className="inline-block mt-2 text-xs font-medium px-2 py-1 rounded-full bg-slate-100 text-slate-600">
              {trend}
            </span>
          )}
        </div>
        <div className={`p-3 rounded-xl ${color} text-white shadow-lg shadow-blue-100`}>
          <Icon size={24} />
        </div>
      </div>
    </Card>
  );
};
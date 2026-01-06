import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { Card } from '../common/Card';

export interface InfoItem {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color?: string;
  unit?: string;
}

interface InfoCardProps {
  title: string;
  items: InfoItem[];
  columns?: number;
  className?: string;
}

export const InfoCard: React.FC<InfoCardProps> = ({
  title,
  items,
  columns = 2,
  className = ''
}) => {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4'
  };

  return (
    <Card title={title} className={className}>
      <div className={`grid ${gridCols[columns as keyof typeof gridCols]} gap-4`}>
        {items.map((item, index) => (
          <div key={index} className="p-4 bg-slate-50 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 mb-2 text-slate-400">
              <item.icon size={16} />
              <span className="text-xs font-bold uppercase tracking-wider">{item.label}</span>
            </div>
            <p className={`text-xl font-bold text-slate-900 ${item.color || ''}`}>
              {item.value}
              {item.unit && <span className="text-xs font-normal text-slate-500 ml-1">{item.unit}</span>}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
};
// src/components/common/AdherenceStatsCard.tsx
import React from 'react';
import { Card } from './Card';
import { getAdherenceBgColor, getAdherenceColor, getAdherenceIcon } from './AdherenceColorUtils';
import {
  Star, TrendingUp, Activity, AlertCircle,
  Zap, Clock, Target
} from 'lucide-react';

interface AdherenceStatsCardProps {
  type: 'score' | 'streak' | 'onTime' | 'bestStreak';
  value: number;
  totalTaken?: number;
  totalScheduled?: number;
  className?: string;
  variant?: 'default' | 'compact';
}

const iconMap = {
  Star,
  TrendingUp,
  Activity,
  AlertCircle,
  Zap,
  Clock,
  Target
};

export const AdherenceStatsCard: React.FC<AdherenceStatsCardProps> = ({
  type,
  value,
  totalTaken,
  totalScheduled,
  className = '',
  variant = 'default'
}) => {
  const getCardConfig = () => {
    switch (type) {
      case 'score':
        return {
          title: 'Adherence Score',
          iconName: getAdherenceIcon(value),
          bgColor: getAdherenceBgColor(value),
          textColor: getAdherenceColor(value),
          subtitle: totalTaken !== undefined && totalScheduled !== undefined
            ? `${totalTaken}/${totalScheduled} doses`
            : undefined,
          gradient: 'from-primary-100 to-primary-200',
          iconBg: value >= 80 ? 'bg-green-100' : value >= 60 ? 'bg-yellow-100' : 'bg-red-100',
          iconColor: value >= 80 ? 'text-green-600' : value >= 60 ? 'text-yellow-600' : 'text-red-600'
        };
      case 'streak':
        return {
          title: 'Current Streak',
          iconName: 'Zap',
          bgColor: 'bg-orange-50 border-orange-200',
          textColor: 'text-orange-600',
          subtitle: `${value === 1 ? 'day' : 'days'} in a row`,
          gradient: 'from-orange-100 to-orange-200',
          iconBg: 'bg-orange-100',
          iconColor: 'text-orange-600'
        };
      case 'onTime':
        return {
          title: 'On-Time Rate',
          iconName: 'Clock',
          bgColor: 'bg-green-50 border-green-200',
          textColor: 'text-green-600',
          subtitle: 'Taken on schedule',
          gradient: 'from-green-100 to-green-200',
          iconBg: 'bg-green-100',
          iconColor: 'text-green-600'
        };
      case 'bestStreak':
        return {
          title: 'Best Streak',
          iconName: 'Target',
          bgColor: 'bg-purple-50 border-purple-200',
          textColor: 'text-purple-600',
          subtitle: `${value === 1 ? 'day' : 'days'} record`,
          gradient: 'from-purple-100 to-purple-200',
          iconBg: 'bg-purple-100',
          iconColor: 'text-purple-600'
        };
      default:
        return {
          title: 'Unknown',
          iconName: 'Activity',
          bgColor: 'bg-gray-50 border-gray-200',
          textColor: 'text-gray-600',
          gradient: 'from-gray-100 to-gray-200',
          iconBg: 'bg-gray-100',
          iconColor: 'text-gray-600'
        };
    }
  };

  const config = getCardConfig();
  const IconComponent = iconMap[config.iconName as keyof typeof iconMap] || Activity;

  // Compact variant - matches dashboard style
  if (variant === 'compact') {
    return (
      <Card className={`p-5 hover:shadow-md transition-shadow ${className}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 font-medium">{config.title}</p>
            <p className={`text-3xl font-bold mt-1 ${config.textColor}`}>
              {type === 'score' || type === 'onTime' ? `${Math.round(value)}%` : value}
            </p>
            {config.subtitle && (
              <p className="text-xs text-slate-400 mt-1">{config.subtitle}</p>
            )}
          </div>
          <div className={`w-12 h-12 ${config.iconBg} rounded-xl flex items-center justify-center`}>
            <IconComponent className={`w-6 h-6 ${config.iconColor}`} />
          </div>
        </div>
      </Card>
    );
  }

  // Default variant - with gradient decoration
  return (
    <Card variant="elevated" className={`relative overflow-hidden ${className}`}>
      <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${config.gradient} rounded-bl-3xl opacity-50`}></div>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl ${config.iconBg}`}>
            <IconComponent className={`w-5 h-5 ${config.iconColor}`} />
          </div>
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-600">{config.title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className={`text-3xl font-bold ${config.textColor}`}>
              {type === 'score' || type === 'onTime' ? `${value.toFixed(1)}%` : value}
            </h3>
            {config.subtitle && (
              <span className="text-sm text-gray-500">{config.subtitle}</span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
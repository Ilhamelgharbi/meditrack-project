// src/components/common/AdherenceChart.tsx
import React from 'react';
import { Card } from './Card';
import { getAdherenceColor } from './AdherenceColorUtils';
import { BarChart3 } from 'lucide-react';
import { formatDateForDisplay } from '../../utils/timezone';

interface ChartDataItem {
  date: string;
  score: number;
  taken?: number;
  scheduled?: number;
  skipped?: number;
  missed?: number;
}

interface AdherenceChartProps {
  data: ChartDataItem[];
  title?: string;
  subtitle?: string;
  className?: string;
  showPercentage?: boolean;
  showLegend?: boolean;
  variant?: 'default' | 'compact' | 'mini';
}

// Helper to calculate percentages for stacked bar
const getStackedPercentages = (item: ChartDataItem) => {
  const scheduled = item.scheduled || 0;
  if (scheduled === 0) {
    return { taken: item.score, skipped: 0, missed: 0 };
  }
  const taken = item.taken || 0;
  const skipped = item.skipped || 0;
  // Calculate missed as remainder (scheduled - taken - skipped)
  const missed = item.missed !== undefined ? item.missed : Math.max(0, scheduled - taken - skipped);
  
  return {
    taken: (taken / scheduled) * 100,
    skipped: (skipped / scheduled) * 100,
    missed: (missed / scheduled) * 100
  };
};

export const AdherenceChart: React.FC<AdherenceChartProps> = ({
  data,
  title = "Adherence Trend",
  subtitle = "Daily adherence scores",
  className = '',
  showPercentage = true,
  showLegend = true,
  variant = 'default'
}) => {
  if (!data || data.length === 0) {
    return null;
  }

  // Check if we have detailed data (taken/scheduled/skipped/missed)
  const hasDetailedData = data.some(item => item.scheduled !== undefined && item.scheduled > 0);

  // Mini variant - vertical bar chart with day abbreviations
  if (variant === 'mini') {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="flex items-end justify-between gap-1 h-16">
          {data.slice(-7).map((item, index) => {
            const dayAbbrev = new Date(item.date).toLocaleDateString('en-US', { weekday: 'short' }).slice(0, 3);
            const pcts = getStackedPercentages(item);
            const total = pcts.taken + pcts.skipped + pcts.missed;
            const heightPercent = Math.max(total, 5);
            
            return (
              <div key={index} className="flex flex-col items-center flex-1">
                <div className="w-full flex flex-col-reverse items-end h-10 overflow-hidden rounded-t">
                  {hasDetailedData && total > 0 ? (
                    <>
                      {/* Taken - Green */}
                      {pcts.taken > 0 && (
                        <div
                          className="w-full bg-emerald-500 transition-all"
                          style={{ height: `${(pcts.taken / total) * heightPercent}%` }}
                          title={`Taken: ${pcts.taken.toFixed(0)}%`}
                        />
                      )}
                      {/* Skipped - Yellow */}
                      {pcts.skipped > 0 && (
                        <div
                          className="w-full bg-amber-400 transition-all"
                          style={{ height: `${(pcts.skipped / total) * heightPercent}%` }}
                          title={`Skipped: ${pcts.skipped.toFixed(0)}%`}
                        />
                      )}
                      {/* Missed - Red */}
                      {pcts.missed > 0 && (
                        <div
                          className="w-full bg-red-500 transition-all"
                          style={{ height: `${(pcts.missed / total) * heightPercent}%` }}
                          title={`Missed: ${pcts.missed.toFixed(0)}%`}
                        />
                      )}
                    </>
                  ) : (
                    <div
                      className={`w-full transition-all ${item.score >= 75 ? 'bg-emerald-500' : item.score >= 50 ? 'bg-amber-400' : 'bg-red-500'}`}
                      style={{ height: `${heightPercent}%` }}
                      title={`${item.score.toFixed(0)}%`}
                    />
                  )}
                </div>
                <span className="text-xs text-gray-500 mt-1">{dayAbbrev}</span>
              </div>
            );
          })}
        </div>
        {showLegend && hasDetailedData && (
          <div className="flex items-center justify-center gap-4 mt-3 pt-2 border-t text-xs">
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-500" /><span className="text-gray-500">Taken</span></div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-400" /><span className="text-gray-500">Skipped</span></div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500" /><span className="text-gray-500">Missed</span></div>
          </div>
        )}
      </Card>
    );
  }

  // Compact variant - smaller with horizontal bars
  if (variant === 'compact') {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="space-y-2">
          {data.map((item, index) => {
            const dayAbbrev = new Date(item.date).toLocaleDateString('en-US', { weekday: 'short' });
            const pcts = getStackedPercentages(item);
            
            return (
              <div key={index} className="flex items-center gap-2">
                <div className="w-10 text-xs font-medium text-gray-500">{dayAbbrev}</div>
                <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden flex">
                  {hasDetailedData ? (
                    <>
                      {/* Taken - Green */}
                      {pcts.taken > 0 && (
                        <div
                          className="h-full bg-emerald-500 transition-all"
                          style={{ width: `${pcts.taken}%` }}
                          title={`Taken: ${pcts.taken.toFixed(0)}%`}
                        />
                      )}
                      {/* Skipped - Yellow */}
                      {pcts.skipped > 0 && (
                        <div
                          className="h-full bg-amber-400 transition-all"
                          style={{ width: `${pcts.skipped}%` }}
                          title={`Skipped: ${pcts.skipped.toFixed(0)}%`}
                        />
                      )}
                      {/* Missed - Red */}
                      {pcts.missed > 0 && (
                        <div
                          className="h-full bg-red-500 transition-all"
                          style={{ width: `${pcts.missed}%` }}
                          title={`Missed: ${pcts.missed.toFixed(0)}%`}
                        />
                      )}
                    </>
                  ) : (
                    <div
                      className={`h-full transition-all ${item.score >= 75 ? 'bg-emerald-500' : item.score >= 50 ? 'bg-amber-400' : 'bg-red-500'}`}
                      style={{ width: `${item.score}%` }}
                    />
                  )}
                </div>
                <div className="w-10 text-right">
                  <span className={`text-xs font-semibold ${getAdherenceColor(item.score)}`}>
                    {item.score.toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        {showLegend && hasDetailedData && (
          <div className="flex items-center justify-center gap-4 mt-3 pt-2 border-t text-xs">
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-500" /><span className="text-gray-500">Taken</span></div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-400" /><span className="text-gray-500">Skipped</span></div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500" /><span className="text-gray-500">Missed</span></div>
          </div>
        )}
      </Card>
    );
  }

  // Default variant
  return (
    <Card variant="elevated" className={className}>
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-blue-100 rounded-lg">
          <BarChart3 className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-gray-900">{title}</h2>
          <p className="text-sm text-gray-500">{subtitle}</p>
        </div>
      </div>

      <div className="space-y-3">
        {data.map((item, index) => {
          const pcts = getStackedPercentages(item);
          
          return (
            <div key={index} className="flex items-center gap-3">
              <div className="w-14 text-sm font-medium text-gray-600">
                {formatDateForDisplay(item.date)}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden flex">
                    {hasDetailedData ? (
                      <>
                        {/* Taken - Green */}
                        {pcts.taken > 0 && (
                          <div
                            className="h-full bg-emerald-500 transition-all duration-500"
                            style={{ width: `${pcts.taken}%` }}
                            title={`Taken: ${pcts.taken.toFixed(0)}%`}
                          />
                        )}
                        {/* Skipped - Yellow/Amber */}
                        {pcts.skipped > 0 && (
                          <div
                            className="h-full bg-amber-400 transition-all duration-500"
                            style={{ width: `${pcts.skipped}%` }}
                            title={`Skipped: ${pcts.skipped.toFixed(0)}%`}
                          />
                        )}
                        {/* Missed - Red */}
                        {pcts.missed > 0 && (
                          <div
                            className="h-full bg-red-500 transition-all duration-500"
                            style={{ width: `${pcts.missed}%` }}
                            title={`Missed: ${pcts.missed.toFixed(0)}%`}
                          />
                        )}
                      </>
                    ) : (
                      <div
                        className={`h-full transition-all duration-500 ${item.score >= 75 ? 'bg-emerald-500' : item.score >= 50 ? 'bg-amber-400' : 'bg-red-500'}`}
                        style={{ width: `${item.score}%` }}
                      />
                    )}
                  </div>
                  {showPercentage && (
                    <div className="w-10 text-right">
                      <span className={`text-sm font-bold ${getAdherenceColor(item.score)}`}>
                        {item.score.toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      {showLegend && hasDetailedData && (
        <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-gray-600">Taken</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-400" />
            <span className="text-gray-600">Skipped</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-gray-600">Missed</span>
          </div>
        </div>
      )}
    </Card>
  );
};
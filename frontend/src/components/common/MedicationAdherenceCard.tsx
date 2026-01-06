// src/components/common/MedicationAdherenceCard.tsx
import React, { useState, useEffect } from 'react';
import { getAdherenceBgColor, getAdherenceColor, getAdherenceBarColor } from './AdherenceColorUtils';
import { adherenceService } from '../../services/adherence.service';
import type { AdherenceStats } from '../../services/adherence.service';

interface PatientMedication {
  id: number;
  medication_id: number;
  dosage: string;
  instructions?: string;
  medication?: {
    id: number;
    name: string;
    form: string;
  };
}

interface MedicationAdherenceCardProps {
  medication: PatientMedication;
  patientId?: number;
  selectedPeriod: 'daily' | 'weekly' | 'monthly' | 'overall';
  className?: string;
}

export const MedicationAdherenceCard: React.FC<MedicationAdherenceCardProps> = ({
  medication,
  patientId,
  selectedPeriod,
  className = ''
}) => {
  const [stats, setStats] = useState<AdherenceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getPeriodLabel = (period: string): string => {
    switch (period) {
      case 'daily': return 'day';
      case 'weekly': return 'week';
      case 'monthly': return 'month';
      case 'overall': return 'period';
      default: return 'period';
    }
  };

  const clampedScore = Math.min(stats?.adherence_score || 0, 100);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        let medicationStats: AdherenceStats;

        if (patientId) {
          // Admin view: fetch stats for specific patient
          medicationStats = await adherenceService.getPatientAdherenceStats(
            patientId,
            selectedPeriod,
            medication.id
          );
        } else {
          // Patient view: fetch current user's stats
          medicationStats = await adherenceService.getStats(
            selectedPeriod,
            medication.id
          );
        }

        setStats(medicationStats);
      } catch (error) {
        console.error('Error fetching medication stats:', error);
        setError('Failed to load medication stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [medication.id, patientId, selectedPeriod]);

  if (loading) {
    return (
      <div className={`p-5 border border-gray-200 rounded-xl bg-white ${className}`}>
        <div className="animate-pulse">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="h-5 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
            </div>
            <div className="h-8 w-16 bg-gray-200 rounded"></div>
          </div>
          <div className="h-12 bg-gray-200 rounded-lg mb-4"></div>
          <div className="h-3 bg-gray-200 rounded-full"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className={`p-5 border border-red-200 rounded-xl bg-red-50 ${className}`}>
        <div className="text-center">
          <div className="text-red-600 mb-2">
            <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-sm font-medium text-red-800 mb-1">{medication.medication?.name}</h3>
          <p className="text-xs text-red-600">{error || 'Unable to load stats'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-5 border border-gray-200 rounded-xl hover:shadow-md transition-all duration-200 bg-white ${className}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-lg truncate">{medication.medication?.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{medication.dosage}</p>
        </div>
        <div className="text-right ml-4">
          <div className={`text-3xl font-bold ${getAdherenceColor(clampedScore)}`}>
            {clampedScore.toFixed(1)}%
          </div>
          <div className={`text-xs px-3 py-1 rounded-full font-medium mt-1 ${getAdherenceBgColor(clampedScore)} ${getAdherenceColor(clampedScore)}`}>
            {clampedScore >= 90 ? 'Excellent' : clampedScore >= 75 ? 'Good' : clampedScore >= 60 ? 'Fair' : 'Needs Attention'}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-600 mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="font-semibold text-gray-900">{stats.total_taken}</div>
            <div className="text-xs text-gray-500">Taken</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-gray-900">{stats.total_scheduled}</div>
            <div className="text-xs text-gray-500">Scheduled</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-gray-900">{stats.current_streak}</div>
            <div className="text-xs text-gray-500">Day Streak</div>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Adherence Progress</span>
          <span>{clampedScore.toFixed(1)}% this {getPeriodLabel(selectedPeriod)}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all duration-1000 ${getAdherenceBarColor(clampedScore)}`}
            style={{
              width: `${Math.max(clampedScore, 2)}%`,
              minWidth: clampedScore > 0 ? '4px' : '0px'
            }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-gray-400">
          <span>0%</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  );
};
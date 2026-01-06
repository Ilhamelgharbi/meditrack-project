import React, { useState } from 'react';
import { Eye, CheckCircle, AlertCircle, Pill } from 'lucide-react';
import type { MedicationCardProps } from './types';
import { MedicationImage } from './MedicationImage';
import { MedicationStatusBadge } from './MedicationStatusBadge';
import { useAuth } from '../../contexts/AuthContext';
import type { PatientMedicationDetailed } from '../../types/medications.types';

export const PatientMedicationCard: React.FC<MedicationCardProps & {
  onActivate?: (medication: PatientMedicationDetailed) => void;
}> = ({
  medication,
  onView,
  onActivate,
  showActions = true,
  compact = false,
  className = ''
}) => {
  const { user } = useAuth();
  const [isActivating, setIsActivating] = useState(false);

  const handleView = () => onView?.(medication);

  const handleActivate = async () => {
    if (!user || medication.status !== 'pending') return;

    try {
      setIsActivating(true);
      onActivate?.(medication);
    } catch (error) {
      console.error('Error activating medication:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to activate medication. Please try again.';
      alert(errorMessage);
    } finally {
      setIsActivating(false);
    }
  };

  if (compact) {
    return (
      <div className={`bg-white border border-slate-100 rounded-lg p-4 hover:shadow-md transition-all ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MedicationImage
              src={undefined}
              alt={medication.medication?.name || 'Medication'}
              size="sm"
            />
            <div>
              <h4 className="font-semibold text-slate-900 text-sm">
                {medication.medication?.name || 'Unknown Medication'}
              </h4>
              <p className="text-xs text-slate-500 capitalize">
                {medication.medication?.form} • {medication.dosage}
              </p>
            </div>
          </div>
          <MedicationStatusBadge status={medication.status} />
        </div>
        {showActions && (
          <div className="flex gap-2 mt-3 pt-3 border-t border-slate-100">
            <button
              onClick={handleView}
              className="flex-1 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1"
            >
              <Eye size={12} /> View
            </button>
            {medication.status === 'pending' && (
              <button
                onClick={handleActivate}
                disabled={isActivating}
                className="flex-1 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1 disabled:opacity-50"
              >
                <CheckCircle size={12} />
                {isActivating ? 'Starting...' : 'Start'}
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-100 hover:shadow-md hover:border-blue-200 transition-all overflow-hidden group flex flex-col h-full ${className}`}>
      {/* Card Image/Header */}
      <div className="h-24 bg-slate-100 relative overflow-hidden">
        <div className="w-full h-full flex items-center justify-center bg-blue-50 text-blue-200">
          <Pill size={32} />
        </div>
        <div className="absolute top-2 right-2">
          <MedicationStatusBadge status={medication.status} />
        </div>
        {medication.status === 'pending' && (
          <div className="absolute top-2 left-2">
            <div className="flex items-center gap-1 bg-amber-100 text-amber-700 px-2 py-1 rounded-full text-xs font-medium">
              <AlertCircle size={12} />
              Action Required
            </div>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="p-4 flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
            {medication.medication?.name || 'Unknown Medication'}
          </h3>
          <button className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-opacity">
            <Eye size={16} />
          </button>
        </div>

        <div className="space-y-2 mb-3 flex-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Pill size={14} className="text-blue-500" />
              <span className="font-medium capitalize">{medication.medication?.form}</span>
            </div>
            <span className="text-sm text-slate-600 font-medium">{medication.dosage}</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-50 p-2 rounded-lg">
              <p className="text-slate-500 font-medium uppercase tracking-wider">Frequency</p>
              <p className="text-slate-900 font-semibold">{medication.times_per_day}x per day</p>
            </div>
            <div className="bg-slate-50 p-2 rounded-lg">
              <p className="text-slate-500 font-medium uppercase tracking-wider">Start Date</p>
              <p className="text-slate-900 font-semibold text-xs">
                {new Date(medication.start_date).toLocaleDateString()}
              </p>
            </div>
          </div>

          {medication.end_date && (
            <div className="bg-slate-50 p-2 rounded-lg">
              <p className="text-slate-500 font-medium uppercase tracking-wider">End Date</p>
              <p className="text-slate-900 font-semibold text-xs">
                {new Date(medication.end_date).toLocaleDateString()}
              </p>
            </div>
          )}

          {medication.instructions && (
            <div className="flex items-start gap-2 text-xs text-blue-600 bg-blue-50 p-2 rounded-lg">
              <AlertCircle size={12} className="text-blue-500 mt-0.5 flex-shrink-0" />
              <span className="line-clamp-2">{medication.instructions}</span>
            </div>
          )}

          {medication.status === 'pending' && (
            <div className="flex items-start gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded-lg">
              <AlertCircle size={12} className="text-amber-500 mt-0.5 flex-shrink-0" />
              <span>This medication has been prescribed but not yet started. Confirm to begin taking it.</span>
            </div>
          )}
        </div>

        {/* Card Actions */}
        {showActions && (
          <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
            <button
              onClick={handleView}
              className="flex-1 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5"
            >
              <Eye size={14} /> View
            </button>
            {medication.status === 'pending' && (
              <button
                onClick={handleActivate}
                disabled={isActivating}
                className="flex-1 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <CheckCircle size={14} />
                {isActivating ? 'Starting...' : 'Start Taking'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
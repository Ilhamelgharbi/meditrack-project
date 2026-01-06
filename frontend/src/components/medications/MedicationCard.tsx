import React from 'react';
import { Eye, Edit2, Trash2, FileText } from 'lucide-react';
import type { MedicationCardProps } from './types';
import { MedicationImage } from './MedicationImage';
import { MedicationStatusBadge } from './MedicationStatusBadge';

export const MedicationCard: React.FC<MedicationCardProps> = ({
  medication,
  onView,
  onEdit,
  onDelete,
  showActions = true,
  compact = false,
  className = ''
}) => {
  const handleView = () => onView?.(medication);
  const handleEdit = () => onEdit?.(medication);
  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete ${medication.medication?.name}?`)) {
      onDelete?.(medication);
    }
  };

  // Determine card styling based on status for admin view
  const getCardClasses = () => {
    const baseClasses = 'rounded-lg p-4 hover:shadow-md transition-all';
    if (medication.status === 'pending') {
      return `${baseClasses} bg-amber-100 border border-amber-300`;
    }
    return `${baseClasses} bg-white border border-slate-100`;
  };

  if (compact) {
    return (
      <div className={`${getCardClasses()} ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MedicationImage
              src={undefined} // We'll add image support later
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
            {onEdit && (
              <button
                onClick={handleEdit}
                className="flex-1 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1"
              >
                <Edit2 size={12} /> Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={handleDelete}
                className="p-1.5 text-red-400 hover:bg-red-50 hover:text-red-600 rounded transition-colors"
              >
                <Trash2 size={12} />
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white border border-slate-100 rounded-xl shadow-sm hover:shadow-md transition-all overflow-hidden ${medication.status === 'pending' ? 'bg-amber-100 border-amber-300' : ''} ${className}`}>
      {/* Header with Image */}
      <div className="h-32 bg-gradient-to-r from-blue-50 to-indigo-50 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <MedicationImage
            src={undefined} // We'll add image support later
            alt={medication.medication?.name || 'Medication'}
            size="lg"
            className="opacity-80"
          />
        </div>
        <div className="absolute top-3 right-3">
          <MedicationStatusBadge status={medication.status} />
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              {medication.medication?.name || 'Unknown Medication'}
            </h3>
            <p className="text-sm text-slate-500 capitalize">
              {medication.medication?.form}
            </p>
          </div>
        </div>

        {/* Medication Details Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Dosage</p>
            <p className="text-sm font-semibold text-slate-900">{medication.dosage}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Frequency</p>
            <p className="text-sm font-semibold text-slate-900">{medication.times_per_day}x per day</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Start Date</p>
            <p className="text-sm font-semibold text-slate-900">
              {new Date(medication.start_date).toLocaleDateString()}
            </p>
          </div>
          {medication.end_date && (
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">End Date</p>
              <p className="text-sm font-semibold text-slate-900">
                {new Date(medication.end_date).toLocaleDateString()}
              </p>
            </div>
          )}
        </div>

        {/* Instructions */}
        {medication.instructions && (
          <div className="mb-4">
            <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded-lg">
              <FileText size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-blue-900 uppercase tracking-wider mb-1">Instructions</p>
                <p className="text-sm text-blue-800">{medication.instructions}</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2 pt-4 border-t border-slate-100">
            <button
              onClick={handleView}
              className="flex-1 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <Eye size={16} /> View Details
            </button>
            {onEdit && (
              <button
                onClick={handleEdit}
                className="flex-1 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Edit2 size={16} /> Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={handleDelete}
                className="p-2 text-red-400 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
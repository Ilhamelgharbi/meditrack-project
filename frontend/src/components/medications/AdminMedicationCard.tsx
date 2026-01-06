import React from 'react';
import { Eye, Edit2, Trash2, Pill } from 'lucide-react';
import type { AdminMedicationCardProps } from './types';
import { MedicationImage } from './MedicationImage';

export const AdminMedicationCard: React.FC<AdminMedicationCardProps> = ({
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
    if (confirm(`Are you sure you want to delete "${medication.name}"? This action cannot be undone.`)) {
      onDelete?.(medication);
    }
  };

  if (compact) {
    return (
      <div className={`bg-white border border-slate-100 rounded-lg p-4 hover:shadow-md transition-all ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MedicationImage
              src={undefined}
              alt={medication.name}
              size="sm"
            />
            <div>
              <h4 className="font-semibold text-slate-900 text-sm">{medication.name}</h4>
              <p className="text-xs text-slate-500 capitalize">{medication.form}</p>
            </div>
          </div>
          <span className="px-2 py-1 bg-emerald-50 text-emerald-600 text-xs font-medium rounded-full">Active</span>
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
    <div className={`bg-white rounded-xl shadow-sm border border-slate-100 hover:shadow-md hover:border-blue-200 transition-all overflow-hidden group flex flex-col h-full ${className}`}>
      {/* Card Image/Header */}
      <div className="h-24 bg-slate-100 relative overflow-hidden">
        <div className="w-full h-full flex items-center justify-center bg-blue-50 text-blue-200">
          <Pill size={32} />
        </div>
        <div className="absolute top-2 right-2">
          <span className="px-2 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm backdrop-blur-md bg-emerald-500/90 text-white">
            Active
          </span>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4 flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">{medication.name}</h3>
          <button className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-opacity">
            <Edit2 size={16} />
          </button>
        </div>

        <div className="space-y-2 mb-3 flex-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Pill size={14} className="text-blue-500" />
              <span className="font-medium capitalize">{medication.form}</span>
            </div>
            {medication.default_dosage && (
              <span className="text-sm text-slate-600 font-medium">{medication.default_dosage}</span>
            )}
          </div>

          {medication.side_effects && (
            <div className="flex items-start gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded-lg">
              <span className="line-clamp-2">{medication.side_effects}</span>
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
            <button
              onClick={handleEdit}
              className="flex-1 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5"
            >
              <Edit2 size={14} /> Edit
            </button>
            <button
              onClick={handleDelete}
              className="p-2 text-red-400 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
            >
              <Trash2 size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
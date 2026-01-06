// src/components/medications/MedicationDetails.tsx
import React from 'react';
import { X, FileText, AlertTriangle, User, Edit2, Trash2 } from 'lucide-react';
import type { MedicationDetailsProps } from './types';
import { MedicationImage } from './MedicationImage';
import { MedicationStatusBadge } from './MedicationStatusBadge';

export const MedicationDetails: React.FC<MedicationDetailsProps> = ({
  medication,
  onClose,
  onEdit,
  onDelete,
  showActions = true
}) => {
  const handleEdit = () => onEdit?.(medication);
  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete ${medication.medication?.name}?`)) {
      onDelete?.(medication);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="h-48 relative bg-slate-100 flex-shrink-0">
          <div className="absolute inset-0 flex items-center justify-center">
            <MedicationImage
              src={undefined} // We'll add image support later
              alt={medication.medication?.name || 'Medication'}
              size="xl"
              className="opacity-80"
            />
          </div>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-black/20 hover:bg-black/40 text-white rounded-full backdrop-blur-sm transition-colors"
          >
            <X size={20} />
          </button>
          <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/60 to-transparent p-6">
            <h2 className="text-3xl font-bold text-white mb-2">
              {medication.medication?.name || 'Unknown Medication'}
            </h2>
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 bg-white/20 backdrop-blur-md rounded text-white text-sm font-medium border border-white/10 capitalize">
                {medication.medication?.form}
              </span>
              <MedicationStatusBadge status={medication.status} />
            </div>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">Instructions</h4>
                    <div className="flex items-start gap-3 mb-2">
                        <FileText size={18} className="text-blue-500 mt-0.5" />
                        <div>
                            <p className="font-medium text-slate-900">{medication.times_per_day}x per day</p>
                            <p className="text-sm text-slate-500">Every {24/medication.times_per_day} hours</p>
                        </div>
                    </div>
                     <div className="flex items-start gap-3">
                        <FileText size={18} className="text-blue-500 mt-0.5" />
                        <p className="text-sm text-slate-700">{medication.instructions || 'Take as directed'}</p>
                    </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                     <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">Details</h4>
                     <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-600">Dosage</span>
                            <span className="font-bold text-slate-900">{medication.dosage}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-600">Start Date</span>
                            <span className="font-bold text-slate-900">{new Date(medication.start_date).toLocaleDateString()}</span>
                        </div>
                        {medication.end_date && (
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-600">End Date</span>
                                <span className="font-bold text-slate-900">{new Date(medication.end_date).toLocaleDateString()}</span>
                            </div>
                        )}
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-600">Status</span>
                            <MedicationStatusBadge status={medication.status} />
                        </div>
                     </div>
                </div>
            </div>

            {/* Side Effects */}
            {medication.medication?.side_effects && (
                <div className="mb-6">
                    <h4 className="text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
                        <AlertTriangle size={16} className="text-amber-500" />
                        Potential Side Effects
                    </h4>
                    <p className="text-slate-600 text-sm bg-amber-50 border border-amber-100 p-3 rounded-lg">
                        {medication.medication.side_effects}
                    </p>
                </div>
            )}

            {/* Warnings */}
            {medication.medication?.warnings && (
                <div className="mb-6">
                    <h4 className="text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
                        <AlertTriangle size={16} className="text-red-500" />
                        Important Warnings
                    </h4>
                    <p className="text-slate-600 text-sm bg-red-50 border border-red-100 p-3 rounded-lg">
                        {medication.medication.warnings}
                    </p>
                </div>
            )}

            {/* Assignment Info */}
            {medication.assigning_doctor && (
                <div className="mb-6">
                    <h4 className="text-sm font-bold text-slate-900 mb-2">Prescribed By</h4>
                    <div className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-100 rounded-lg">
                        <User size={16} className="text-slate-500" />
                        <div>
                            <p className="font-medium text-slate-900">{medication.assigning_doctor.full_name}</p>
                            <p className="text-sm text-slate-500">{medication.assigning_doctor.email}</p>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex justify-between text-xs text-slate-400 pt-4 border-t border-slate-100">
                <span>Started: {new Date(medication.start_date).toLocaleDateString()}</span>
                <span>Assigned: {new Date(medication.created_at).toLocaleDateString()}</span>
            </div>
        </div>

        {/* Modal Actions */}
        {showActions && (onEdit || onDelete) && (
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex gap-3 justify-end">
            {onDelete && (
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-600 text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <Trash2 size={16} /> Delete
              </button>
            )}
            {onEdit && (
              <button
                onClick={handleEdit}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <Edit2 size={16} /> Edit Medication
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
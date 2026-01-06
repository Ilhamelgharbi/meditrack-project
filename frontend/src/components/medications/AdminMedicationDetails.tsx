import React from 'react';
import { Edit, Trash2, X } from 'lucide-react';
import type { AdminMedicationDetailsProps } from './types';
import { MedicationImage } from './MedicationImage';

export const AdminMedicationDetails: React.FC<AdminMedicationDetailsProps> = ({
  medication,
  onClose,
  onEdit,
  onDelete,
  showActions = true
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="h-48 relative bg-slate-100 flex-shrink-0">
          <div className="absolute inset-0 flex items-center justify-center">
            <MedicationImage
              src={undefined}
              alt={medication.name}
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
            <h2 className="text-3xl font-bold text-white mb-2">{medication.name}</h2>
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 bg-white/20 backdrop-blur-md rounded text-white text-sm font-medium border border-white/10 capitalize">
                {medication.form}
              </span>
              <span className="px-2 py-1 bg-emerald-500/90 text-white text-sm font-medium rounded">
                Active
              </span>
            </div>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">Medication Details</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Form</span>
                  <span className="font-bold text-slate-900 capitalize">{medication.form}</span>
                </div>
                {medication.default_dosage && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Default Dosage</span>
                    <span className="font-bold text-slate-900">{medication.default_dosage}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Status</span>
                  <span className="px-2 py-1 bg-emerald-50 text-emerald-600 text-xs font-medium rounded-full">Active</span>
                </div>
              </div>
            </div>
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">Information</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Created</span>
                  <span className="font-bold text-slate-900">{new Date(medication.created_at).toLocaleDateString()}</span>
                </div>
                {medication.updated_at && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Updated</span>
                    <span className="font-bold text-slate-900">{new Date(medication.updated_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {medication.side_effects && (
            <div className="mb-6">
              <h4 className="text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
                <span className="text-amber-500">⚠️</span>
                Side Effects
              </h4>
              <p className="text-slate-600 text-sm bg-amber-50 border border-amber-100 p-3 rounded-lg">
                {medication.side_effects}
              </p>
            </div>
          )}

          {medication.warnings && (
            <div className="mb-6">
              <h4 className="text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
                <span className="text-red-500">⚠️</span>
                Important Warnings
              </h4>
              <p className="text-slate-600 text-sm bg-red-50 border border-red-100 p-3 rounded-lg">
                {medication.warnings}
              </p>
            </div>
          )}

          <div className="flex justify-between text-xs text-slate-400 pt-4 border-t border-slate-100">
            <span>Created: {new Date(medication.created_at).toLocaleDateString()}</span>
            {medication.updated_at && (
              <span>Updated: {new Date(medication.updated_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>

        {/* Modal Actions */}
        {showActions && (
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
            >
              Close
            </button>
            {onEdit && (
              <button
                onClick={() => onEdit(medication)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <Edit size={16} /> Edit Medication
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(medication)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <Trash2 size={16} /> Delete Medication
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
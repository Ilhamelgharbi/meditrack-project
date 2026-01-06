import React from 'react';
import { Trash2, X, AlertTriangle } from 'lucide-react';
import type { AdminMedicationDeleteProps } from './types';

export const AdminMedicationDelete: React.FC<AdminMedicationDeleteProps> = ({
  medication,
  onClose,
  onConfirm,
  isLoading = false
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="h-24 relative bg-gradient-to-r from-red-600 to-red-700 flex-shrink-0">
          <div className="absolute inset-0 flex items-center justify-center">
            <AlertTriangle className="w-12 h-12 text-white opacity-80" />
          </div>
          <button
            onClick={onClose}
            className="absolute top-3 right-3 p-1.5 bg-black/20 hover:bg-black/40 text-white rounded-full backdrop-blur-sm transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Trash2 className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Delete Medication</h2>
            <p className="text-slate-600 mb-4">
              Are you sure you want to delete <span className="font-semibold text-slate-900">"{medication.name}"</span>?
              This action cannot be undone.
            </p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-6">
              <p className="text-sm text-red-800">
                <strong>Warning:</strong> Deleting this medication will permanently remove it from the catalog.
                Any patients currently prescribed this medication may be affected.
              </p>
            </div>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Deleting...
              </>
            ) : (
              <>
                <Trash2 size={16} /> Delete Medication
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
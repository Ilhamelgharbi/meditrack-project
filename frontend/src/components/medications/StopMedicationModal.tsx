import React, { useState } from 'react';
import { Button } from '../common/Button';
import { AlertTriangle, X } from 'lucide-react';

interface StopMedicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  medicationName: string;
}

export const StopMedicationModal: React.FC<StopMedicationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  medicationName
}) => {
  const [reason, setReason] = useState('');

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm(reason.trim() || undefined);
    onClose();
    setReason('');
  };

  const handleClose = () => {
    onClose();
    setReason('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle size={20} className="text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">Stop Medication</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={handleClose}>
            <X size={20} />
          </Button>
        </div>

        <div className="p-6">
          <p className="text-slate-700 mb-4">
            Are you sure you want to stop <strong>{medicationName}</strong>? This action cannot be undone.
          </p>

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Reason (Optional)
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g., Patient completed course, adverse reaction, etc."
              rows={3}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-3">
            <Button
              onClick={handleConfirm}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white"
            >
              Stop Medication
            </Button>
            <Button variant="outline" onClick={handleClose} className="flex-1">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
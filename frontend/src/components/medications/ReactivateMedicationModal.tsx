import React from 'react';
import { Button } from '../common/Button';
import { RotateCcw, X } from 'lucide-react';

interface ReactivateMedicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  medicationName: string;
}

export const ReactivateMedicationModal: React.FC<ReactivateMedicationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  medicationName
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <RotateCcw size={20} className="text-blue-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">Reactivate Medication</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X size={20} />
          </Button>
        </div>

        <div className="p-6">
          <p className="text-slate-700 mb-6">
            Are you sure you want to reactivate <strong>{medicationName}</strong>? 
            The medication will be set to pending status and the patient will need to confirm again.
          </p>

          <div className="flex gap-3">
            <Button
              onClick={handleConfirm}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Reactivate Medication
            </Button>
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
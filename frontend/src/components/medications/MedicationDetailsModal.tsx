import React from 'react';
import { Button } from '../common/Button';
import { X, Pill, Calendar, Clock, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import type { PatientMedicationDetailed } from '../../types/medications.types';

interface MedicationDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  medication: PatientMedicationDetailed | null;
}

export const MedicationDetailsModal: React.FC<MedicationDetailsModalProps> = ({
  isOpen,
  onClose,
  medication
}) => {
  if (!isOpen || !medication) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'stopped':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle size={16} className="text-green-600" />;
      case 'stopped':
        return <X size={16} className="text-red-600" />;
      case 'pending':
        return <Clock size={16} className="text-yellow-600" />;
      default:
        return <Info size={16} className="text-slate-600" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <Pill size={24} className="text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">{medication.medication?.name}</h2>
              <p className="text-slate-600 capitalize">{medication.medication?.form} • {medication.medication?.default_dosage}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="hover:bg-slate-100">
            <X size={20} />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Status Badge */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon(medication.status)}
              <span className={`px-3 py-1 text-sm font-semibold rounded-full border ${getStatusColor(medication.status)}`}>
                {medication.status.toUpperCase()}
              </span>
            </div>
            <div className="text-sm text-slate-500">
              {medication.confirmed_by_patient ? (
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle size={14} />
                  Confirmed by patient
                </span>
              ) : (
                <span className="flex items-center gap-1 text-yellow-600">
                  <Clock size={14} />
                  Awaiting confirmation
                </span>
              )}
            </div>
          </div>

          {/* Medication Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Prescription Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Pill size={18} className="text-blue-600" />
                Prescription Details
              </h3>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm font-medium text-slate-600">Dosage</span>
                  <span className="font-semibold text-slate-900">{medication.dosage}</span>
                </div>

                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm font-medium text-slate-600">Frequency</span>
                  <span className="font-semibold text-slate-900">{medication.times_per_day} times per day</span>
                </div>

                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm font-medium text-slate-600">Start Date</span>
                  <span className="font-semibold text-slate-900">{new Date(medication.start_date).toLocaleDateString()}</span>
                </div>

                {medication.end_date && (
                  <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="text-sm font-medium text-slate-600">End Date</span>
                    <span className="font-semibold text-slate-900">{new Date(medication.end_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Instructions & Notes */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Info size={18} className="text-blue-600" />
                Instructions & Notes
              </h3>

              <div className="space-y-3">
                {medication.instructions ? (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">Special Instructions</h4>
                    <p className="text-blue-800 text-sm">{medication.instructions}</p>
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                    <p className="text-slate-600 text-sm">No special instructions</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Medication Information */}
          {medication.medication && (
            <div className="border-t border-slate-200 pt-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <AlertTriangle size={18} className="text-amber-600" />
                Medication Information
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {medication.medication.side_effects && (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <h4 className="font-medium text-amber-900 mb-2 flex items-center gap-2">
                      <AlertTriangle size={16} />
                      Side Effects
                    </h4>
                    <p className="text-amber-800 text-sm">{medication.medication.side_effects}</p>
                  </div>
                )}

                {medication.medication.warnings && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="font-medium text-red-900 mb-2 flex items-center gap-2">
                      <AlertTriangle size={16} />
                      Warnings
                    </h4>
                    <p className="text-red-800 text-sm">{medication.medication.warnings}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Assignment Information */}
          <div className="border-t border-slate-200 pt-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Calendar size={18} className="text-blue-600" />
              Assignment Information
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Assigned by</p>
                <p className="font-medium text-slate-900">{medication.assigning_doctor?.full_name || 'Unknown'}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Assigned on</p>
                <p className="font-medium text-slate-900">{new Date(medication.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
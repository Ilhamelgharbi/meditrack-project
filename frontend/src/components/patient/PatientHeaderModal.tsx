import React from 'react';
import { PatientAvatar, StatusBadge, AgeDisplay } from '@/components/patient';
import { Mail, Smartphone, X } from 'lucide-react';
import type { PatientProfile } from '../../types/patient.types';

interface PatientHeaderModalProps {
  isOpen: boolean;
  onClose: () => void;
  patient: PatientProfile;
}

const PatientHeaderModal: React.FC<PatientHeaderModalProps> = ({ isOpen, onClose, patient }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-900">Patient Information</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          <div className="flex items-center gap-6">
            <PatientAvatar fullName={patient.user?.full_name} size="lg" />
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-slate-900">{patient.user?.full_name}</h2>
              <div className="flex items-center gap-4 mt-2 text-slate-600">
                <span className="flex items-center gap-1"><Mail size={14} /> {patient.user?.email}</span>
                <span className="flex items-center gap-1"><Smartphone size={14} /> {patient.user?.phone || 'Not provided'}</span>
                <AgeDisplay dateOfBirth={patient.date_of_birth} />
              </div>
              <div className="mt-3">
                <StatusBadge status={patient.status} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientHeaderModal;

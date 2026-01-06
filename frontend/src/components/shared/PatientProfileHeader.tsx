import React from 'react';
import { Button } from '../common/Button';
import {
  Pill, Activity, Edit2, Save,
  CheckCircle,
  FileText, Heart
} from 'lucide-react';
import PatientAvatar from '../patient/PatientAvatar';
import StatusBadge from '../patient/StatusBadge';
import AgeDisplay from '../patient/AgeDisplay';

export interface PatientHeaderData {
  fullName: string;
  email: string;
  phone?: string;
  dateOfBirth?: string;
  weight?: number;
  height?: number;
  bloodType?: string;
  adherence?: number;
  status?: string;
  role: 'patient' | 'admin';
}

interface PatientProfileHeaderProps {
  patient: PatientHeaderData;
  isEditing?: boolean;
  saving?: boolean;
  canEdit?: boolean;
  isPatientViewingOwnProfile?: boolean;
  onEditClick?: () => void;
  onSave?: () => void;
  onCancel?: () => void;
  showAdminActions?: boolean;
  onViewReports?: () => void;
  onPrescribe?: () => void;
}

export const PatientProfileHeader: React.FC<PatientProfileHeaderProps> = ({
  patient,
  isEditing = false,
  saving = false,
  canEdit = false,
  isPatientViewingOwnProfile = false,
  onEditClick,
  onSave,
  onCancel,
  showAdminActions = false,
  onViewReports,
  onPrescribe
}) => {
  const getAdherenceColor = (adherence: number) => {
    if (adherence >= 80) return 'text-green-600';
    if (adherence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row items-center md:items-start gap-6">
      <PatientAvatar fullName={patient.fullName} size="lg" />
      <div className="flex-1 text-center md:text-left">
        <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4 mb-2">
          <h1 className="text-3xl font-bold text-slate-900">
            {patient.fullName || 'Unknown Patient'}
          </h1>
          {!isPatientViewingOwnProfile && patient.status && (
            <StatusBadge status={patient.status} />
          )}
        </div>
        <div className="flex flex-wrap justify-center md:justify-start gap-4 text-slate-500 text-sm">
          <AgeDisplay dateOfBirth={patient.dateOfBirth} className="flex items-center gap-1" />
          {patient.weight && patient.height && (
            <span className="flex items-center gap-1">
              <Activity size={14} /> {patient.weight}kg • {patient.height}cm
            </span>
          )}
          {patient.bloodType && (
            <span className="flex items-center gap-1">
              <Heart size={14} /> {patient.bloodType}
            </span>
          )}
          {patient.adherence && (
            <span className={`flex items-center gap-1 ${getAdherenceColor(patient.adherence)}`}>
              <CheckCircle size={14} /> {Math.round(patient.adherence)}% Adherence
            </span>
          )}
        </div>
      </div>
      <div className="flex gap-3">
        {canEdit && (
          <>
            {isEditing ? (
              <Button
                variant="primary"
                leftIcon={<Save size={18} />}
                onClick={onSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            ) : (
              <Button
                variant="secondary"
                leftIcon={<Edit2 size={18} />}
                onClick={onEditClick}
              >
                Edit Profile
              </Button>
            )}
            {isEditing && onCancel && (
              <Button
                variant="outline"
                onClick={onCancel}
                disabled={saving}
              >
                Cancel
              </Button>
            )}
          </>
        )}
        {showAdminActions && patient.role === 'admin' && (
          <>
            <Button variant="secondary" leftIcon={<FileText size={18} />} onClick={onViewReports}>
              Reports
            </Button>
            <Button leftIcon={<Pill size={18} />} onClick={onPrescribe}>
              Prescribe
            </Button>
          </>
        )}
        {isPatientViewingOwnProfile && !isEditing && onViewReports && (
          <Button leftIcon={<FileText size={18} />} onClick={onViewReports}>
            View Reports
          </Button>
        )}
      </div>
    </div>
  );
};
import React from 'react';
import { Edit2, Mail, ShieldCheck, Calendar, Smartphone, Activity, Heart, CheckCircle } from 'lucide-react';
import { Button } from '../common/Button';
import PatientAvatar from '../patient/PatientAvatar';
import StatusBadge from '../patient/StatusBadge';
import AgeDisplay from '../patient/AgeDisplay';

export interface UserHeaderData {
  fullName: string;
  email: string;
  role: string;
  avatar?: string;
  phone?: string;
  specialty?: string;
  hospital?: string;
  dateOfBirth?: string;
  status?: string;
  // Patient-specific fields
  weight?: number;
  height?: number;
  bloodType?: string;
  adherence?: number;
}

interface UserHeaderProps {
  user: UserHeaderData;
  variant?: 'patient' | 'admin';
  onEditClick?: () => void;
  showEditButton?: boolean;
  subtitle?: string;
  className?: string;
}

export const UserHeader: React.FC<UserHeaderProps> = ({
  user,
  variant = 'patient',
  onEditClick,
  showEditButton = true,
  subtitle,
  className = ''
}) => {
  if (variant === 'admin') {
    return (
      <div className={`bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row items-center md:items-start gap-6 ${className}`}>
        <div className="w-24 h-24 rounded-full bg-blue-600 text-white flex items-center justify-center text-3xl font-bold shadow-md border-4 border-white ring-1 ring-slate-100">
          {user.avatar || user.fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)}
        </div>
        <div className="flex-1 text-center md:text-left">
          <h1 className="text-3xl font-bold text-slate-900">{user.fullName}</h1>
          {(user.specialty || user.hospital) && (
            <p className="text-blue-600 font-medium">
              {user.specialty} {user.specialty && user.hospital && '•'} {user.hospital}
            </p>
          )}
          <div className="flex flex-wrap justify-center md:justify-start gap-4 text-slate-500 text-sm mt-3">
            <span className="flex items-center gap-1"><Mail size={14} /> {user.email}</span>
            <span className="flex items-center gap-1"><ShieldCheck size={14} /> {user.role} Privileges</span>
            {subtitle && <span className="flex items-center gap-1"><Calendar size={14} /> {subtitle}</span>}
          </div>
        </div>
        {showEditButton && onEditClick && (
          <Button onClick={onEditClick} variant="secondary" leftIcon={<Edit2 size={16} />}>Edit Profile</Button>
        )}
      </div>
    );
  }

  // Patient variant (default)
  return (
    <div className={`relative mb-20 ${className}`}>
      <div className="h-40 bg-gradient-to-r from-[#2A7EF0] to-blue-400 rounded-2xl shadow-sm"></div>
      <div className="absolute -bottom-12 left-8 flex items-end gap-6">
        <div className="relative">
          <PatientAvatar fullName={user.fullName} size="lg" className="border-4 border-white shadow-lg" />
          {showEditButton && onEditClick && (
            <button className="absolute bottom-0 right-0 p-2 bg-slate-100 rounded-full border border-white shadow-sm hover:bg-blue-50 text-slate-600 hover:text-blue-600 transition-colors">
              <Edit2 size={16} />
            </button>
          )}
        </div>
        <div className="mb-3">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mb-2">
            <h1 className="text-3xl font-bold text-slate-900">{user.fullName}</h1>
            {user.status && <StatusBadge status={user.status} />}
          </div>
          <div className="flex flex-wrap gap-4 text-slate-600 text-sm">
            <span className="flex items-center gap-1"><Mail size={14} /> {user.email}</span>
            {user.phone && <span className="flex items-center gap-1"><Smartphone size={14} /> {user.phone}</span>}
            {user.dateOfBirth && <AgeDisplay dateOfBirth={user.dateOfBirth} />}
            {user.weight && user.height && (
              <span className="flex items-center gap-1"><Activity size={14} /> {user.weight}kg • {user.height}cm</span>
            )}
            {user.bloodType && (
              <span className="flex items-center gap-1"><Heart size={14} /> {user.bloodType}</span>
            )}
            {user.adherence && (
              <span className={`flex items-center gap-1 ${
                user.adherence >= 80 ? 'text-green-600' :
                user.adherence >= 60 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                <CheckCircle size={14} /> {user.adherence}% Adherence
              </span>
            )}
            {subtitle && <span className="flex items-center gap-1"><Calendar size={14} /> {subtitle}</span>}
          </div>
        </div>
      </div>
      {showEditButton && onEditClick && (
        <div className="absolute top-4 right-4">
          <Button
            variant="secondary"
            className="bg-white/90 backdrop-blur-sm border-none shadow-sm"
            leftIcon={<Edit2 size={16} />}
            onClick={onEditClick}
          >
            Edit Profile
          </Button>
        </div>
      )}
    </div>
  );
};
import React from 'react';
import { Edit2, Mail, ShieldCheck, Calendar } from 'lucide-react';
import { Button } from '../common/Button';

interface AdminProfileHeaderProps {
  user: {
    fullName: string;
    email: string;
    avatar?: string;
  };
  doctorProfile: {
    specialty: string;
    hospital: string;
  };
  onEditClick?: () => void;
}

export const AdminProfileHeader: React.FC<AdminProfileHeaderProps> = ({
  user,
  doctorProfile,
  onEditClick
}) => {
  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row items-center md:items-start gap-6">
      <div className="w-24 h-24 rounded-full bg-blue-600 text-white flex items-center justify-center text-3xl font-bold shadow-md border-4 border-white ring-1 ring-slate-100">
        {user.avatar || user.fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)}
      </div>
      <div className="flex-1 text-center md:text-left">
        <h1 className="text-3xl font-bold text-slate-900">{user.fullName}</h1>
        <p className="text-blue-600 font-medium">{doctorProfile.specialty} • {doctorProfile.hospital}</p>
        <div className="flex flex-wrap justify-center md:justify-start gap-4 text-slate-500 text-sm mt-3">
          <span className="flex items-center gap-1"><Mail size={14} /> {user.email}</span>
          <span className="flex items-center gap-1"><ShieldCheck size={14} /> Admin Privileges</span>
          <span className="flex items-center gap-1"><Calendar size={14} /> Member since 2021</span>
        </div>
      </div>
      {onEditClick && (
        <Button onClick={onEditClick} variant="secondary" leftIcon={<Edit2 size={16}/>}>Edit Profile</Button>
      )}
    </div>
  );
};

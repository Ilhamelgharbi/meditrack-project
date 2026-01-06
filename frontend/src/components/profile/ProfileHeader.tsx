import React from 'react';
import { Edit2, Mail, ShieldCheck, Calendar } from 'lucide-react';
import { Button } from '../common/Button';
import PatientAvatar from '../patient/PatientAvatar';

interface ProfileHeaderProps {
  user: {
    fullName: string;
    email: string;
    role: string;
    avatar?: string;
  };
  onEditClick?: () => void;
  showEditButton?: boolean;
  subtitle?: string;
}

export const ProfileHeader: React.FC<ProfileHeaderProps> = ({
  user,
  onEditClick,
  showEditButton = true,
  subtitle
}) => {
  return (
    <div className="relative mb-20">
      <div className="h-40 bg-gradient-to-r from-[#2A7EF0] to-blue-400 rounded-2xl shadow-sm"></div>
      <div className="absolute -bottom-12 left-8 flex items-end gap-6">
        <div className="relative">
          <PatientAvatar fullName={user.fullName} size="lg" className="border-4 border-white shadow-lg" />
          {showEditButton && (
            <button className="absolute bottom-0 right-0 p-2 bg-slate-100 rounded-full border border-white shadow-sm hover:bg-blue-50 text-slate-600 hover:text-blue-600 transition-colors">
              <Edit2 size={16} />
            </button>
          )}
        </div>
        <div className="mb-3">
          <h1 className="text-3xl font-bold text-slate-900">{user.fullName}</h1>
          <div className="flex items-center gap-4 text-slate-500 text-sm mt-1">
            <span className="flex items-center gap-1"><Mail size={14}/> {user.email}</span>
            <span className="flex items-center gap-1 capitalize"><ShieldCheck size={14}/> {user.role}</span>
            {subtitle && <span className="flex items-center gap-1"><Calendar size={14}/> {subtitle}</span>}
          </div>
        </div>
      </div>
      {showEditButton && onEditClick && (
        <div className="absolute top-4 right-4">
          <Button
            variant="secondary"
            className="bg-white/90 backdrop-blur-sm border-none shadow-sm"
            leftIcon={<Edit2 size={16}/>}
            onClick={onEditClick}
          >
            Edit Profile
          </Button>
        </div>
      )}
    </div>
  );
};

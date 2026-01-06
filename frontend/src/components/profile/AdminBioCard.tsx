import React from 'react';
import { Award, Building } from 'lucide-react';
import { Card } from '../common/Card';

interface AdminBioCardProps {
  bio: string;
  specialty: string;
  hospital: string;
  licenseNumber: string;
}

export const AdminBioCard: React.FC<AdminBioCardProps> = ({
  bio,
  specialty,
  hospital,
  licenseNumber
}) => {
  return (
    <Card title="Professional Information">
      <div className="space-y-4">
        <div>
          <h4 className="font-semibold text-slate-900 mb-2">Bio</h4>
          <p className="text-slate-600 leading-relaxed">{bio}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-200">
          <div className="flex items-center gap-3">
            <Award className="text-blue-600" size={18} />
            <div>
              <p className="text-sm text-slate-500">Specialty</p>
              <p className="font-medium text-slate-900">{specialty}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Building className="text-blue-600" size={18} />
            <div>
              <p className="text-sm text-slate-500">Hospital</p>
              <p className="font-medium text-slate-900">{hospital}</p>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200">
          <div className="flex items-center gap-3">
            <Award className="text-green-600" size={18} />
            <div>
              <p className="text-sm text-slate-500">License Number</p>
              <p className="font-medium text-slate-900">{licenseNumber}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

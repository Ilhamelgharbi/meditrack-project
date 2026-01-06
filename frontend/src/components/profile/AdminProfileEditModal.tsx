import React, { useState } from 'react';
import { X, Save } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';

interface AdminProfileEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: AdminProfileData) => void;
  initialData: AdminProfileData;
}

export interface AdminProfileData {
  fullName: string;
  email: string;
  specialty: string;
  hospital: string;
  licenseNumber: string;
  bio: string;
}

export const AdminProfileEditModal: React.FC<AdminProfileEditModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialData
}) => {
  const [formData, setFormData] = useState<AdminProfileData>(initialData);

  const handleSave = () => {
    onSave(formData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-slate-900">Edit Admin Profile</h2>
          <Button onClick={onClose} variant="ghost" leftIcon={<X size={20} />} />
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              placeholder="Enter full name"
            />
            <Input
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="Enter email"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Specialty"
              value={formData.specialty}
              onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
              placeholder="Enter specialty"
            />
            <Input
              label="Hospital"
              value={formData.hospital}
              onChange={(e) => setFormData({ ...formData, hospital: e.target.value })}
              placeholder="Enter hospital"
            />
          </div>

          <Input
            label="License Number"
            value={formData.licenseNumber}
            onChange={(e) => setFormData({ ...formData, licenseNumber: e.target.value })}
            placeholder="Enter license number"
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Bio</label>
            <textarea
              value={formData.bio}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
              placeholder="Enter bio"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button onClick={onClose} variant="secondary">Cancel</Button>
          <Button onClick={handleSave} leftIcon={<Save size={16} />}>Save Changes</Button>
        </div>
      </div>
    </div>
  );
};

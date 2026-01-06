import React from 'react';
import { X, Save } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';

interface PatientProfile {
  age: string;
  weight: string;
  height: string;
  bloodType: string;
  allergies: string;
  heartConditions: string;
  conditions: string;
  surgeries: string;
  chronicDiseases: string;
  phone?: string;
}

interface PatientProfileEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: PatientProfile;
  onSave: (profile: PatientProfile) => void;
  onProfileChange: (field: keyof PatientProfile, value: string) => void;
}

export const PatientProfileEditModal: React.FC<PatientProfileEditModalProps> = ({
  isOpen,
  onClose,
  profile,
  onSave,
  onProfileChange
}) => {
  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(profile);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-900">Edit Profile</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20}/>
          </button>
        </div>

        <form onSubmit={handleSave}>
          <div className="p-6 overflow-y-auto space-y-6">
            {/* Section: Vitals */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Vitals</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Input
                  label="Age"
                  type="number"
                  value={profile.age}
                  onChange={(e) => onProfileChange('age', e.target.value)}
                />
                <Input
                  label="Weight (kg)"
                  value={profile.weight}
                  onChange={(e) => onProfileChange('weight', e.target.value)}
                />
                <Input
                  label="Height (cm)"
                  value={profile.height}
                  onChange={(e) => onProfileChange('height', e.target.value)}
                />
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Blood Type</label>
                  <select
                    className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-100 text-slate-700 bg-white"
                    value={profile.bloodType}
                    onChange={(e) => onProfileChange('bloodType', e.target.value)}
                  >
                    {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Section: Medical History */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Medical History</h3>
              <div className="space-y-4">
                <Input
                  label="Allergies (comma separated)"
                  value={profile.allergies}
                  onChange={(e) => onProfileChange('allergies', e.target.value)}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Heart Conditions"
                    value={profile.heartConditions}
                    onChange={(e) => onProfileChange('heartConditions', e.target.value)}
                  />
                  <Input
                    label="Asthma / Respiratory"
                    value={profile.conditions}
                    onChange={(e) => onProfileChange('conditions', e.target.value)}
                  />
                  <Input
                    label="Surgeries"
                    value={profile.surgeries}
                    onChange={(e) => onProfileChange('surgeries', e.target.value)}
                  />
                  <Input
                    label="Chronic Diseases"
                    value={profile.chronicDiseases}
                    onChange={(e) => onProfileChange('chronicDiseases', e.target.value)}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" leftIcon={<Save size={18}/>}>Save Changes</Button>
          </div>
        </form>
      </div>
    </div>
  );
};

import React, { useState, useMemo } from 'react';
import { Button } from '../common/Button';
import { X, Save } from 'lucide-react';
import type { PatientMedicationDetailed, PatientMedicationUpdate } from '../../types/medications.types';

interface MedicationEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: PatientMedicationUpdate) => void;
  medication: PatientMedicationDetailed | null;
  saving?: boolean;
}

export const MedicationEditModal: React.FC<MedicationEditModalProps> = ({
  isOpen,
  onClose,
  onSave,
  medication,
  saving = false
}) => {
  const initialFormData = useMemo(() => {
    if (medication) {
      return {
        dosage: medication.dosage,
        instructions: medication.instructions || '',
        times_per_day: medication.times_per_day,
        start_date: medication.start_date.split('T')[0], // Extract date part
        end_date: medication.end_date ? medication.end_date.split('T')[0] : ''
      };
    }
    return {
      dosage: '',
      instructions: '',
      times_per_day: 1,
      start_date: '',
      end_date: ''
    };
  }, [medication]);

  const [formData, setFormData] = useState(initialFormData);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!medication) return;

    const submitData: PatientMedicationUpdate = {
      dosage: formData.dosage,
      instructions: formData.instructions || undefined,
      times_per_day: formData.times_per_day,
      start_date: formData.start_date,
      end_date: formData.end_date || undefined
    };

    onSave(submitData);
  };

  const handleClose = () => {
    onClose();
  };

  if (!isOpen || !medication) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">Edit Medication</h2>
          <Button variant="ghost" size="sm" onClick={handleClose}>
            <X size={20} />
          </Button>
        </div>

        {/* Medication Info */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <div className="w-6 h-6 bg-blue-500 rounded"></div>
            </div>
            <div>
              <h3 className="font-medium text-slate-900">{medication.medication?.name}</h3>
              <p className="text-sm text-slate-500 capitalize">{medication.medication?.form}</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Dosage */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Dosage *
              </label>
              <input
                type="text"
                value={formData.dosage}
                onChange={(e) => setFormData(prev => ({ ...prev, dosage: e.target.value }))}
                placeholder="e.g., 1 tablet, 5ml"
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Frequency */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Times per Day *
              </label>
              <select
                value={formData.times_per_day}
                onChange={(e) => setFormData(prev => ({ ...prev, times_per_day: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={1}>Once daily</option>
                <option value={2}>Twice daily</option>
                <option value={3}>Three times daily</option>
                <option value={4}>Four times daily</option>
              </select>
            </div>
          </div>

          {/* Instructions */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Instructions
            </label>
            <textarea
              value={formData.instructions}
              onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
              rows={3}
              placeholder="e.g., Take with food, avoid alcohol"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Start Date *
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                End Date (Optional)
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="submit" leftIcon={<Save size={18} />} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
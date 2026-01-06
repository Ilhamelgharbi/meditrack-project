import React, { useState, useMemo } from 'react';
import { Plus, Edit, X } from 'lucide-react';
import type { AdminMedicationFormProps, MedicationFormData } from './types';
import { MedicationImage } from './MedicationImage';

export const AdminMedicationForm: React.FC<AdminMedicationFormProps> = ({
  medication,
  onClose,
  onSubmit,
  isLoading = false,
  mode = 'create'
}) => {
  const initialFormData = useMemo(() => {
    if (medication && mode === 'edit') {
      return {
        name: medication.name,
        form: medication.form,
        default_dosage: medication.default_dosage || '',
        side_effects: medication.side_effects || '',
        warnings: medication.warnings || ''
      };
    }
    return {
      name: '',
      form: '',
      default_dosage: '',
      side_effects: '',
      warnings: ''
    };
  }, [medication, mode]);

  const [formData, setFormData] = useState<MedicationFormData>(initialFormData);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      form: '',
      default_dosage: '',
      side_effects: '',
      warnings: ''
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className={`h-32 relative bg-gradient-to-r ${mode === 'create' ? 'from-emerald-600 to-emerald-700' : 'from-blue-600 to-blue-700'} flex-shrink-0`}>
          <div className="absolute inset-0 flex items-center justify-center">
            {mode === 'create' ? (
              <Plus className="w-16 h-16 text-white opacity-80" />
            ) : (
              <MedicationImage
                src={undefined}
                alt={medication?.name || 'Edit Medication'}
                size="lg"
                className="opacity-80"
              />
            )}
          </div>
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 p-2 bg-black/20 hover:bg-black/40 text-white rounded-full backdrop-blur-sm transition-colors"
          >
            <X size={20} />
          </button>
          <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/60 to-transparent p-6">
            <h2 className="text-2xl font-bold text-white">
              {mode === 'create' ? 'Add New Medication' : 'Edit Medication'}
            </h2>
            <p className={mode === 'create' ? 'text-emerald-100' : 'text-blue-100'}>
              {mode === 'create' ? 'Create a new medication entry' : medication?.name}
            </p>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Medication Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    required
                    placeholder="Enter medication name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Form</label>
                  <select
                    value={formData.form}
                    onChange={(e) => setFormData({ ...formData, form: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    required
                  >
                    <option value="">Select form</option>
                    <option value="tablet">Tablet</option>
                    <option value="capsule">Capsule</option>
                    <option value="liquid">Liquid</option>
                    <option value="injection">Injection</option>
                    <option value="cream">Cream</option>
                    <option value="ointment">Ointment</option>
                    <option value="patch">Patch</option>
                    <option value="inhaler">Inhaler</option>
                    <option value="drops">Drops</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Default Dosage</label>
                  <input
                    type="text"
                    value={formData.default_dosage}
                    onChange={(e) => setFormData({ ...formData, default_dosage: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="e.g., 500mg, 10ml, etc."
                  />
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Side Effects</label>
                  <textarea
                    value={formData.side_effects}
                    onChange={(e) => setFormData({ ...formData, side_effects: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
                    rows={4}
                    placeholder="List any common side effects..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Warnings</label>
                  <textarea
                    value={formData.warnings}
                    onChange={(e) => setFormData({ ...formData, warnings: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
                    rows={4}
                    placeholder="Important warnings or contraindications..."
                  />
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* Modal Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex gap-3 justify-end">
          <button
            onClick={handleClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className={`px-4 py-2 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2 ${
              mode === 'create'
                ? 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400'
                : 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400'
            }`}
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                {mode === 'create' ? 'Creating...' : 'Updating...'}
              </>
            ) : (
              <>
                {mode === 'create' ? <Plus size={16} /> : <Edit size={16} />}
                {mode === 'create' ? 'Create Medication' : 'Update Medication'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
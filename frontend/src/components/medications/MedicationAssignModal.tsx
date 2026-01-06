import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../common/Button';
import { X, Save, Search, Pill, RotateCcw } from 'lucide-react';
import { medicationService } from '../../services/medications.service';
import type { Medication, PatientMedicationCreate, PatientMedication } from '../../types/medications.types';

interface MedicationAssignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: PatientMedicationCreate) => void;
  saving?: boolean;
  existingMedications?: PatientMedication[];
}

interface MedicationOption {
  id: number;
  name: string;
  form: string;
  default_dosage?: string;
}

export const MedicationAssignModal: React.FC<MedicationAssignModalProps> = ({
  isOpen,
  onClose,
  onSave,
  saving = false,
  existingMedications = []
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [medications, setMedications] = useState<MedicationOption[]>([]);
  const [selectedMedication, setSelectedMedication] = useState<Medication | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [existingMedication, setExistingMedication] = useState<PatientMedication | null>(null);
  const [formData, setFormData] = useState({
    dosage: '',
    instructions: '',
    times_per_day: 1,
    start_date: new Date().toISOString().split('T')[0],
    end_date: ''
  });

  const searchRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Search medications when search term changes
  useEffect(() => {
    const searchMedications = async () => {
      if (searchTerm.length < 2) {
        setMedications([]);
        setShowDropdown(false);
        return;
      }

      try {
        setLoading(true);
        const results = await medicationService.getAllMedications(searchTerm, 10);
        setMedications(results.map(med => ({
          id: med.id,
          name: med.name,
          form: med.form,
          default_dosage: med.default_dosage
        })));
        setShowDropdown(true);
      } catch (err) {
        console.error('Error searching medications:', err);
        setMedications([]);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(searchMedications, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMedicationSelect = (medication: MedicationOption) => {
    // Get full medication details
    medicationService.getMedicationById(medication.id)
      .then(fullMed => {
        setSelectedMedication(fullMed);
        setSearchTerm(fullMed.name);
        
        // Check if patient already has this medication
        // Prioritize stopped medications for reactivation
        const stoppedMed = existingMedications.find(
          med => med.medication_id === fullMed.id && med.status === 'stopped'
        );
        const activeMed = existingMedications.find(
          med => med.medication_id === fullMed.id && med.status !== 'stopped'
        );
        
        // Use stopped medication if available (for reactivation), otherwise use active one
        const existing = stoppedMed || activeMed;
        setExistingMedication(existing || null);
        
        // Pre-fill form with existing data if reactivating
        if (existing && existing.status === 'stopped') {
          setFormData(prev => ({
            ...prev,
            dosage: existing.dosage,
            instructions: existing.instructions || '',
            times_per_day: existing.times_per_day,
            start_date: existing.start_date
          }));
        } else {
          setFormData(prev => ({
            ...prev,
            dosage: fullMed.default_dosage || ''
          }));
        }
        
        setShowDropdown(false);
      })
      .catch(err => {
        console.error('Error fetching medication details:', err);
      });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMedication) return;

    const submitData: PatientMedicationCreate = {
      medication_id: selectedMedication.id,
      dosage: formData.dosage,
      instructions: formData.instructions,
      times_per_day: formData.times_per_day,
      start_date: formData.start_date,
      end_date: formData.end_date || undefined
    };

    onSave(submitData);
  };

  const resetForm = () => {
    setSearchTerm('');
    setSelectedMedication(null);
    setExistingMedication(null);
    setMedications([]);
    setShowDropdown(false);
    setFormData({
      dosage: '',
      instructions: '',
      times_per_day: 1,
      start_date: new Date().toISOString().split('T')[0],
      end_date: ''
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">Assign Medication</h2>
          <Button variant="ghost" size="sm" onClick={handleClose}>
            <X size={20} />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Medication Search */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Medication Name *
            </label>
            <div className="relative">
              <div className="relative">
                <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                <input
                  ref={searchRef}
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onFocus={() => searchTerm.length >= 2 && setShowDropdown(true)}
                  placeholder="Search for medication..."
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                {loading && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  </div>
                )}
              </div>

              {/* Dropdown */}
              {showDropdown && medications.length > 0 && (
                <div
                  ref={dropdownRef}
                  className="absolute z-10 w-full mt-1 bg-white border border-slate-300 rounded-md shadow-lg max-h-60 overflow-y-auto"
                >
                  {medications.map((medication) => (
                    <button
                      key={medication.id}
                      type="button"
                      onClick={() => handleMedicationSelect(medication)}
                      className="w-full px-4 py-3 text-left hover:bg-slate-50 border-b border-slate-100 last:border-b-0 flex items-center gap-3"
                    >
                      <Pill size={16} className="text-blue-500 flex-shrink-0" />
                      <div>
                        <div className="font-medium text-slate-900">{medication.name}</div>
                        <div className="text-sm text-slate-500 capitalize">
                          {medication.form}
                          {medication.default_dosage && ` • ${medication.default_dosage}`}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {showDropdown && searchTerm.length >= 2 && medications.length === 0 && !loading && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-slate-300 rounded-md shadow-lg p-4 text-center text-slate-500">
                  No medications found
                </div>
              )}
            </div>

            {selectedMedication && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex items-center gap-2">
                  <Pill size={16} className="text-blue-600" />
                  <span className="font-medium text-blue-900">{selectedMedication.name}</span>
                  <span className="text-sm text-blue-700 capitalize">({selectedMedication.form})</span>
                </div>
                {existingMedication && (
                  <div className="mt-2 text-sm">
                    {existingMedication.status === 'stopped' ? (
                      <span className="text-orange-700 bg-orange-100 px-2 py-1 rounded">
                        <RotateCcw size={14} className="inline mr-1" />
                        Previously stopped - will reactivate
                      </span>
                    ) : existingMedication.status === 'active' ? (
                      <span className="text-red-700 bg-red-100 px-2 py-1 rounded">
                        Already active - cannot assign again
                      </span>
                    ) : existingMedication.status === 'pending' ? (
                      <span className="text-yellow-700 bg-yellow-100 px-2 py-1 rounded">
                        Already pending - cannot assign again
                      </span>
                    ) : null}
                  </div>
                )}
                {selectedMedication.side_effects && (
                  <p className="text-sm text-blue-700 mt-1">
                    <strong>Side effects:</strong> {selectedMedication.side_effects}
                  </p>
                )}
                {selectedMedication.warnings && (
                  <p className="text-sm text-red-700 mt-1">
                    <strong>Warnings:</strong> {selectedMedication.warnings}
                  </p>
                )}
              </div>
            )}
          </div>

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
            <Button 
              type="submit" 
              leftIcon={existingMedication?.status === 'stopped' ? <RotateCcw size={18} /> : <Save size={18} />} 
              disabled={saving || !selectedMedication || Boolean(existingMedication && existingMedication.status !== 'stopped')}
            >
              {saving ? 'Processing...' : 
               existingMedication?.status === 'stopped' ? 'Reactivate Medication' :
               'Assign Medication'}
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
import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '../common/Button';
import { SimpleMedicationList, type SimpleMedicationData } from './SimpleMedicationList';
import { StopMedicationModal } from './StopMedicationModal';
import { MedicationAssignModal } from './MedicationAssignModal';
import { MedicationEditModal } from './MedicationEditModal';
import { MedicationDetailsModal } from './MedicationDetailsModal';
import { ReactivateMedicationModal } from './ReactivateMedicationModal';
import { Plus, Activity, Loader2 } from 'lucide-react';
import { medicationService } from '../../services/medications.service';
import type { PatientMedicationDetailed, PatientMedicationCreate, PatientMedicationUpdate } from '../../types/medications.types';

interface PatientMedicationManagementProps {
  patientId: number;
  isAdmin?: boolean;
}

export const PatientMedicationManagement: React.FC<PatientMedicationManagementProps> = ({
  patientId,
  isAdmin = false
}) => {
  const [medications, setMedications] = useState<PatientMedicationDetailed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isStopModalOpen, setIsStopModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isReactivateModalOpen, setIsReactivateModalOpen] = useState(false);
  const [selectedMedication, setSelectedMedication] = useState<PatientMedicationDetailed | null>(null);
  const [selectedMedicationForDetails, setSelectedMedicationForDetails] = useState<PatientMedicationDetailed | null>(null);
  const [selectedMedicationForReactivate, setSelectedMedicationForReactivate] = useState<PatientMedicationDetailed | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchPatientMedications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await medicationService.getPatientMedications(patientId, { include_inactive: true });
      setMedications(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch medications');
      console.error('Error fetching medications:', err);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  // Fetch patient medications on mount
  useEffect(() => {
    fetchPatientMedications();
  }, [fetchPatientMedications]);

  const handleAssignMedication = async (medicationData: PatientMedicationCreate) => {
    try {
      setSaving(true);
      const newMedication = await medicationService.assignMedicationToPatient(patientId, medicationData);
      // Add the new medication to the local state
      setMedications(prev => [newMedication, ...prev]);
      setIsAssignModalOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign medication');
      console.error('Error assigning medication:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleEditMedication = async (updateData: PatientMedicationUpdate) => {
    if (!selectedMedication) return;

    try {
      setSaving(true);
      const updatedMedication = await medicationService.updatePatientMedication(patientId, selectedMedication.id, updateData);
      // Update the medication in the local state
      setMedications(prev => prev.map(med =>
        med.id === selectedMedication.id ? updatedMedication : med
      ));
      setIsEditModalOpen(false);
      setSelectedMedication(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update medication');
      console.error('Error updating medication:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleStopMedication = async (reason?: string) => {
    if (!selectedMedication) return;

    try {
      setSaving(true);
      const stoppedMedication = await medicationService.stopMedication(patientId, selectedMedication.id, reason);
      // Update the medication in the local state
      setMedications(prev => prev.map(med =>
        med.id === selectedMedication.id ? stoppedMedication : med
      ));
      setIsStopModalOpen(false);
      setSelectedMedication(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop medication');
      console.error('Error stopping medication:', err);
    } finally {
      setSaving(false);
    }
  };

  const openEditModal = (medication: PatientMedicationDetailed) => {
    setSelectedMedication(medication);
    setIsEditModalOpen(true);
  };

  const openStopModal = (medication: PatientMedicationDetailed) => {
    setSelectedMedication(medication);
    setIsStopModalOpen(true);
  };

  const openDetailsModal = (simpleMed: SimpleMedicationData) => {
    const fullMed = medications.find(m => m.id.toString() === simpleMed.id);
    if (fullMed) {
      setSelectedMedicationForDetails(fullMed);
      setIsDetailsModalOpen(true);
    }
  };

  const handleReactivateMedication = async (simpleMed: SimpleMedicationData) => {
    const fullMed = medications.find(m => m.id.toString() === simpleMed.id);
    if (!fullMed) return;

    setSelectedMedicationForReactivate(fullMed);
    setIsReactivateModalOpen(true);
  };

  const handleConfirmReactivate = async () => {
    if (!selectedMedicationForReactivate) return;

    try {
      setSaving(true);
      // Use the assign medication endpoint which will handle reactivation
      const updatedMedication = await medicationService.assignMedicationToPatient(patientId, {
        medication_id: selectedMedicationForReactivate.medication_id,
        dosage: selectedMedicationForReactivate.dosage,
        instructions: selectedMedicationForReactivate.instructions,
        times_per_day: selectedMedicationForReactivate.times_per_day,
        start_date: selectedMedicationForReactivate.start_date
      });

      // Update the medication in the local state
      setMedications(prev => prev.map(med =>
        med.id === selectedMedicationForReactivate.id ? updatedMedication : med
      ));

      setIsReactivateModalOpen(false);
      setSelectedMedicationForReactivate(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reactivate medication';
      setError(errorMessage);
      console.error('Error reactivating medication:', err);
    } finally {
      setSaving(false);
    }
  };

  // Convert to SimpleMedicationData for the list component
  const simpleMedications: SimpleMedicationData[] = medications.map(med => ({
    id: med.id.toString(),
    name: med.medication?.name || 'Unknown Medication',
    status: med.status === 'stopped' ? 'inactive' : med.status,
    dosage: med.dosage,
    timesPerDay: med.times_per_day,
    startDate: med.start_date,
    instructions: med.instructions
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 size={24} className="animate-spin text-blue-500" />
        <span className="ml-2 text-slate-600">Loading medications...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-2"
          onClick={fetchPatientMedications}
        >
          Retry
        </Button>
      </div>
    );
  }

  const activeMedications = simpleMedications.filter(med => med.status === 'active');
  const pendingMedications = simpleMedications.filter(med => med.status === 'pending');
  const inactiveMedications = simpleMedications.filter(med => med.status === 'inactive');

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Activity size={20} className="text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Medication Management</h2>
            <p className="text-sm text-slate-500">
              {activeMedications.length + pendingMedications.length + inactiveMedications.length} medication{(activeMedications.length + pendingMedications.length + inactiveMedications.length) !== 1 ? 's' : ''} ({activeMedications.length} active, {pendingMedications.length} pending, {inactiveMedications.length} stopped)
            </p>
          </div>
        </div>
        {isAdmin && (
          <Button
            leftIcon={<Plus size={18} />}
            onClick={() => setIsAssignModalOpen(true)}
            disabled={saving}
          >
            Assign Medication
          </Button>
        )}
      </div>

      {/* Active Medications */}
      <SimpleMedicationList
        medications={activeMedications}
        onAddMedication={isAdmin ? () => setIsAssignModalOpen(true) : undefined}
        onViewDetails={openDetailsModal}
        onEditMedication={isAdmin ? (med) => {
          const fullMed = medications.find(m => m.id.toString() === med.id);
          if (fullMed) openEditModal(fullMed);
        } : undefined}
        onStopMedication={isAdmin ? (med) => {
          const fullMed = medications.find(m => m.id.toString() === med.id);
          if (fullMed) openStopModal(fullMed);
        } : undefined}
        showActions={isAdmin}
        title="Active Medications"
      />

      {/* Pending Medications */}
      {pendingMedications.length > 0 && (
        <SimpleMedicationList
          medications={pendingMedications}
          onViewDetails={openDetailsModal}
          onEditMedication={isAdmin ? (med) => {
            const fullMed = medications.find(m => m.id.toString() === med.id);
            if (fullMed) openEditModal(fullMed);
          } : undefined}
          onStopMedication={isAdmin ? (med) => {
            const fullMed = medications.find(m => m.id.toString() === med.id);
            if (fullMed) openStopModal(fullMed);
          } : undefined}
          showActions={isAdmin}
          title="Pending Medications"
        />
      )}

      {/* Inactive Medications */}
      {inactiveMedications.length > 0 && (
        <SimpleMedicationList
          medications={inactiveMedications}
          onViewDetails={openDetailsModal}
          onReactivateMedication={handleReactivateMedication}
          showActions={isAdmin}
          title="Inactive Medications"
        />
      )}

      {/* Modals */}
      <MedicationAssignModal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        onSave={handleAssignMedication}
        saving={saving}
        existingMedications={medications}
      />

      <MedicationEditModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedMedication(null);
        }}
        onSave={handleEditMedication}
        medication={selectedMedication}
        saving={saving}
      />

      <StopMedicationModal
        isOpen={isStopModalOpen}
        onClose={() => {
          setIsStopModalOpen(false);
          setSelectedMedication(null);
        }}
        onConfirm={(reason) => handleStopMedication(reason)}
        medicationName={selectedMedication?.medication?.name || ''}
      />

      <MedicationDetailsModal
        isOpen={isDetailsModalOpen}
        onClose={() => {
          setIsDetailsModalOpen(false);
          setSelectedMedicationForDetails(null);
        }}
        medication={selectedMedicationForDetails}
      />

      <ReactivateMedicationModal
        isOpen={isReactivateModalOpen}
        onClose={() => {
          setIsReactivateModalOpen(false);
          setSelectedMedicationForReactivate(null);
        }}
        onConfirm={handleConfirmReactivate}
        medicationName={selectedMedicationForReactivate?.medication?.name || ''}
      />
    </div>
  );
};
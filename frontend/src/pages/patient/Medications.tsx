import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card } from '../../components/common/Card';
import { AlertTriangle } from 'lucide-react';
import { medicationService } from '../../services/medications.service';
import type { PatientMedicationDetailed } from '../../types/medications.types';
import {
  PatientMedicationList,
  MedicationDetails
} from '../../components/medications';

const MedicationsPage = () => {
  const { user } = useAuth();
  const [medications, setMedications] = useState<PatientMedicationDetailed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMed, setSelectedMed] = useState<PatientMedicationDetailed | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  const fetchMedications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const patientId = user!.id;
      const data = await medicationService.getPatientMedications(patientId, {
        limit: 100,
        include_inactive: true
      });

      setMedications(data);
    } catch (err: unknown) {
      console.error('Error fetching medications:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load medications';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Fetch medications on mount
  useEffect(() => {
    if (user) {
      fetchMedications();
    }
  }, [user, fetchMedications]);

  const handleActivateMedication = async (medication: PatientMedicationDetailed) => {
    try {
      if (!user) return;

      // Optimistically update the medication status
      setMedications(prev => prev.map(med =>
        med.id === medication.id
          ? { ...med, status: 'active' as const, confirmed_by_patient: true }
          : med
      ));

      // Then make the API call
      await medicationService.confirmMedication(user.id, medication.id);
    } catch (error) {
      console.error('Error activating medication:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to activate medication. Please try again.';
      setError(errorMessage);

      // Revert the optimistic update on error
      setMedications(prev => prev.map(med =>
        med.id === medication.id
          ? { ...med, status: 'pending' as const, confirmed_by_patient: false }
          : med
      ));
    }
  };

  return (
    <div className="space-y-6 relative p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Medications</h1>
        <p className="text-slate-500">Track and manage your prescribed medications</p>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <div className="flex items-center gap-3 text-red-700">
            <AlertTriangle size={20} />
            <p>{error}</p>
          </div>
        </Card>
      )}

      {/* Medications List with Search/Filter */}
      <PatientMedicationList
        medications={medications}
        onView={(med) => {
          setSelectedMed(med);
          setIsDetailsOpen(true);
        }}
        onActivate={handleActivateMedication}
        loading={loading}
        showActions={true}
        compact={false}
      />

      {/* Details Modal */}
      {isDetailsOpen && selectedMed && (
        <MedicationDetails
          medication={selectedMed}
          onClose={() => setIsDetailsOpen(false)}
          showActions={false}
        />
      )}
    </div>
  );
};

export default MedicationsPage;
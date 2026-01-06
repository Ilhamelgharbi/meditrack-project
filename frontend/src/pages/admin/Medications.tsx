import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Pill, FlaskConical, Syringe, Package } from 'lucide-react';
import { StatCard } from '../../components/common/StatCard';
import type { MedicationCreate, MedicationFormType } from '../../types/medications.types';
import type { MedicationFormData } from '../../components/medications/types';
import type { Medication } from '../../types/medications.types';
import { medicationService } from '../../services/medications.service';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import {
  AdminMedicationList,
  AdminMedicationDetails,
  AdminMedicationForm,
  AdminMedicationDelete
} from '../../components/medications';

const Medications: React.FC = () => {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedMedication, setSelectedMedication] = useState<Medication | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadMedications = useCallback(async () => {
    try {
      setLoading(true);
      const data = await medicationService.getAllMedications(searchTerm);
      setMedications(data);
    } catch (err) {
      setError('Failed to load medications');
      console.error('Error loading medications:', err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  useEffect(() => {
    loadMedications();
  }, [loadMedications]);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      loadMedications();
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, loadMedications]);

  const handleCreate = async (formData: MedicationFormData) => {
    try {
      setIsSubmitting(true);
      const medicationData: MedicationCreate = {
        name: formData.name,
        form: formData.form as MedicationFormType,
        default_dosage: formData.default_dosage || undefined,
        side_effects: formData.side_effects || undefined,
        warnings: formData.warnings || undefined
      };
      await medicationService.createMedication(medicationData);
      setShowCreateModal(false);
      loadMedications();
    } catch (err) {
      console.error('Error creating medication:', err);
      setError('Failed to create medication');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (formData: MedicationFormData) => {
    if (!selectedMedication) return;

    try {
      setIsSubmitting(true);
      const medicationData: Partial<MedicationCreate> = {
        name: formData.name,
        form: formData.form as MedicationFormType,
        default_dosage: formData.default_dosage || undefined,
        side_effects: formData.side_effects || undefined,
        warnings: formData.warnings || undefined
      };
      await medicationService.updateMedication(selectedMedication.id, medicationData);
      setShowEditModal(false);
      setSelectedMedication(null);
      loadMedications();
    } catch (err) {
      console.error('Error updating medication:', err);
      setError('Failed to update medication');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedMedication) return;

    try {
      setIsSubmitting(true);
      await medicationService.deleteMedication(selectedMedication.id);
      setShowDeleteModal(false);
      setSelectedMedication(null);
      loadMedications();
    } catch (err) {
      console.error('Error deleting medication:', err);
      setError('Failed to delete medication');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditModal = (medication: Medication) => {
    setSelectedMedication(medication);
    setShowEditModal(true);
  };

  const openDeleteModal = (medication: Medication) => {
    setSelectedMedication(medication);
    setShowDeleteModal(true);
  };

  const openDetailsModal = (medication: Medication) => {
    setSelectedMedication(medication);
    setShowDetailsModal(true);
  };

  const closeAllModals = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setShowDeleteModal(false);
    setShowDetailsModal(false);
    setSelectedMedication(null);
  };

  const handleRetry = () => {
    loadMedications();
  };

  if (loading) {
    return <DashboardLoadingModal />;
  }

  if (error) {
    return <DashboardErrorModal error={error} onRetry={handleRetry} />;
  }

  // Calculate stats by form type
  const tabletCount = medications.filter(m => m.form === 'tablet').length;
  const capsuleCount = medications.filter(m => m.form === 'capsule').length;
  const syrupCount = medications.filter(m => m.form === 'syrup').length;
  const otherCount = medications.filter(m => !['tablet', 'capsule', 'syrup'].includes(m.form)).length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Medication Catalog</h1>
          <p className="text-slate-500 mt-1">Manage the medication catalog for all patients</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Medication
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Medications"
          value={medications.length}
          icon={Pill}
          color="bg-teal-500"
          subtitle="In catalog"
        />
        <StatCard
          title="Tablets"
          value={tabletCount}
          icon={Package}
          color="bg-blue-500"
          subtitle="Tablet form"
        />
        <StatCard
          title="Capsules"
          value={capsuleCount}
          icon={FlaskConical}
          color="bg-purple-500"
          subtitle="Capsule form"
        />
        <StatCard
          title="Syrups & Others"
          value={syrupCount + otherCount}
          icon={Syringe}
          color="bg-orange-500"
          subtitle="Liquid & other forms"
        />
      </div>

      {/* Medications List with Search/Filter */}
      <AdminMedicationList
        medications={medications}
        onView={openDetailsModal}
        onEdit={openEditModal}
        onDelete={openDeleteModal}
        loading={loading}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />

      {/* Modals */}
      {showCreateModal && (
        <AdminMedicationForm
          onClose={closeAllModals}
          onSubmit={handleCreate}
          isLoading={isSubmitting}
          mode="create"
        />
      )}

      {showEditModal && selectedMedication && (
        <AdminMedicationForm
          medication={selectedMedication}
          onClose={closeAllModals}
          onSubmit={handleEdit}
          isLoading={isSubmitting}
          mode="edit"
        />
      )}

      {showDeleteModal && selectedMedication && (
        <AdminMedicationDelete
          medication={selectedMedication}
          onClose={closeAllModals}
          onConfirm={handleDelete}
          isLoading={isSubmitting}
        />
      )}

      {showDetailsModal && selectedMedication && (
        <AdminMedicationDetails
          medication={selectedMedication}
          onClose={closeAllModals}
          onEdit={openEditModal}
          onDelete={openDeleteModal}
        />
      )}
    </div>
  );
};

export default Medications;
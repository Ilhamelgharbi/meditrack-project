// src/services/medications.ts
import api from './api';
import type {
  Medication,
  PatientMedicationDetailed,
  PatientMedicationCreate,
  PatientMedicationUpdate,
  MedicationFilters,
  MedicationCreate
} from '../types/medications.types';

export const medicationService = {
  // Get all medications from catalog
  getAllMedications: async (search?: string, limit = 100): Promise<Medication[]> => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit.toString());

    const response = await api.get<Medication[]>(`/medications/?${params}`);
    return response.data;
  },

  // Get medication by ID
  getMedicationById: async (id: number): Promise<Medication> => {
    const response = await api.get<Medication>(`/medications/${id}/`);
    return response.data;
  },

  // Get current patient's medications
  getMyMedications: async (
    filters?: MedicationFilters
  ): Promise<PatientMedicationDetailed[]> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status_filter', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.include_inactive) params.append('include_inactive', filters.include_inactive.toString());

    // Get current user ID - try localStorage first, then API if needed
    let user;
    const storedUser = localStorage.getItem('meditrack_user');
    const token = localStorage.getItem('meditrack_token');

    if (!token) {
      throw new Error('User not authenticated');
    }

    if (storedUser) {
      try {
        user = JSON.parse(storedUser);
      } catch {
        localStorage.removeItem('meditrack_user');
      }
    }

    // If we don't have user data, fetch it
    if (!user?.id) {
      try {
        const response = await api.get('/auth/me');
        user = response.data;
        localStorage.setItem('meditrack_user', JSON.stringify(user));
      } catch (error) {
        throw new Error('Failed to authenticate user');
      }
    }

    if (!user?.id) {
      throw new Error('User not authenticated');
    }

    const response = await api.get<PatientMedicationDetailed[]>(`/medications/patients/${user.id}/medications?${params}`);
    return response.data;
  },

  // Get patient medications (for admin use)
  getPatientMedications: async (
    patientId: number,
    filters?: MedicationFilters
  ): Promise<PatientMedicationDetailed[]> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status_filter', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.include_inactive) params.append('include_inactive', filters.include_inactive.toString());

    const response = await api.get<PatientMedicationDetailed[]>(`/medications/patients/${patientId}/medications?${params}`);
    return response.data;
  },

  // Confirm medication (patient action)
  confirmMedication: async (patientId: number, medicationId: number): Promise<PatientMedicationDetailed> => {
    const response = await api.patch<PatientMedicationDetailed>(`/medications/patients/${patientId}/medications/${medicationId}/confirm`);
    return response.data;
  },

  // Assign medication to patient (admin only)
  assignMedicationToPatient: async (
    patientId: number,
    medicationData: PatientMedicationCreate
  ): Promise<PatientMedicationDetailed> => {
    const response = await api.post<PatientMedicationDetailed>(`/medications/patients/${patientId}/medications`, medicationData);
    return response.data;
  },

  // Update patient medication (admin only)
  updatePatientMedication: async (
    patientId: number,
    medicationId: number,
    updateData: PatientMedicationUpdate
  ): Promise<PatientMedicationDetailed> => {
    const response = await api.put<PatientMedicationDetailed>(`/medications/patients/${patientId}/medications/${medicationId}`, updateData);
    return response.data;
  },

  // Stop medication (admin only)
  stopMedication: async (
    patientId: number,
    medicationId: number,
    reason?: string
  ): Promise<PatientMedicationDetailed> => {
    const response = await api.patch(`/medications/patients/${patientId}/medications/${medicationId}/stop`, {
      reason
    });
    return response.data;
  },

  // Create new medication in catalog (admin only)
  createMedication: async (medicationData: MedicationCreate): Promise<Medication> => {
    const response = await api.post<Medication>('/medications', medicationData);
    return response.data;
  },

  // Update medication in catalog (admin only)
  updateMedication: async (id: number, medicationData: Partial<MedicationCreate>): Promise<Medication> => {
    const response = await api.put<Medication>(`/medications/${id}`, medicationData);
    return response.data;
  },

  // Delete medication from catalog (admin only)
  deleteMedication: async (id: number): Promise<void> => {
    await api.delete(`/medications/${id}`);
  }
};
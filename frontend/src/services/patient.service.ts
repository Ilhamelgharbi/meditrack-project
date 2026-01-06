// src/services/patient.service.ts
import api from './api';
import type { PatientProfile, PatientUpdate, PatientAdminUpdate } from '../types/patient.types';
import type { AdherenceDashboard } from '../types/adherence.types';

export const patientService = {
  // Get all patients (Admin only)
  getAllPatients: async (): Promise<PatientProfile[]> => {
    const response = await api.get<PatientProfile[]>('/patients/');
    return response.data;
  },

  // Get patient by ID (Admin only)
  getPatientById: async (patientId: number): Promise<PatientProfile> => {
    const response = await api.get<PatientProfile>(`/patients/${patientId}`);
    return response.data;
  },

  // Get current user's patient profile
  getMyProfile: async (): Promise<PatientProfile> => {
    const response = await api.get<PatientProfile>('/patients/me/profile');
    return response.data;
  },

  // Update current user's patient profile
  updateMyProfile: async (data: PatientUpdate): Promise<PatientProfile> => {
    const response = await api.put<PatientProfile>('/patients/me/profile', data);
    return response.data;
  },

  // Admin updates patient (Admin only)
  updatePatientByAdmin: async (
    patientId: number,
    data: PatientAdminUpdate
  ): Promise<PatientProfile> => {
    const response = await api.put<PatientProfile>(
      `/patients/${patientId}/admin-update`,
      data
    );
    return response.data;
  },

  // Get adherence dashboard for current patient
  getAdherenceDashboard: async (): Promise<AdherenceDashboard> => {
    const response = await api.get<AdherenceDashboard>('/adherence/dashboard');
    return response.data;
  },
};

// Alias for easier imports
export const patientsAPI = patientService;
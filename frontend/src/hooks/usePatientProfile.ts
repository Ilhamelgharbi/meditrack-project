// src/hooks/usePatientProfile.ts
import { useState, useEffect } from 'react';
import { patientService } from '../services/patient.service';
import type { PatientProfile, PatientUpdate } from '../types/patient.types';

export const usePatientProfile = () => {
  const [patientData, setPatientData] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patientService.getMyProfile();
      setPatientData(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load profile';
      setError(message);
      console.error('Error fetching profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (data: PatientUpdate) => {
    try {
      const updated = await patientService.updateMyProfile(data);
      setPatientData(updated);
      return updated;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update profile';
      setError(message);
      throw new Error(message);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  return {
    patientData,
    loading,
    error,
    updateProfile,
    refetch: fetchProfile,
  };
};
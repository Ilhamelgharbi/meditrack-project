// src/hooks/usePatientList.ts
import { useState, useEffect } from 'react';
import { patientService } from '../services/patient.service';
import type { PatientProfile } from '../types/patient.types';

export const usePatientList = () => {
  const [patients, setPatients] = useState<PatientProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patientService.getAllPatients();
      setPatients(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load patients';
      setError(message);
      console.error('Error fetching patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  return {
    patients,
    loading,
    error,
    refetch: fetchPatients,
  };
};
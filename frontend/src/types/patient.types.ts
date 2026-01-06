// src/types/patient.types.ts
export type GenderEnum = 'male' | 'female' | 'other';
export type StatusEnum = 'stable' | 'critical' | 'under_observation';

export interface User {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  role: string;
}

export interface PatientProfile {
  id: number;
  user_id: number;
  date_of_birth?: string;
  gender?: GenderEnum;
  blood_type?: string;
  height?: number;
  weight?: number;
  status: StatusEnum;
  medical_history?: string;
  allergies?: string;
  current_medications?: string;
  assigned_admin_id?: number;
  created_at: string;
  updated_at?: string;
  user?: User;
  // Optional fields for UI
  adherence?: number;
  medicationCount?: number;
  active_meds?: string[];
}

export interface PatientUpdate {
  email?: string;
  phone?: string;
  date_of_birth?: string;
  gender?: GenderEnum;
  blood_type?: string;
  height?: number;
  weight?: number;
  medical_history?: string;
  allergies?: string;
  current_medications?: string;
}

export interface PatientAdminUpdate extends PatientUpdate {
  status?: StatusEnum;
  assigned_admin_id?: number;
}
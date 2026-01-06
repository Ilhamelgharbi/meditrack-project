// src/types/medications.ts
export const MedicationForm = {
  tablet: "tablet",
  capsule: "capsule",
  syrup: "syrup",
  injection: "injection",
  cream: "cream",
  drops: "drops",
  inhaler: "inhaler",
  patch: "patch"
} as const;

export type MedicationFormType = typeof MedicationForm[keyof typeof MedicationForm];

export const MedicationStatus = {
  pending: "pending",
  active: "active",
  stopped: "stopped"
} as const;

export type MedicationStatusType = typeof MedicationStatus[keyof typeof MedicationStatus];

export interface Medication {
  id: number;
  name: string;
  form: MedicationFormType;
  default_dosage?: string;
  side_effects?: string;
  warnings?: string;
  created_by: number;
  created_at: string;
  updated_at?: string;
}

export interface PatientMedication {
  id: number;
  patient_id: number;
  medication_id: number;
  dosage: string;
  instructions?: string;
  times_per_day: number;
  start_date: string;
  end_date?: string;
  status: MedicationStatusType;
  confirmed_by_patient: boolean;
  assigned_by_doctor: number;
  created_at: string;
  updated_at?: string;
  medication?: Medication;
  patient?: UserBasicInfo;
  assigning_doctor?: UserBasicInfo;
}

export interface PatientMedicationDetailed extends PatientMedication {
  medication?: Medication;
}

export interface UserBasicInfo {
  id: number;
  full_name: string;
  email: string;
}

export interface MedicationCreate {
  name: string;
  form: MedicationFormType;
  default_dosage?: string;
  side_effects?: string;
  warnings?: string;
}

export interface PatientMedicationCreate {
  medication_id: number;
  dosage: string;
  instructions?: string;
  times_per_day: number;
  start_date: string;
  end_date?: string;
}

export interface PatientMedicationUpdate {
  dosage?: string;
  instructions?: string;
  times_per_day?: number;
  start_date?: string;
  end_date?: string;
}

export interface MedicationFilters {
  status?: MedicationStatusType;
  limit?: number;
  search?: string;
  include_inactive?: boolean;
}
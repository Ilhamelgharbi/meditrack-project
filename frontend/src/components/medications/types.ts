// src/components/medications/types.ts
import type { PatientMedicationDetailed, Medication } from '../../types/medications.types';

export interface MedicationCardProps {
  medication: PatientMedicationDetailed;
  onView?: (medication: PatientMedicationDetailed) => void;
  onEdit?: (medication: PatientMedicationDetailed) => void;
  onDelete?: (medication: PatientMedicationDetailed) => void;
  showActions?: boolean;
  compact?: boolean;
  className?: string;
}

export interface MedicationListProps {
  medications: PatientMedicationDetailed[];
  onView?: (medication: PatientMedicationDetailed) => void;
  onEdit?: (medication: PatientMedicationDetailed) => void;
  onDelete?: (medication: PatientMedicationDetailed) => void;
  loading?: boolean;
  emptyMessage?: string;
  showActions?: boolean;
  compact?: boolean;
  className?: string;
}

export interface MedicationDetailsProps {
  medication: PatientMedicationDetailed;
  onClose: () => void;
  onEdit?: (medication: PatientMedicationDetailed) => void;
  onDelete?: (medication: PatientMedicationDetailed) => void;
  showActions?: boolean;
}

export interface MedicationStatsProps {
  medications: PatientMedicationDetailed[];
  className?: string;
}

export type MedicationStatusBadgeProps = {
  status: 'pending' | 'active' | 'stopped';
  className?: string;
};

export interface MedicationImageProps {
  src?: string;
  alt: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  fallbackIcon?: React.ComponentType<{ size?: number; className?: string }>;
}

// Admin-specific interfaces
export interface AdminMedicationCardProps {
  medication: Medication;
  onView?: (medication: Medication) => void;
  onEdit?: (medication: Medication) => void;
  onDelete?: (medication: Medication) => void;
  showActions?: boolean;
  compact?: boolean;
  className?: string;
}

export interface AdminMedicationListProps {
  medications: Medication[];
  onView?: (medication: Medication) => void;
  onEdit?: (medication: Medication) => void;
  onDelete?: (medication: Medication) => void;
  loading?: boolean;
  emptyMessage?: string;
  showActions?: boolean;
  compact?: boolean;
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
  className?: string;
}

export interface AdminMedicationDetailsProps {
  medication: Medication;
  onClose: () => void;
  onEdit?: (medication: Medication) => void;
  onDelete?: (medication: Medication) => void;
  showActions?: boolean;
}

export interface AdminMedicationFormProps {
  medication?: Medication;
  onClose: () => void;
  onSubmit: (data: MedicationFormData) => void;
  isLoading?: boolean;
  mode?: 'create' | 'edit';
}

export interface AdminMedicationDeleteProps {
  medication: Medication;
  onClose: () => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

export interface MedicationFormData {
  name: string;
  form: string;
  default_dosage: string;
  side_effects: string;
  warnings: string;
}
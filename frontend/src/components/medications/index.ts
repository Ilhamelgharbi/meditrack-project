// src/components/medications/index.ts
// Note: Removed unused exports for MedicationList, MedicationStats, MedicationModal, and MedicationFormModal
// These components are marked as UNUSED in their respective files but kept for reference
export { MedicationImage } from './MedicationImage';
export { MedicationStatusBadge } from './MedicationStatusBadge';
export { MedicationCard } from './MedicationCard';
export { MedicationDetails } from './MedicationDetails';

// Shared components
export { MedicationSearchFilter } from './MedicationSearchFilter';
export { MedicationLoadingState } from './MedicationLoadingState';
export { MedicationEmptyState } from './MedicationEmptyState';
export { MedicationDashboardStats } from './MedicationDashboardStats';

// Patient components
export { PatientMedicationCard } from './PatientMedicationCard';
export { PatientMedicationList } from './PatientMedicationList';

// Admin components
export { AdminMedicationCard } from './AdminMedicationCard';
export { AdminMedicationList } from './AdminMedicationList';
export { AdminMedicationDetails } from './AdminMedicationDetails';
export { AdminMedicationForm } from './AdminMedicationForm';
export { AdminMedicationDelete } from './AdminMedicationDelete';

// New simplified components
export { SimpleMedicationList, type SimpleMedicationData } from './SimpleMedicationList';
export { StopMedicationModal } from './StopMedicationModal';
export { MedicationAssignModal } from './MedicationAssignModal';
export { MedicationEditModal } from './MedicationEditModal';
export { MedicationDetailsModal } from './MedicationDetailsModal';
export { PatientMedicationManagement } from './PatientMedicationManagement';

export * from './types';
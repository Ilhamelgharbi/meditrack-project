import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import { patientsAPI } from '../../services/patient.service';
import type { PatientProfile } from '../../types/patient.types';
import { useAuth } from '../../contexts/AuthContext';
import { PatientProfileTabs } from '@/components/patient';

const PatientDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [editFormData, setEditFormData] = useState<Partial<PatientProfile & {email?: string, phone?: string}>>({});

  useEffect(() => {
    const fetchPatient = async () => {
      try {
        setLoading(true);
        setError(null);

        let patientData: PatientProfile;

        // Check if current user is a patient viewing their own profile
        // If id is undefined/null, we're on /patients/me route (patient viewing own profile)
        // If id is a number string, we're on /patients/:id route (admin viewing patient)
        const isPatientViewingOwnProfile = user?.role === 'patient' && (!id || id === 'me');

        if (isPatientViewingOwnProfile) {
          // Use /me/profile endpoint for patients viewing their own profile
          patientData = await patientsAPI.getMyProfile();
        } else if (id) {
          // Use admin endpoint for admins viewing patient details
          patientData = await patientsAPI.getPatientById(parseInt(id));
        } else {
          // Should not happen - admin without patient ID
          throw new Error('No patient ID provided for admin view');
        }

        // Ensure we have the correct data structure
        if (!patientData) {
          throw new Error('No patient data received');
        }

        // Remove mock active meds - will be fetched from real API
        // Remove mock adherence - real adherence will be fetched by PatientProfileTabs component

        // Create properly typed patient object
        const enhancedPatient: PatientProfile = {
          ...patientData
          // Remove active_meds - this will be handled by the medication management component
          // Remove adherence - real adherence will be fetched by PatientProfileTabs
        };

        setPatient(enhancedPatient);
      } catch (err) {
        console.error('Error fetching patient:', err);
        setError(err instanceof Error ? err.message : 'Failed to load patient details');
      } finally {
        setLoading(false);
      }
    };

    fetchPatient();
  }, [id, user]);

  const handleSaveProfile = async () => {
    if (!patient) return;

    try {
      setSaving(true);
      setError(null);

      // Validate Moroccan phone number format if phone is being updated
      if (editFormData.phone) {
        const moroccanPhoneRegex = /^(\+212|0)[5-7]\d{8}$/;
        if (!moroccanPhoneRegex.test(editFormData.phone.replace(/\s/g, ''))) {
          throw new Error('Invalid Moroccan phone number. Format: +212XXXXXXXXX or 0XXXXXXXXX (must start with 5, 6, or 7)');
        }
      }

      // Validate email format if email is being updated
      if (editFormData.email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(editFormData.email)) {
          throw new Error('Invalid email format');
        }

        // Confirm email change
        if (editFormData.email !== patient.user?.email) {
          const confirmChange = window.confirm(
            `Are you sure you want to change the email from "${patient.user?.email}" to "${editFormData.email}"?\n\nThis will be used for login and communication.`
          );
          if (!confirmChange) {
            setSaving(false);
            return;
          }
        }
      }

      // Determine if this is a patient self-update or admin update
      const isPatientSelfUpdate = user?.role === 'patient' && (!id || id === 'me');
      
      let updatedPatient: PatientProfile;
      
      if (isPatientSelfUpdate) {
        // Patient updating their own profile
        updatedPatient = await patientsAPI.updateMyProfile(editFormData);
      } else if (user?.role === 'admin' && patient.id) {
        // Admin updating patient profile
        updatedPatient = await patientsAPI.updatePatientByAdmin(patient.id, editFormData);
      } else {
        throw new Error('Unauthorized to update this profile');
      }

      // Update the local state with the response
      setPatient(updatedPatient);
      setIsEditingProfile(false);
      setEditFormData({});
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleEditClick = () => {
    if (isEditingProfile) {
      handleSaveProfile();
    } else {
      // Initialize form data with current patient data
      setEditFormData({
        email: patient?.user?.email,
        phone: patient?.user?.phone,
        weight: patient?.weight,
        height: patient?.height,
        blood_type: patient?.blood_type,
        gender: patient?.gender,
        date_of_birth: patient?.date_of_birth,
        allergies: patient?.allergies,
        medical_history: patient?.medical_history,
        current_medications: patient?.current_medications,
      });
      setIsEditingProfile(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditingProfile(false);
    setEditFormData({});
    setError(null);
  };

  const updateFormData = (field: keyof (PatientProfile & {email?: string, phone?: string}), value: string | number | undefined) => {
    setEditFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return <DashboardLoadingModal />;
  }

  if (error || !patient) {
    return <DashboardErrorModal error={error || 'Patient not found'} onRetry={() => navigate('/patients')} />;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn pb-10">
      {patient && (
        <PatientProfileTabs
          patient={patient}
          userRole={user?.role || 'patient'}
          isEditing={isEditingProfile}
          saving={saving}
          editFormData={editFormData}
          onEditToggle={handleEditClick}
          onSave={handleSaveProfile}
          onCancel={handleCancelEdit}
          onFormDataChange={updateFormData}
          error={error}
          onErrorDismiss={() => setError(null)}
        />
      )}
    </div>
  );
};

export default PatientDetailsPage;

// src/pages/admin/PatientDetails.tsx
import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { patientsAPI } from '../../services/patient.service';
import type { PatientProfile } from '../../types/patient.types';
import { ArrowLeft, Loader2, AlertTriangle } from 'lucide-react';
import { PatientProfileTabs } from '../../components/patient/PatientProfileTabs';

const PatientDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Patient state
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editFormData, setEditFormData] = useState<Partial<PatientProfile & {email?: string, phone?: string}>>({});

  // Fetch patient data on mount
  useEffect(() => {
    if (id) {
      fetchPatientDetails();
    }
  }, [id]);

  const fetchPatientDetails = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patientsAPI.getPatientById(parseInt(id!));
      setPatient(data);
      setEditFormData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patient details');
      console.error('Error fetching patient:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Handle save patient updates
  const handleSave = async () => {
    if (!patient || !id) return;
    
    try {
      setSaving(true);
      setError(null);
      
      await patientsAPI.updatePatientByAdmin(parseInt(id), {
        status: editFormData.status,
        medical_history: editFormData.medical_history,
        allergies: editFormData.allergies,
      });
      
      await fetchPatientDetails();
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update patient');
      console.error('Error updating patient:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/admin/patients')} leftIcon={<ArrowLeft size={16} />}>
            Back to Patients
          </Button>
        </div>
        <Card className="p-8 text-center">
          <Loader2 size={48} className="animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-600">Loading patient details...</p>
        </Card>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/admin/patients')} leftIcon={<ArrowLeft size={16} />}>
            Back to Patients
          </Button>
        </div>
        <Card className="p-8 text-center">
          <AlertTriangle size={48} className="text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error || 'Patient not found'}</p>
          <Button onClick={() => navigate('/admin/patients')}>Back to Patients</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn pb-10">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/admin/patients')} leftIcon={<ArrowLeft size={16} />}>
          Back to Patients
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Patient Details</h1>
          <p className="text-slate-500 mt-1">Manage patient information and medical records</p>
        </div>
      </div>

      {/* Patient Profile Tabs - Profile, Medications, Analytics */}
      <PatientProfileTabs
        patient={patient}
        userRole="admin"
        isEditing={isEditing}
        saving={saving}
        editFormData={editFormData}
        onEditToggle={() => setIsEditing(!isEditing)}
        onSave={handleSave}
        onCancel={() => {
          setIsEditing(false);
          setEditFormData(patient);
        }}
        onFormDataChange={(field, value) => {
          setEditFormData(prev => ({ ...prev, [field]: value }));
        }}
        error={error}
        onErrorDismiss={() => setError(null)}
      />
    </div>
  );
};

export default PatientDetailsPage;

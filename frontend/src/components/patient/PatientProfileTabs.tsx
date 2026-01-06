import { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Input } from '../common/Input';
import {
  Pill, AlertTriangle, Stethoscope
} from 'lucide-react';
import type { PatientProfile } from '../../types/patient.types';
import { StatusBadge } from '../patient';
import { PatientProfileHeader, type PatientHeaderData } from '../shared/PatientProfileHeader';
import { medicationService } from '../../services/medications.service';
import { adherenceService } from '../../services/adherence.service';
import type { PatientMedicationDetailed } from '../../types/medications.types';
import type { AdherenceStats } from '../../services/adherence.service';
import { PatientMedicationManagement } from '../medications/PatientMedicationManagement';
import {
  AdherenceStatsCard,
  AdherenceChart
} from '../common';

interface PatientProfileTabsProps {
  patient: PatientProfile;
  userRole: 'patient' | 'admin';
  isEditing: boolean;
  saving: boolean;
  editFormData: Partial<PatientProfile & {email?: string, phone?: string}>;
  onEditToggle: () => void;
  onSave: () => void;
  onCancel: () => void;
  onFormDataChange: (field: keyof (PatientProfile & {email?: string, phone?: string}), value: string | number | undefined) => void;
  error?: string | null;
  onErrorDismiss?: () => void;
}

export const PatientProfileTabs = ({
  patient,
  userRole,
  isEditing,
  saving: _saving,
  editFormData,
  onEditToggle: _onEditToggle,
  onSave: _onSave,
  onCancel: _onCancel,
  onFormDataChange,
  error,
  onErrorDismiss
}: PatientProfileTabsProps) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'medications' | 'analytics'>('profile');

  const handleTabChange = (tab: 'profile' | 'medications' | 'analytics') => {
    setActiveTab(tab);
    // Refresh medication data when switching to medications tab
    if (tab === 'medications' && userRole === 'admin') {
      fetchPatientMedications();
    }
    // Fetch adherence data when switching to analytics tab
    if (tab === 'analytics' && userRole === 'admin') {
      fetchPatientAdherenceData();
    }
  };

  // Medication state for overview tab
  const [medications, setMedications] = useState<PatientMedicationDetailed[]>([]);
  const [medicationsLoading, setMedicationsLoading] = useState(false);
  const [medicationsError, setMedicationsError] = useState<string | null>(null);

  // Adherence state for analytics tab
  const [adherenceData, setAdherenceData] = useState<any[]>([]);
  const [adherenceStats, setAdherenceStats] = useState<any>(null);

  // Fetch medications and adherence data when component mounts or patient changes
  useEffect(() => {
    // Fetch medications for both patients and admins since it's shown in profile
    fetchPatientMedications();
    // Fetch adherence data for both patients and admins since it's shown in profile
    fetchPatientAdherenceData();
  }, [patient.user_id, userRole]);

  const fetchPatientMedications = async () => {
    try {
      setMedicationsLoading(true);
      setMedicationsError(null);

      const medicationData = await medicationService.getPatientMedications(patient.user_id, {
        limit: 50,
        include_inactive: false
      });
      setMedications(medicationData);
    } catch (err) {
      setMedicationsError(err instanceof Error ? err.message : 'Failed to fetch medications');
      console.error('Error fetching medications:', err);
    } finally {
      setMedicationsLoading(false);
    }
  };

  const fetchPatientAdherenceData = async () => {
    try {
      let stats: AdherenceStats;

      if (userRole === 'patient') {
        // For patients viewing their own profile, use the patient endpoint
        stats = await adherenceService.getStats('weekly');
      } else {
        // For admins viewing patient profiles, use the admin endpoint
        stats = await adherenceService.getPatientAdherenceStats(patient.user_id, 'weekly');
      }

      setAdherenceStats(stats);

      // Also fetch chart data for analytics tab (only for admins)
      if (userRole === 'admin') {
        const dashboardData = await adherenceService.getPatientDashboard(patient.user_id);

        // Transform chart data for the chart component
        const transformedData = dashboardData.chart_data.map((item: any) => ({
          date: item.date,
          score: item.score,
          missed: item.scheduled - item.taken
        }));
        setAdherenceData(transformedData);
      }

    } catch (err) {
      console.error('Error fetching adherence data:', err);
    }
  };

  // Determine available tabs based on user role
  const availableTabs = userRole === 'admin'
    ? ['profile', 'medications', 'analytics'] as const
    : ['profile'] as const;

  // Prepare patient header data
  const patientHeaderData: PatientHeaderData = {
    fullName: patient.user?.full_name || 'Unknown Patient',
    email: patient.user?.email || '',
    phone: patient.user?.phone,
    dateOfBirth: patient.date_of_birth,
    weight: patient.weight,
    height: patient.height,
    bloodType: patient.blood_type,
    adherence: adherenceStats?.adherence_score || patient.adherence || 0,
    status: patient.status,
    role: userRole
  };

  return (
    <div className="space-y-6">
      {/* Patient Header */}
      <PatientProfileHeader
        patient={patientHeaderData}
        isEditing={isEditing}
        saving={_saving}
        canEdit={true}
        isPatientViewingOwnProfile={userRole === 'patient'}
        onEditClick={_onEditToggle}
        onSave={_onSave}
        onCancel={_onCancel}
        showAdminActions={userRole === 'admin'}
        onViewReports={() => {}}
        onPrescribe={() => {}}
      />

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex space-x-8">
          {availableTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabChange(tab)}
              className={`pb-4 px-2 font-medium text-sm transition-all relative ${
                activeTab === tab
                  ? 'text-blue-600'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab === 'profile' ? 'Clinical Profile' :
               tab === 'medications' ? 'Medications' :
               'Analytics'}
              {activeTab === tab && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-t-full"></span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'profile' && (
        <>
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
              <AlertTriangle size={20} className="text-red-500 flex-shrink-0" />
              <p className="text-red-800 text-sm">{error}</p>
              {onErrorDismiss && (
                <button
                  onClick={onErrorDismiss}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              )}
            </div>
          )}

          {/* CLINICAL PROFILE */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
            {/* Vitals & Stats */}
            <div className="space-y-6">
              <Card title="Vitals & Attributes">
                <div className="space-y-4">
                  {isEditing ? (
                    <>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Weight (kg)</label>
                        <Input
                          type="number"
                          value={editFormData.weight || ''}
                          onChange={(e) => onFormDataChange('weight', parseFloat(e.target.value) || undefined)}
                          placeholder="Enter weight"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Height (cm)</label>
                        <Input
                          type="number"
                          value={editFormData.height || ''}
                          onChange={(e) => onFormDataChange('height', parseFloat(e.target.value) || undefined)}
                          placeholder="Enter height"
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      {patient.weight && (
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-slate-500 text-sm">Weight</span>
                          <span className="font-bold text-slate-900">{patient.weight} kg</span>
                        </div>
                      )}
                      {patient.height && (
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-slate-500 text-sm">Height</span>
                          <span className="font-bold text-slate-900">{patient.height} cm</span>
                        </div>
                      )}
                    </>
                  )}
                  {isEditing ? (
                    <>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Blood Type</label>
                        <select
                          value={editFormData.blood_type || ''}
                          onChange={(e) => onFormDataChange('blood_type', e.target.value)}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">Select blood type</option>
                          <option value="A+">A+</option>
                          <option value="A-">A-</option>
                          <option value="B+">B+</option>
                          <option value="B-">B-</option>
                          <option value="AB+">AB+</option>
                          <option value="AB-">AB-</option>
                          <option value="O+">O+</option>
                          <option value="O-">O-</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Gender</label>
                        <select
                          value={editFormData.gender || ''}
                          onChange={(e) => onFormDataChange('gender', e.target.value as 'male' | 'female' | 'other')}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">Select gender</option>
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Date of Birth</label>
                        <Input
                          type="date"
                          value={editFormData.date_of_birth || ''}
                          onChange={(e) => onFormDataChange('date_of_birth', e.target.value)}
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      {patient.blood_type && (
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-slate-500 text-sm">Blood Type</span>
                          <span className="font-bold text-slate-900">{patient.blood_type}</span>
                        </div>
                      )}
                      {patient.gender && (
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-slate-500 text-sm">Gender</span>
                          <span className="font-bold text-slate-900">{patient.gender}</span>
                        </div>
                      )}
                      {patient.date_of_birth && (
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-slate-500 text-sm">Date of Birth</span>
                          <span className="font-bold text-slate-900">{new Date(patient.date_of_birth).toLocaleDateString()}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </Card>

              {/* Contact Information */}
              <Card title="Contact Information">
                <div className="space-y-3">
                  {isEditing ? (
                    <>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Email</label>
                        <Input
                          type="email"
                          value={editFormData.email || patient.user?.email || ''}
                          onChange={(e) => onFormDataChange('email', e.target.value)}
                          placeholder="Enter email"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Phone (Moroccan)</label>
                        <Input
                          type="tel"
                          value={editFormData.phone || patient.user?.phone || ''}
                          onChange={(e) => onFormDataChange('phone', e.target.value)}
                          placeholder="+212XXXXXXXXX or 0XXXXXXXXX"
                        />
                        <p className="text-xs text-slate-500">Format: +212 followed by 9 digits starting with 5, 6, or 7</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-slate-500 text-sm">Email</span>
                        <span className="font-bold text-slate-900 text-sm">{patient.user?.email}</span>
                      </div>
                      {patient.user?.phone && (
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-slate-500 text-sm">Phone</span>
                          <span className="font-bold text-slate-900">{patient.user?.phone}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </Card>

              {/* Patient Status (Admin Only) */}
              {userRole === 'admin' && (
                <Card title="Patient Status">
                  <div className="space-y-3">
                    {isEditing ? (
                      <div className="space-y-2">
                        <label className="text-slate-500 text-sm">Status</label>
                        <select
                          value={editFormData.status || patient.status}
                          onChange={(e) => onFormDataChange('status', e.target.value as 'stable' | 'critical' | 'under_observation')}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="stable">Stable</option>
                          <option value="critical">Critical</option>
                          <option value="under_observation">Under Observation</option>
                        </select>
                      </div>
                    ) : (
                      <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-slate-500 text-sm">Current Status</span>
                        <StatusBadge status={patient.status} />
                      </div>
                    )}
                  </div>
                </Card>
              )}
            </div>

            {/* History & Notes */}
            <div className="lg:col-span-2 space-y-6">
              <Card title="Medical History">
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <AlertTriangle size={14} className="text-amber-500"/> Allergies
                      </h4>
                      {isEditing ? (
                        <textarea
                          value={editFormData.allergies || ''}
                          onChange={(e) => onFormDataChange('allergies', e.target.value)}
                          placeholder="List any allergies..."
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                          rows={3}
                          maxLength={500}
                        />
                      ) : (
                        <div className="p-3 bg-amber-50 text-amber-800 rounded-lg border border-amber-100 text-sm font-medium">
                          {patient.allergies || 'No known allergies'}
                        </div>
                      )}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <Stethoscope size={14} className="text-blue-500"/> Medical History
                      </h4>
                      {isEditing ? (
                        <textarea
                          value={editFormData.medical_history || ''}
                          onChange={(e) => onFormDataChange('medical_history', e.target.value)}
                          placeholder="Enter medical history..."
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                          rows={3}
                          maxLength={2000}
                        />
                      ) : (
                        <div className="p-3 bg-blue-50 text-blue-800 rounded-lg border border-blue-100 text-sm font-medium">
                          {patient.medical_history || 'No medical history recorded'}
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                      <Pill size={14} className="text-green-500"/> Current Medications
                    </h4>
                    {medicationsLoading ? (
                      <div className="p-3 bg-green-50 text-green-800 rounded-lg border border-green-100 text-sm">
                        Loading medications...
                      </div>
                    ) : medicationsError ? (
                      <div className="p-3 bg-red-50 text-red-800 rounded-lg border border-red-100 text-sm">
                        Error loading medications: {medicationsError}
                      </div>
                    ) : medications.length > 0 ? (
                      <div className="space-y-2">
                        {medications
                          .filter(med => med.status === 'active')
                          .slice(0, 3) // Show only first 3 active medications
                          .map((medication) => (
                            <div key={medication.id} className="flex items-center justify-between p-2 bg-green-50 text-green-800 rounded-lg border border-green-100 text-sm">
                              <span className="font-medium">{medication.medication?.name}</span>
                              <span className="text-green-600">{medication.dosage}</span>
                            </div>
                          ))}
                        {medications.filter(med => med.status === 'active').length > 3 && (
                          <div className="text-xs text-green-600 mt-1">
                            +{medications.filter(med => med.status === 'active').length - 3} more active medications
                          </div>
                        )}
                        {medications.filter(med => med.status === 'active').length === 0 && (
                          <div className="p-3 bg-green-50 text-green-800 rounded-lg border border-green-100 text-sm font-medium">
                            No active medications
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="p-3 bg-green-50 text-green-800 rounded-lg border border-green-100 text-sm font-medium">
                        No medications found
                      </div>
                    )}
                  </div>
                </div>
              </Card>

              {/* Remove Active Medications Summary - use Medications tab instead */}
              {/* {patient.active_meds && patient.active_meds.length > 0 && (
                <Card title="Active Medications Summary">
                  <div className="flex flex-wrap gap-2">
                    {patient.active_meds.map((med, index) => (
                      <span key={index} className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full border border-blue-200">
                        <Pill size={12} />
                        {med}
                      </span>
                    ))}
                  </div>
                </Card>
              )} */}
            </div>
          </div>
        </>
      )}

      {activeTab === 'medications' && userRole === 'admin' && (
        <div className="animate-fadeIn">
          <PatientMedicationManagement
            patientId={patient.user_id}
            isAdmin={userRole === 'admin'}
          />
        </div>
      )}

      {activeTab === 'analytics' && userRole === 'admin' && (
        <div className="animate-fadeIn space-y-6">
          {/* Adherence Stats Cards - Compact Grid */}
          {adherenceStats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <AdherenceStatsCard
                type="score"
                value={adherenceStats.adherence_score}
                totalTaken={adherenceStats.total_taken}
                totalScheduled={adherenceStats.total_scheduled}
                variant="compact"
              />
              <AdherenceStatsCard
                type="streak"
                value={adherenceStats.current_streak}
                variant="compact"
              />
              <AdherenceStatsCard
                type="onTime"
                value={adherenceStats.on_time_score}
                variant="compact"
              />
              <AdherenceStatsCard
                type="bestStreak"
                value={adherenceStats.longest_streak}
                variant="compact"
              />
            </div>
          )}

          {/* Adherence Chart - Full Width */}
          {adherenceData && adherenceData.length > 0 && (
            <AdherenceChart
              data={adherenceData}
              title="Adherence Analytics"
              subtitle="Weekly adherence trend"
            />
          )}
        </div>
      )}
    </div>
  );
};
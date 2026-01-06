import { useState, useEffect } from 'react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatCard } from '../../components/common/StatCard';
import { Plus, Search, ChevronRight, Users, UserCheck, AlertTriangle, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { patientsAPI } from '../../services/patient.service';
import { adherenceService } from '../../services/adherence.service';
import { medicationService } from '../../services/medications.service';
import type { PatientProfile } from '../../types/patient.types';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import { PatientAvatar, StatusBadge, AdherenceIndicator, AgeDisplay } from '@/components/patient';

const PatientsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [patients, setPatients] = useState<PatientProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch patients on component mount
  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patientsAPI.getAllPatients();

      // Fetch active medications and adherence for each patient
      const patientsWithData = await Promise.all(
        data.map(async (patient: PatientProfile) => {
          try {
            // Fetch adherence stats for this patient using patient.user_id
            let adherence = 0;
            try {
              const adherenceStats = await adherenceService.getPatientAdherenceStats(patient.user_id, 'weekly');
              adherence = adherenceStats.adherence_score;
            } catch (adherenceError) {
              console.warn(`Failed to fetch adherence for patient ${patient.id}:`, adherenceError);
              // Keep default adherence of 0 if fetch fails
            }

            // Fetch active medication count for this patient
            let medicationCount = 0;
            try {
              const medications = await medicationService.getPatientMedications(patient.user_id);
              medicationCount = medications.filter(med => med.status === 'active').length;
            } catch (medError) {
              console.warn(`Failed to fetch medications for patient ${patient.id}:`, medError);
              // Keep default medication count of 0 if fetch fails
            }

            return {
              ...patient,
              adherence,
              medicationCount
            };
          } catch (error) {
            console.warn(`Failed to fetch data for patient ${patient.id}:`, error);
            // Return patient with default values if fetch fails
            return {
              ...patient,
              adherence: 0,
              medicationCount: 0
            };
          }
        })
      );

      setPatients(patientsWithData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patients');
      console.error('Error fetching patients:', err);
    } finally {
      setLoading(false);
    }
  };

  // Filter patients based on search term and status filter
  const filteredPatients = patients.filter(patient => {
    const matchesSearch = !searchTerm ||
      patient.user?.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.user?.email?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = !statusFilter || patient.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <DashboardLoadingModal />;
  }

  if (error) {
    return <DashboardErrorModal error={error} onRetry={fetchPatients} />;
  }

  // Calculate stats
  const stablePatients = patients.filter(p => p.status === 'stable').length;
  const criticalPatients = patients.filter(p => p.status === 'critical').length;
  const underObservation = patients.filter(p => p.status === 'under_observation').length;

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
            <h1 className="text-2xl font-bold text-slate-900">Patients Management</h1>
            <p className="text-base text-slate-600">View and manage patient records</p>
        </div>
        <Button leftIcon={<Plus size={20} />}>Add Patient</Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Patients"
          value={patients.length}
          icon={Users}
          color="bg-blue-500"
          subtitle="Registered in system"
        />
        <StatCard
          title="Stable"
          value={stablePatients}
          icon={UserCheck}
          color="bg-emerald-500"
          subtitle="Good health status"
        />
        <StatCard
          title="Critical"
          value={criticalPatients}
          icon={AlertTriangle}
          color="bg-red-500"
          subtitle="Needs attention"
        />
        <StatCard
          title="Under Observation"
          value={underObservation}
          icon={Eye}
          color="bg-amber-500"
          subtitle="Being monitored"
        />
      </div>

      <Card className="overflow-hidden p-0 border border-slate-200 shadow-sm">
        {/* Toolbar */}
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-3 bg-slate-50/50">
            <div className="relative flex-1">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                    type="text"
                    placeholder="Search patients by name or email..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 shadow-sm"
                />
            </div>
            <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 shadow-sm"
            >
                <option value="">All Status</option>
                <option value="stable">Stable</option>
                <option value="under_observation">Under Observation</option>
                <option value="critical">Critical</option>
            </select>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600 uppercase tracking-wider">Patient</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600 uppercase tracking-wider">Medications</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600 uppercase tracking-wider">Adherence</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-slate-600 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredPatients.map((patient) => (
                <tr key={patient.id} className="hover:bg-slate-50 transition-colors cursor-pointer" onClick={() => navigate(`/admin/patients/${patient.id}`)}>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <PatientAvatar fullName={patient.user?.full_name} size="sm" />
                      <div className="ml-4">
                        <div className="text-base font-medium text-slate-900">{patient.user?.full_name}</div>
                        <div className="text-sm text-slate-500">{patient.user?.email} • <AgeDisplay dateOfBirth={patient.date_of_birth} showLabel={false} /></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-slate-900">{patient.medicationCount || 0}</span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={patient.status} />
                  </td>
                  <td className="px-6 py-4">
                    <AdherenceIndicator adherence={patient.adherence || 0} size="sm" />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="p-2 hover:bg-blue-100 rounded-full text-slate-400 hover:text-blue-600 transition-colors" onClick={(e) => { e.stopPropagation(); navigate(`/admin/patients/${patient.id}`); }}>
                        <ChevronRight size={20} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-between items-center text-base text-slate-600">
            <span>Showing {filteredPatients.length} of {patients.length} patients</span>
            <div className="flex gap-2">
                <Button variant="secondary" className="py-1.5 px-3 text-sm" disabled>Previous</Button>
                <Button variant="secondary" className="py-1.5 px-3 text-sm" disabled>Next</Button>
            </div>
        </div>
      </Card>
    </div>
  );
};

export default PatientsPage;
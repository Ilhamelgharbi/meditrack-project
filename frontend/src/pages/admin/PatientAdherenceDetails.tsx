import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import {
  ArrowLeft, Calendar, BarChart3, History,
  Pill, Loader2, Activity
} from 'lucide-react';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import { adherenceService } from '../../services/adherence.service';
import type { AdherenceStats, AdherenceChartData, MedicationLog } from '../../services/adherence.service';
import { patientService } from '../../services/patient.service';
import { medicationService } from '../../services/medications.service';
import {
  AdherenceStatsCard,
  AdherenceChart,
  AdherenceLogTable,
  MedicationAdherenceCard,
  getAdherenceColor
} from '../../components/common';

interface PatientMedication {
  id: number;
  medication_id: number;
  dosage: string;
  instructions?: string;
  medication?: {
    id: number;
    name: string;
    form: string;
  };
}

type TabType = 'overview' | 'history';
type PeriodType = 'daily' | 'weekly' | 'monthly' | 'overall';

export const PatientAdherenceDetails = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();

  const [patient, setPatient] = useState<any>(null);
  const [medications, setMedications] = useState<PatientMedication[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('weekly');
  const [selectedMedication, setSelectedMedication] = useState<number | null>(null);
  const [stats, setStats] = useState<AdherenceStats | null>(null);
  const [chartData, setChartData] = useState<AdherenceChartData[]>([]);
  const [logs, setLogs] = useState<MedicationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (patientId) {
      fetchPatientData();
    }
  }, [patientId]);

  useEffect(() => {
    if (patientId) {
      fetchAdherenceData();
    }
  }, [patientId, selectedPeriod, selectedMedication]);

  const fetchPatientData = async () => {
    try {
      const patientIdNum = parseInt(patientId!);
      const [patientData, medicationsData] = await Promise.all([
        patientService.getPatientById(patientIdNum),
        medicationService.getPatientMedications(patientIdNum)
      ]);
      setPatient(patientData);
      setMedications(medicationsData);
    } catch (err: any) {
      console.error('Error fetching patient data:', err);
      setError('Failed to load patient data');
    }
  };

  const fetchAdherenceData = async () => {
    try {
      setLoading(true);
      setError(null);

      const patientIdNum = parseInt(patientId!);
      const [statsData, chartDataResult, logsData] = await Promise.all([
        adherenceService.getPatientAdherenceStats(patientIdNum, selectedPeriod, selectedMedication || undefined),
        adherenceService.getChartData(14),
        adherenceService.getPatientLogs(patientIdNum, {
          patient_medication_id: selectedMedication || undefined,
          limit: 50
        })
      ]);

      setStats(statsData);
      setChartData(chartDataResult);
      setLogs(logsData);
    } catch (err: any) {
      console.error('Error fetching adherence data:', err);
      setError('Failed to load adherence data');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !patient) {
    return <DashboardLoadingModal title="Patient Adherence" subtitle="Loading adherence data..." />;
  }

  if (error || !patient) {
    return <DashboardErrorModal 
      title="Patient Adherence" 
      error={error || 'Patient not found'} 
      onRetry={() => navigate('/admin/adherence')} 
      retryButtonText="Back to Adherence Dashboard"
    />;
  }

  // Filter logs by medication if selected
  const filteredLogs = selectedMedication
    ? logs.filter(log => log.patient_medication_id === selectedMedication)
    : logs;

  const tabs = [
    { key: 'overview' as const, label: 'Overview', icon: BarChart3 },
    { key: 'history' as const, label: 'Logs History', icon: History },
  ];

  const periods = [
    { key: 'daily' as const, label: 'Today' },
    { key: 'weekly' as const, label: 'This Week' },
    { key: 'monthly' as const, label: 'This Month' },
    { key: 'overall' as const, label: 'All Time' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => navigate('/admin/adherence')}
          leftIcon={<ArrowLeft size={16} />}
        >
          Back
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">
                {patient.user?.full_name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) || 'P'}
              </span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{patient.user?.full_name}</h1>
              <p className="text-slate-500">Detailed Adherence Analysis</p>
            </div>
          </div>
        </div>
        {stats && (
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-xl border border-slate-200 shadow-sm">
            <span className={`text-2xl font-bold ${getAdherenceColor(stats.adherence_score)}`}>
              {Math.round(stats.adherence_score)}%
            </span>
            <span className="text-sm text-slate-500">Overall</span>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <AdherenceStatsCard
            type="score"
            value={stats.adherence_score}
            totalTaken={stats.total_taken}
            totalScheduled={stats.total_scheduled}
            variant="compact"
          />
          <AdherenceStatsCard
            type="streak"
            value={stats.current_streak}
            variant="compact"
          />
          <AdherenceStatsCard
            type="onTime"
            value={stats.on_time_score}
            variant="compact"
          />
          <AdherenceStatsCard
            type="bestStreak"
            value={stats.longest_streak}
            variant="compact"
          />
        </div>
      )}

      {/* Filters Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {/* Period Filter */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-600 font-medium">Period:</span>
            <div className="flex bg-slate-100 rounded-lg p-1">
              {periods.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setSelectedPeriod(key)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                    selectedPeriod === key
                      ? 'bg-white text-primary-600 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Medication Filter */}
          <div className="flex items-center gap-2 sm:ml-auto">
            <Pill className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-600 font-medium">Medication:</span>
            <select
              value={selectedMedication || ''}
              onChange={(e) => setSelectedMedication(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">All Medications</option>
              {medications.map((med) => (
                <option key={med.id} value={med.id}>
                  {med.medication?.name}
                </option>
              ))}
            </select>
          </div>

          {/* Refresh */}
          <Button 
            onClick={fetchAdherenceData} 
            disabled={loading} 
            variant="secondary"
            className="sm:w-auto"
          >
            {loading ? <Loader2 className="animate-spin w-4 h-4 mr-2" /> : null}
            Refresh
          </Button>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-6">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-all ${
                activeTab === key
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' ? (
        <div className="space-y-6">
          {/* Chart and Medication Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart Data */}
            {chartData.length > 0 && (
              <AdherenceChart
                data={chartData.slice(-14)}
                title="14-Day Adherence Trend"
                subtitle="Daily adherence scores"
              />
            )}

            {/* Medication Breakdown */}
            {medications.length > 0 && (
              <Card>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-teal-100 rounded-lg">
                    <Activity className="w-5 h-5 text-teal-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Medication Breakdown</h2>
                    <p className="text-sm text-slate-500">{medications.length} medications</p>
                  </div>
                </div>

                <div className="space-y-3">
                  {medications.map((medication) => (
                    <MedicationAdherenceCard
                      key={medication.id}
                      medication={medication}
                      patientId={parseInt(patientId!)}
                      selectedPeriod={selectedPeriod}
                    />
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Recent Logs Preview */}
          {logs.length > 0 && (
            <Card>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <History className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Recent Logs</h2>
                    <p className="text-sm text-slate-500">Latest {Math.min(5, logs.length)} logs</p>
                  </div>
                </div>
                <button 
                  onClick={() => setActiveTab('history')}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  View All →
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-2 px-3 font-medium text-slate-600">Date</th>
                      <th className="text-left py-2 px-3 font-medium text-slate-600">Time</th>
                      <th className="text-left py-2 px-3 font-medium text-slate-600">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.slice(0, 5).map((log) => (
                      <tr key={log.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-2 px-3">{new Date(log.scheduled_time).toLocaleDateString()}</td>
                        <td className="py-2 px-3">{new Date(log.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                        <td className="py-2 px-3">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                            log.status === 'taken' ? 'bg-green-100 text-green-700' :
                            log.status === 'skipped' ? 'bg-amber-100 text-amber-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      ) : (
        /* History Tab */
        <AdherenceLogTable
          logs={filteredLogs}
          title="Medication Logs History"
          subtitle={`${filteredLogs.length} total logs for ${patient.user?.full_name}${selectedMedication ? ' (filtered)' : ''}`}
          showFilters={true}
          showActions={false}
        />
      )}
    </div>
  );
};
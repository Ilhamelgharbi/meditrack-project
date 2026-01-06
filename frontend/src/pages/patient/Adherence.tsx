// src/pages/patient/Adherence.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import {
  CheckCircle, Clock, XCircle,
  Plus, Calendar, BarChart3, Activity,
  Pill, X, Loader2, AlertCircle, History
} from 'lucide-react';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import { adherenceService } from '../../services/adherence.service';
import type { AdherenceDashboard } from '../../services/adherence.service';
import { medicationService } from '../../services/medications.service';
import {
  AdherenceStatsCard,
  AdherenceChart,
  AdherenceLogTable,
  MedicationAdherenceCard
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

export const PatientAdherence = () => {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<AdherenceDashboard | null>(null);
  const [medications, setMedications] = useState<PatientMedication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Tab and filter state
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('weekly');
  const [selectedMedicationFilter, setSelectedMedicationFilter] = useState<number | null>(null);
  
  // Modal state
  const [showLogModal, setShowLogModal] = useState(false);
  const [selectedMedication, setSelectedMedication] = useState<PatientMedication | null>(null);
  const [loggingDose, setLoggingDose] = useState(false);

  // Logs history state
  const [allLogs, setAllLogs] = useState<any[]>([]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedLog, setSelectedLog] = useState<any | null>(null);
  const [editForm, setEditForm] = useState({
    status: 'taken' as 'taken' | 'skipped' | 'missed',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch dashboard data, medications, and all logs in parallel
      const [dashboardData, medicationsData, logsData] = await Promise.all([
        adherenceService.getDashboard(),
        medicationService.getPatientMedications(user.id),
        adherenceService.getLogs({ limit: 100 })
      ]);

      setDashboard(dashboardData);
      setMedications(medicationsData);
      setAllLogs(logsData);
    } catch (err: any) {
      console.error('Error fetching adherence data:', err);
      setError(err.message || 'Failed to load adherence data');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentStats = () => {
    if (!dashboard) return null;

    switch (selectedPeriod) {
      case 'daily': return dashboard.daily_stats;
      case 'weekly': return dashboard.weekly_stats;
      case 'monthly': return dashboard.overall_stats;
      case 'overall': return dashboard.overall_stats;
      default: return dashboard.weekly_stats;
    }
  };

  const handleLogDose = async (medication: PatientMedication, status: 'taken' | 'skipped' | 'missed', notes?: string) => {
    try {
      setLoggingDose(true);

      const logData = {
        patient_medication_id: medication.id,
        scheduled_time: new Date().toISOString(),
        status,
        actual_time: status === 'taken' ? new Date().toISOString() : undefined,
        notes,
        skipped_reason: status === 'skipped' ? notes : undefined,
      };

      await adherenceService.logDose(logData);

      // Refresh data
      await fetchData();
      setShowLogModal(false);
      setSelectedMedication(null);
    } catch (err: any) {
      console.error('Error logging dose:', err);
      setError('Failed to log medication dose');
    } finally {
      setLoggingDose(false);
    }
  };

  const handleEditLog = async () => {
    if (!selectedLog) return;
    try {
      setLoggingDose(true);
      const data = {
        actual_time: editForm.status === 'taken' ? new Date().toISOString() : undefined,
        status: editForm.status,
        notes: editForm.notes || undefined
      };
      await adherenceService.updateLog(selectedLog.id, data);
      setShowEditModal(false);
      setSelectedLog(null);
      await fetchData();
    } catch (err: any) {
      console.error('Error updating log:', err);
      setError('Failed to update log');
    } finally {
      setLoggingDose(false);
    }
  };

  const handleDeleteLog = async () => {
    if (!selectedLog) return;
    try {
      setLoggingDose(true);
      await adherenceService.deleteLog(selectedLog.id);
      setShowDeleteModal(false);
      setSelectedLog(null);
      await fetchData();
    } catch (err: any) {
      console.error('Error deleting log:', err);
      setError('Failed to delete log');
    } finally {
      setLoggingDose(false);
    }
  };

  const openEditModal = (log: any) => {
    setSelectedLog(log);
    setEditForm({
      status: log.status,
      notes: log.notes || ''
    });
    setShowEditModal(true);
  };

  const openDeleteModal = (log: any) => {
    setSelectedLog(log);
    setShowDeleteModal(true);
  };

  // Filter logs by medication if selected
  const filteredLogs = selectedMedicationFilter
    ? allLogs.filter(log => log.patient_medication_id === selectedMedicationFilter)
    : allLogs;

  if (loading) {
    return <DashboardLoadingModal title="Medication Adherence" subtitle="Loading your adherence data..." />;
  }

  if (error || !dashboard) {
    return <DashboardErrorModal 
      title="Medication Adherence" 
      error={error || 'Failed to load adherence data'} 
      onRetry={fetchData} 
    />;
  }

  const stats = getCurrentStats();
  if (!stats) return null;

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Medication Adherence</h1>
          <p className="text-slate-500 mt-1">Track your medication compliance</p>
        </div>
        <Button
          onClick={() => setShowLogModal(true)}
          className="bg-primary-600 hover:bg-primary-700 text-white"
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Log Dose
        </Button>
      </div>

      {/* Stats Cards */}
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
              value={selectedMedicationFilter || ''}
              onChange={(e) => setSelectedMedicationFilter(e.target.value ? parseInt(e.target.value) : null)}
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
          {/* Chart and Quick Actions Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart */}
            <div className="lg:col-span-2">
              {dashboard.chart_data && dashboard.chart_data.length > 0 && (
                <AdherenceChart
                  data={dashboard.chart_data.slice(-14)}
                  title="14-Day Adherence Trend"
                  subtitle="Your daily adherence scores"
                />
              )}
            </div>

            {/* Quick Log Actions */}
            <Card variant="elevated">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <Pill className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">Quick Log</h3>
                  <p className="text-xs text-slate-500">Log today's medications</p>
                </div>
              </div>

              <div className="space-y-3">
                {medications.slice(0, 4).map((medication) => (
                  <div key={medication.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-slate-900 text-sm truncate">{medication.medication?.name}</p>
                      <p className="text-xs text-slate-500">{medication.dosage}</p>
                    </div>
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={() => handleLogDose(medication, 'taken')}
                        disabled={loggingDose}
                        className="p-1.5 bg-green-100 hover:bg-green-200 rounded-lg transition-colors"
                        title="Taken"
                      >
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      </button>
                      <button
                        onClick={() => handleLogDose(medication, 'skipped')}
                        disabled={loggingDose}
                        className="p-1.5 bg-amber-100 hover:bg-amber-200 rounded-lg transition-colors"
                        title="Skipped"
                      >
                        <Clock className="w-4 h-4 text-amber-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Medication Breakdown */}
          {medications.length > 0 && (
            <Card variant="elevated">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-teal-100 rounded-lg">
                  <Activity className="w-5 h-5 text-teal-600" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Medication Breakdown</h2>
                  <p className="text-sm text-slate-500">{medications.length} active medications</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {medications.map((medication) => (
                  <MedicationAdherenceCard
                    key={medication.id}
                    medication={medication}
                    selectedPeriod={selectedPeriod}
                  />
                ))}
              </div>
            </Card>
          )}

          {/* Recent Activity */}
          {dashboard.recent_logs && dashboard.recent_logs.length > 0 && (
            <Card variant="elevated">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <History className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Recent Activity</h2>
                    <p className="text-sm text-slate-500">Latest medication logs</p>
                  </div>
                </div>
                <button 
                  onClick={() => setActiveTab('history')}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  View All →
                </button>
              </div>

              <div className="space-y-2">
                {dashboard.recent_logs.slice(0, 5).map((log) => {
                  const statusConfigs = {
                    taken: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Taken' },
                    skipped: { icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50', label: 'Skipped' },
                    missed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: 'Missed' },
                  };
                  const config = statusConfigs[log.status as keyof typeof statusConfigs] || statusConfigs.taken;
                  const StatusIcon = config.icon;

                  return (
                    <div key={log.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                      <div className={`p-2 rounded-lg ${config.bg}`}>
                        <StatusIcon className={`w-4 h-4 ${config.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 text-sm">Medication Dose</p>
                        <p className="text-xs text-slate-500">
                          {new Date(log.scheduled_time).toLocaleString([], {
                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                          })}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
                        {config.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>
      ) : (
        /* History Tab */
        <AdherenceLogTable
          logs={filteredLogs}
          title="Medication Logs History"
          subtitle={`${filteredLogs.length} total logs${selectedMedicationFilter ? ' (filtered)' : ''}`}
          showFilters={true}
          showActions={true}
          onEdit={openEditModal}
          onDelete={openDeleteModal}
        />
      )}

      {/* Log Dose Modal */}
      {showLogModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-900">Log Medication Dose</h3>
                <button
                  onClick={() => { setShowLogModal(false); setSelectedMedication(null); }}
                  className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Select Medication</label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {medications.map((medication) => (
                    <button
                      key={medication.id}
                      onClick={() => setSelectedMedication(medication)}
                      className={`w-full p-3 rounded-xl border-2 transition-all text-left ${
                        selectedMedication?.id === medication.id
                          ? 'border-primary-300 bg-primary-50'
                          : 'border-slate-200 hover:border-primary-200'
                      }`}
                    >
                      <p className="font-medium text-slate-900">{medication.medication?.name}</p>
                      <p className="text-sm text-slate-500">{medication.dosage}</p>
                    </button>
                  ))}
                </div>
              </div>

              {selectedMedication && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Status</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleLogDose(selectedMedication, 'taken')}
                      disabled={loggingDose}
                      className="flex items-center justify-center gap-2 p-4 bg-green-50 hover:bg-green-100 border-2 border-green-200 rounded-xl transition-all disabled:opacity-50"
                    >
                      {loggingDose ? <Loader2 className="animate-spin w-5 h-5" /> : <CheckCircle className="w-5 h-5 text-green-600" />}
                      <span className="font-medium text-green-700">Taken</span>
                    </button>
                    <button
                      onClick={() => handleLogDose(selectedMedication, 'skipped')}
                      disabled={loggingDose}
                      className="flex items-center justify-center gap-2 p-4 bg-amber-50 hover:bg-amber-100 border-2 border-amber-200 rounded-xl transition-all disabled:opacity-50"
                    >
                      {loggingDose ? <Loader2 className="animate-spin w-5 h-5" /> : <Clock className="w-5 h-5 text-amber-600" />}
                      <span className="font-medium text-amber-700">Skipped</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Log Modal */}
      {showEditModal && selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-900">Edit Dose Log</h3>
                <button onClick={() => setShowEditModal(false)} className="p-2 hover:bg-slate-100 rounded-lg">
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Status</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value as any })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="taken">Taken</option>
                  <option value="skipped">Skipped</option>
                  <option value="missed">Missed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Notes (optional)</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  placeholder="Any additional notes..."
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="p-6 border-t border-slate-200 flex gap-3">
              <Button onClick={() => setShowEditModal(false)} variant="secondary" className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleEditLog} disabled={loggingDose} className="flex-1">
                {loggingDose && <Loader2 className="animate-spin w-4 h-4 mr-2" />}
                Update Log
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-900">Delete Dose Log</h3>
                <button onClick={() => setShowDeleteModal(false)} className="p-2 hover:bg-slate-100 rounded-lg">
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-red-50 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
                <div className="flex-1">
                  <p className="text-slate-900 mb-2">Are you sure you want to delete this log?</p>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <p className="text-sm font-medium text-slate-900">{selectedLog.medication_name}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(selectedLog.scheduled_time).toLocaleString()} - {selectedLog.status}
                    </p>
                  </div>
                  <p className="text-sm text-red-600 mt-3">This action cannot be undone.</p>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-200 flex gap-3">
              <Button onClick={() => setShowDeleteModal(false)} variant="secondary" className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleDeleteLog} disabled={loggingDose} className="flex-1 bg-red-600 hover:bg-red-700 text-white">
                {loggingDose && <Loader2 className="animate-spin w-4 h-4 mr-2" />}
                Delete Log
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
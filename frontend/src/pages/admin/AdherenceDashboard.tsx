import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import {
  AlertTriangle, CheckCircle, Clock, XCircle, Search,
  Users, Activity, Shield, Eye, ExternalLink,
  User, AlertCircle as AlertCircleIcon, Target, Zap, Loader2
} from 'lucide-react';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import { adherenceService } from '../../services/adherence.service';
import type { AdherenceDashboard } from '../../services/adherence.service';
import { patientService } from '../../services/patient.service';
import {
  AdherenceChart,
  getAdherenceColor,
  StatCard
} from '../../components/common';

interface PatientOverview {
  id: number;
  name: string;
  adherence_score: number;
  current_streak: number;
  total_medications: number;
  last_log_date?: string;
  risk_level: 'low' | 'medium' | 'high';
}

export const AdminAdherenceDashboard = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<PatientOverview[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientOverview | null>(null);
  const [patientDashboard, setPatientDashboard] = useState<AdherenceDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [patientLoading, setPatientLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'adherence' | 'risk'>('risk');

  useEffect(() => {
    fetchPatientsOverview();
  }, []);

  const fetchPatientsOverview = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get all patients
      const patientsData = await patientService.getAllPatients();

      // Get adherence stats for each patient
      const patientsWithAdherence = await Promise.all(
        patientsData.map(async (patient) => {
          try {
            const stats = await adherenceService.getPatientAdherenceStats(patient.user_id, 'weekly');
            const riskLevel: 'low' | 'medium' | 'high' = stats.adherence_score >= 80 ? 'low' :
                             stats.adherence_score >= 60 ? 'medium' : 'high';

            return {
              id: patient.user_id,
              name: patient.user?.full_name || `Patient ${patient.id}`,
              adherence_score: stats.adherence_score,
              current_streak: stats.current_streak,
              total_medications: 0, // We'll need to get this from medications endpoint
              last_log_date: undefined, // We'll need to get this from logs
              risk_level: riskLevel,
            };
          } catch (err) {
            // If no adherence data, return default values
            return {
              id: patient.user_id,
              name: patient.user?.full_name || `Patient ${patient.id}`,
              adherence_score: 0,
              current_streak: 0,
              total_medications: 0,
              risk_level: 'high' as const,
            };
          }
        })
      );

      setPatients(patientsWithAdherence);
    } catch (err: any) {
      console.error('Error fetching patients overview:', err);
      setError(err.message || 'Failed to load patients data');
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientDetails = async (patient: PatientOverview) => {
    try {
      setPatientLoading(true);
      setSelectedPatient(patient);

      const dashboard = await adherenceService.getPatientDashboard(patient.id);
      setPatientDashboard(dashboard);
    } catch (err: any) {
      console.error('Error fetching patient details:', err);
      setError('Failed to load patient adherence details');
    } finally {
      setPatientLoading(false);
    }
  };

  const getRiskConfig = (risk: string) => {
    switch (risk) {
      case 'low':
        return {
          color: 'text-secondary-600',
          bg: 'bg-secondary-50 border-secondary-200',
          icon: <Shield className="w-5 h-5 text-secondary-600" />,
          label: 'Low Risk',
          description: 'Excellent adherence'
        };
      case 'medium':
        return {
          color: 'text-warning',
          bg: 'bg-yellow-50 border-yellow-200',
          icon: <AlertTriangle className="w-5 h-5 text-warning" />,
          label: 'Medium Risk',
          description: 'Needs attention'
        };
      case 'high':
        return {
          color: 'text-error',
          bg: 'bg-red-50 border-red-200',
          icon: <AlertCircleIcon className="w-5 h-5 text-error" />,
          label: 'High Risk',
          description: 'Requires intervention'
        };
      default:
        return {
          color: 'text-gray-600',
          bg: 'bg-gray-50 border-gray-200',
          icon: <Clock className="w-5 h-5 text-gray-600" />,
          label: 'Unknown',
          description: 'No data available'
        };
    }
  };

  const filteredAndSortedPatients = patients
    .filter(patient => patient.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'adherence':
          return b.adherence_score - a.adherence_score;
        case 'risk':
          const riskOrder = { high: 3, medium: 2, low: 1 };
          return riskOrder[b.risk_level] - riskOrder[a.risk_level];
        default:
          return 0;
      }
    });

  const riskSummary = {
    low: patients.filter(p => p.risk_level === 'low').length,
    medium: patients.filter(p => p.risk_level === 'medium').length,
    high: patients.filter(p => p.risk_level === 'high').length,
  };

  if (loading) {
    return <DashboardLoadingModal title="Adherence Management" subtitle="Loading patient adherence data..." />;
  }

  if (error) {
    return <DashboardErrorModal 
      title="Adherence Management" 
      error={error} 
      onRetry={fetchPatientsOverview} 
    />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Adherence Management</h1>
        <p className="text-slate-500 mt-1">Monitor and support patient medication compliance</p>
      </div>

      {/* Risk Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Low Risk Patients"
          value={riskSummary.low}
          icon={CheckCircle}
          color="bg-emerald-500"
          subtitle="≥80% adherence"
        />
        <StatCard
          title="Medium Risk Patients"
          value={riskSummary.medium}
          icon={Clock}
          color="bg-amber-500"
          subtitle="60-79% adherence"
        />
        <StatCard
          title="High Risk Patients"
          value={riskSummary.high}
          icon={AlertTriangle}
          color="bg-red-500"
          subtitle="<60% adherence"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Patients List */}
        <div className="xl:col-span-2">
          <Card variant="elevated">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <Users className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Patient Overview</h2>
                  <p className="text-sm text-gray-600">Monitor adherence across all patients</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {/* Sort Controls */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Sort by:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="risk">Risk Level</option>
                    <option value="adherence">Adherence</option>
                    <option value="name">Name</option>
                  </select>
                </div>
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search patients..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {filteredAndSortedPatients.map((patient) => {
                const riskConfig = getRiskConfig(patient.risk_level);
                return (
                  <div
                    key={patient.id}
                    onClick={() => fetchPatientDetails(patient)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 hover:shadow-md ${
                      selectedPatient?.id === patient.id
                        ? 'border-primary-300 bg-primary-50 shadow-md'
                        : 'border-gray-200 hover:border-primary-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${riskConfig.bg}`}>
                          {riskConfig.icon}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{patient.name}</h3>
                          <div className="flex items-center gap-4 mt-1">
                            <div className="flex items-center gap-2">
                              <Target className="w-4 h-4 text-gray-400" />
                              <span className={`text-sm font-medium ${getAdherenceColor(patient.adherence_score)}`}>
                                {patient.adherence_score.toFixed(1)}% adherence
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Zap className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-600">
                                {patient.current_streak} day streak
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${riskConfig.bg} ${riskConfig.color} border`}>
                          {riskConfig.icon}
                          <span>{riskConfig.label}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{riskConfig.description}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Patient Details Panel */}
        <div className="xl:col-span-1">
          <Card variant="elevated" className="sticky top-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Eye className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">Patient Details</h2>
                <p className="text-sm text-gray-500">
                  {selectedPatient ? `Viewing ${selectedPatient.name}` : 'Select a patient'}
                </p>
              </div>
            </div>

            {patientLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="text-center">
                  <Loader2 className="animate-spin text-blue-600 mx-auto mb-3" size={28} />
                  <p className="text-sm text-gray-500">Loading...</p>
                </div>
              </div>
            ) : selectedPatient && patientDashboard ? (
              <div className="space-y-5">
                {/* Patient Summary Header */}
                <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-4 border border-primary-100">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">
                        {selectedPatient.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{selectedPatient.name}</h3>
                      <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${getRiskConfig(selectedPatient.risk_level).bg} ${getRiskConfig(selectedPatient.risk_level).color} border`}>
                        {getRiskConfig(selectedPatient.risk_level).label}
                      </div>
                    </div>
                  </div>
                  
                  {/* Key Metrics Summary */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white/80 rounded-lg p-2.5 text-center">
                      <p className={`text-xl font-bold ${getAdherenceColor(patientDashboard.weekly_stats.adherence_score)}`}>
                        {Math.round(patientDashboard.weekly_stats.adherence_score)}%
                      </p>
                      <p className="text-xs text-gray-500">Adherence</p>
                    </div>
                    <div className="bg-white/80 rounded-lg p-2.5 text-center">
                      <p className="text-xl font-bold text-orange-600">
                        {patientDashboard.weekly_stats.current_streak}
                      </p>
                      <p className="text-xs text-gray-500">Day Streak</p>
                    </div>
                  </div>
                </div>

                {/* View Details Button */}
                <Button
                  onClick={() => navigate(`/admin/adherence/${selectedPatient.id}`)}
                  className="w-full bg-primary-600 hover:bg-primary-700"
                  rightIcon={<ExternalLink size={14} />}
                >
                  View Full Analysis
                </Button>

                {/* Mini Stats Grid */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-green-50 rounded-lg p-3 border border-green-100">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-green-600" />
                      <span className="text-xs text-green-700 font-medium">On-Time</span>
                    </div>
                    <p className="text-lg font-bold text-green-700 mt-1">
                      {Math.round(patientDashboard.weekly_stats.on_time_score)}%
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3 border border-purple-100">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-purple-600" />
                      <span className="text-xs text-purple-700 font-medium">Best Streak</span>
                    </div>
                    <p className="text-lg font-bold text-purple-700 mt-1">
                      {patientDashboard.weekly_stats.longest_streak} days
                    </p>
                  </div>
                </div>

                {/* 7-Day Trend - Compact */}
                {patientDashboard.chart_data && patientDashboard.chart_data.length > 0 && (
                  <AdherenceChart
                    data={patientDashboard.chart_data.slice(-7)}
                    title="7-Day Trend"
                    subtitle="Daily adherence"
                    variant="compact"
                  />
                )}

                {/* Recent Activity */}
                {patientDashboard.recent_logs && patientDashboard.recent_logs.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="w-4 h-4 text-gray-500" />
                      <h3 className="text-sm font-semibold text-gray-700">Recent Activity</h3>
                    </div>
                    <div className="space-y-2">
                      {patientDashboard.recent_logs.slice(0, 3).map((log) => {
                        const statusConfigs = {
                          taken: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Taken' },
                          skipped: { icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50', label: 'Skipped' },
                          missed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: 'Missed' },
                        };
                        const statusConfig = statusConfigs[log.status as keyof typeof statusConfigs] || {
                          icon: Clock, color: 'text-gray-600', bg: 'bg-gray-50', label: 'Unknown'
                        };
                        const StatusIcon = statusConfig.icon;

                        return (
                          <div key={log.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                            <div className={`p-1.5 rounded-lg ${statusConfig.bg}`}>
                              <StatusIcon className={`w-3.5 h-3.5 ${statusConfig.color}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-gray-500">
                                {new Date(log.scheduled_time).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                              </p>
                            </div>
                            <span className={`text-xs font-medium ${statusConfig.color}`}>
                              {statusConfig.label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <User className="w-10 h-10 text-gray-300 mb-3" />
                <p className="text-gray-500 text-sm mb-1">No patient selected</p>
                <p className="text-xs text-gray-400">Click on a patient to view details</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
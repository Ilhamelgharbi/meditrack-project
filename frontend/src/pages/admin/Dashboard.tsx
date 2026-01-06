// src/pages/admin/Dashboard.tsx
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatCard } from '../../components/common/StatCard';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import {
  Users, AlertTriangle, Pill, Activity, TrendingUp,
  RefreshCw, BarChart3, CheckCircle, XCircle, Clock,
  Target, ChevronRight, Zap
} from 'lucide-react';
import {
  XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';
import { patientsAPI } from '../../services/patient.service';
import { adherenceService, type MedicationLog } from '../../services/adherence.service';
import { medicationService } from '../../services/medications.service';

interface AdminDashboardData {
  total_patients: number;
  active_patients: number;
  critical_patients: number;
  under_observation: number;
  total_medications: number;
  active_prescriptions: number;
  pending_prescriptions: number;
  adherence_rate: number;
  doses_taken: number;
  doses_missed: number;
  doses_scheduled: number;
  recent_activities: Array<{
    id: number;
    type: 'taken' | 'skipped' | 'missed';
    medication: string;
    patient: string;
    timestamp: string;
  }>;
  adherence_trends: Array<{
    date: string;
    score: number;
    taken: number;
    missed: number;
  }>;
  top_patients: Array<{
    id: number;
    name: string;
    adherence: number;
    status: string;
  }>;
  low_adherence_patients: Array<{
    id: number;
    name: string;
    adherence: number;
    status: string;
  }>;
}

const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [patients, analyticsOverview, adherenceTrends, recentLogs, medications] = await Promise.all([
        patientsAPI.getAllPatients(),
        adherenceService.getAnalyticsOverview(),
        adherenceService.getAdherenceTrends(7),
        adherenceService.getLogs({ limit: 10 }),
        medicationService.getAllMedications('', 100).catch(() => [])
      ]);

      // Get patient adherence stats
      const patientAdherenceData = await Promise.all(
        patients.slice(0, 10).map(async (patient) => {
          try {
            const stats = await adherenceService.getPatientAdherenceStats(patient.user_id, 'weekly');
            return {
              id: patient.id,
              name: patient.user?.full_name || `Patient ${patient.id}`,
              adherence: stats.adherence_score || 0,
              status: patient.status
            };
          } catch {
            return {
              id: patient.id,
              name: patient.user?.full_name || `Patient ${patient.id}`,
              adherence: 0,
              status: patient.status
            };
          }
        })
      );

      // Sort by adherence
      const sortedByAdherence = [...patientAdherenceData].sort((a, b) => b.adherence - a.adherence);
      const topPatients = sortedByAdherence.slice(0, 5);
      const lowAdherencePatients = sortedByAdherence.filter(p => p.adherence < 70).slice(0, 5);

      // Transform recent logs
      const activities = recentLogs.slice(0, 8).map((log: MedicationLog, idx: number) => ({
        id: idx + 1,
        type: log.status as 'taken' | 'skipped' | 'missed',
        medication: log.medication_name || 'Medication',
        patient: `Patient #${log.patient_medication_id}`,
        timestamp: log.scheduled_time
      }));

      // Transform adherence trends with more data
      const trends = adherenceTrends.map(trend => ({
        date: trend.date,
        score: trend.adherence_rate || 0,
        taken: trend.doses_taken || 0,
        missed: (trend as any).doses_missed || 0
      }));

      const dashboardData: AdminDashboardData = {
        total_patients: patients.length,
        active_patients: patients.filter(p => p.status === 'stable').length,
        critical_patients: patients.filter(p => p.status === 'critical').length,
        under_observation: patients.filter(p => p.status === 'under_observation').length,
        total_medications: medications.length || 0,
        active_prescriptions: analyticsOverview.total_doses_scheduled || 0,
        pending_prescriptions: 0,
        adherence_rate: Math.round(analyticsOverview.average_adherence_rate || 0),
        doses_taken: analyticsOverview.total_doses_taken || 0,
        doses_missed: analyticsOverview.total_doses_missed || 0,
        doses_scheduled: analyticsOverview.total_doses_scheduled || 0,
        recent_activities: activities,
        adherence_trends: trends,
        top_patients: topPatients,
        low_adherence_patients: lowAdherencePatients,
      };

      setDashboard(dashboardData);
    } catch (err: unknown) {
      console.error('Error fetching dashboard data:', err);
      const message = err instanceof Error ? err.message : 'Failed to load dashboard';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user, fetchDashboardData]);

  if (loading) {
    return <DashboardLoadingModal />;
  }

  if (error) {
    return <DashboardErrorModal error={error} onRetry={fetchDashboardData} />;
  }

  const getStatusIcon = (type: string) => {
    switch (type) {
      case 'taken': return <CheckCircle size={14} className="text-green-500" />;
      case 'skipped': return <Clock size={14} className="text-yellow-500" />;
      case 'missed': return <XCircle size={14} className="text-red-500" />;
      default: return <Activity size={14} className="text-gray-400" />;
    }
  };

  const getAdherenceColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAdherenceBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  // Pie chart data for doses
  const dosesPieData = [
    { name: 'Taken', value: dashboard?.doses_taken || 0, color: '#22c55e' },
    { name: 'Missed', value: dashboard?.doses_missed || 0, color: '#ef4444' },
  ];

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome back, Dr. {user?.full_name?.split(' ')[0]}
          </h1>
          <p className="text-slate-500 mt-1">Here's an overview of your patients and their medication adherence</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right text-sm text-slate-500">
            <p>Last updated</p>
            <p className="font-medium text-slate-700">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            leftIcon={<RefreshCw size={14} />}
            onClick={fetchDashboardData}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div onClick={() => navigate('/admin/patients')} className="cursor-pointer">
          <StatCard
            title="Total Patients"
            value={dashboard?.total_patients || 0}
            icon={Users}
            color="bg-blue-500"
            subtitle="Registered in system"
          />
        </div>

        <div onClick={() => navigate('/admin/medications')} className="cursor-pointer">
          <StatCard
            title="Total Medications"
            value={dashboard?.total_medications || 0}
            icon={Pill}
            color="bg-teal-500"
            subtitle="In database"
          />
        </div>

        <div onClick={() => navigate('/admin/adherence')} className="cursor-pointer">
          <StatCard
            title="Avg. Adherence"
            value={`${dashboard?.adherence_rate || 0}%`}
            icon={TrendingUp}
            color="bg-purple-500"
            subtitle={(dashboard?.adherence_rate || 0) >= 80 ? "Excellent" : "Needs improvement"}
          />
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Adherence Trends Chart */}
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Adherence Trends</h3>
              <p className="text-sm text-slate-500">7-day medication compliance overview</p>
            </div>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate('/admin/adherence')}
              className="text-blue-600 hover:text-blue-700"
            >
              View Details <ChevronRight size={14} className="ml-1" />
            </Button>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dashboard?.adherence_trends || []}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { weekday: 'short' })}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                  labelFormatter={(value) => new Date(value).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                  formatter={(value, name) => [
                    name === 'score' ? `${value}%` : value,
                    name === 'score' ? 'Adherence Rate' : name === 'taken' ? 'Doses Taken' : 'Doses Missed'
                  ]}
                />
                <Area 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  fill="url(#colorScore)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Doses Breakdown Pie Chart */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Doses Overview</h3>
              <p className="text-sm text-slate-500">Taken vs Missed</p>
            </div>
            <Target size={20} className="text-slate-400" />
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={dosesPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {dosesPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name) => [`${value} doses`, name]}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 mt-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm text-slate-600">Taken ({dashboard?.doses_taken || 0})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-sm text-slate-600">Missed ({dashboard?.doses_missed || 0})</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Patients & Activity Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Performing Patients */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <Zap className="text-green-600" size={16} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900">Top Adherence</h3>
                <p className="text-xs text-slate-500">Best performing patients</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            {dashboard?.top_patients.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-4">No patient data available</p>
            ) : (
              dashboard?.top_patients.map((patient, idx) => (
                <div 
                  key={patient.id}
                  onClick={() => navigate(`/admin/patients/${patient.id}`)}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-green-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{patient.name}</p>
                      <p className="text-xs text-slate-500 capitalize">{patient.status}</p>
                    </div>
                  </div>
                  <span className={`text-sm font-bold ${getAdherenceColor(patient.adherence)}`}>
                    {Math.round(patient.adherence)}%
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Low Adherence Patients (Needs Attention) */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="text-red-600" size={16} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900">Needs Attention</h3>
                <p className="text-xs text-slate-500">Low adherence patients</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            {dashboard?.low_adherence_patients.length === 0 ? (
              <div className="text-center py-4">
                <CheckCircle size={24} className="text-green-500 mx-auto mb-2" />
                <p className="text-sm text-green-600">All patients on track!</p>
              </div>
            ) : (
              dashboard?.low_adherence_patients.map((patient) => (
                <div 
                  key={patient.id}
                  onClick={() => navigate(`/admin/patients/${patient.id}`)}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-red-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${getAdherenceBg(patient.adherence).replace('bg-', 'bg-')}`} style={{ backgroundColor: patient.adherence < 60 ? '#ef4444' : '#f59e0b' }}></div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{patient.name}</p>
                      <p className="text-xs text-slate-500 capitalize">{patient.status}</p>
                    </div>
                  </div>
                  <span className={`text-sm font-bold ${getAdherenceColor(patient.adherence)}`}>
                    {Math.round(patient.adherence)}%
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Recent Activity */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Activity className="text-blue-600" size={16} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900">Recent Activity</h3>
                <p className="text-xs text-slate-500">Latest medication logs</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate('/admin/adherence')}
              className="text-blue-600 hover:text-blue-700 text-xs"
            >
              View All
            </Button>
          </div>
          <div className="space-y-2">
            {dashboard?.recent_activities.length === 0 ? (
              <div className="text-center py-4 text-slate-400">
                <Activity size={24} className="mx-auto mb-2" />
                <p className="text-sm">No recent activity</p>
              </div>
            ) : (
              dashboard?.recent_activities.slice(0, 6).map((activity) => (
                <div 
                  key={activity.id} 
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  {getStatusIcon(activity.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{activity.medication}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(activity.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    activity.type === 'taken' ? 'bg-green-100 text-green-700' :
                    activity.type === 'skipped' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {activity.type}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={18} className="text-blue-600" />
          <h3 className="text-lg font-semibold text-slate-900">Quick Actions</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <button 
            onClick={() => navigate('/admin/patients')}
            className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-xl hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-all group"
          >
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <Users className="text-blue-600" size={20} />
            </div>
            <span className="text-sm font-medium text-slate-700 group-hover:text-blue-700">Patients</span>
          </button>
          <button 
            onClick={() => navigate('/admin/medications')}
            className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-xl hover:bg-teal-50 hover:border-teal-200 border border-transparent transition-all group"
          >
            <div className="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center group-hover:bg-teal-200 transition-colors">
              <Pill className="text-teal-600" size={20} />
            </div>
            <span className="text-sm font-medium text-slate-700 group-hover:text-teal-700">Medications</span>
          </button>
          <button 
            onClick={() => navigate('/admin/adherence')}
            className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-xl hover:bg-purple-50 hover:border-purple-200 border border-transparent transition-all group"
          >
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <TrendingUp className="text-purple-600" size={20} />
            </div>
            <span className="text-sm font-medium text-slate-700 group-hover:text-purple-700">Adherence</span>
          </button>
          <button 
            onClick={() => navigate('/admin/analytics')}
            className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-xl hover:bg-orange-50 hover:border-orange-200 border border-transparent transition-all group"
          >
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center group-hover:bg-orange-200 transition-colors">
              <BarChart3 className="text-orange-600" size={20} />
            </div>
            <span className="text-sm font-medium text-slate-700 group-hover:text-orange-700">Analytics</span>
          </button>
          <button 
            onClick={() => navigate('/admin/assistant')}
            className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-xl hover:bg-green-50 hover:border-green-200 border border-transparent transition-all group"
          >
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
              <Activity className="text-green-600" size={20} />
            </div>
            <span className="text-sm font-medium text-slate-700 group-hover:text-green-700">AI Assistant</span>
          </button>
        </div>
      </Card>
    </div>
  );
};

export default AdminDashboard;

// src/pages/patient/Dashboard.tsx
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { DashboardLoadingModal, DashboardErrorModal, StatCard } from '../../components/common';
import {
  Pill, Clock, CheckCircle, Target, Zap
} from 'lucide-react';
import {
  XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line
} from 'recharts';
import { medicationService } from '../../services/medications.service';
import type { PatientMedicationDetailed } from '../../types/medications.types';
import type { AdherenceDashboard } from '../../services/adherence.service';
import { adherenceService } from '../../services/adherence.service';

export const PatientDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [medications, setMedications] = useState<PatientMedicationDetailed[]>([]);
  const [dashboard, setDashboard] = useState<AdherenceDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  const [medicationStats, setMedicationStats] = useState<any[]>([]);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const patientId = user!.id;
      const medicationData = await medicationService.getPatientMedications(patientId, {
        limit: 100,
        include_inactive: true
      });

      setMedications(medicationData);

      // Fetch real adherence dashboard data
      const dashboardData = await adherenceService.getDashboard();
      setDashboard(dashboardData);

      // Fetch medication-specific stats for active medications
      const activeMeds = medicationData.filter(m => m.status === 'active');
      const medStats = [];
      for (const medication of activeMeds.slice(0, 5)) { // Limit to 5 for dashboard
        try {
          const stats = await adherenceService.getStats('weekly', medication.id);
          medStats.push({
            medication: medication,
            stats: stats
          });
        } catch (err) {
          console.warn(`Could not fetch stats for medication ${medication.id}:`, err);
        }
      }
      setMedicationStats(medStats);
    } catch (err: unknown) {
      console.error('Error fetching dashboard data:', err);
      const message = err instanceof Error ? err.message : 'Failed to load dashboard';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user, fetchDashboardData]);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Needs Work';
  };

  if (loading) {
    return <DashboardLoadingModal />;
  }

  if (error) {
    return <DashboardErrorModal error={error} onRetry={fetchDashboardData} />;
  }

  const adherenceScore = dashboard?.weekly_stats.adherence_score || 0;
  const activeMeds = medications.filter(m => m.status === 'active').length;

  // Calculate overall adherence stats
  const totalDoses = dashboard?.weekly_stats.total_scheduled || 0;
  const takenDoses = dashboard?.weekly_stats.total_taken || 0;
  const onTimeRate = dashboard?.weekly_stats.on_time_score || 0;

  // Stats for the overview - include adherence metrics
  const stats = [
    { title: 'Active Meds', value: activeMeds.toString(), icon: CheckCircle, color: 'bg-emerald-500', subtitle: 'currently taking' },
    { title: 'Weekly Adherence', value: `${adherenceScore.toFixed(0)}%`, icon: Target, color: 'bg-blue-500', subtitle: `${takenDoses}/${totalDoses} doses taken` },
    { title: 'Current Streak', value: `${dashboard?.weekly_stats.current_streak || 0}`, icon: Zap, color: 'bg-purple-500', subtitle: 'days in a row' },
    { title: 'On-Time Rate', value: `${onTimeRate.toFixed(0)}%`, icon: Clock, color: 'bg-green-500', subtitle: 'taken on schedule' },
  ];

  // Active medications for preview
  const activeMedications = medications
    .filter(m => m.status === 'active')
    .map(m => {
      // Calculate today's taken doses from recent logs
      const today = new Date().toDateString();
      const todayLogs = dashboard?.recent_logs.filter(log =>
        log.patient_medication_id === m.id &&
        new Date(log.scheduled_time).toDateString() === today &&
        log.status === 'taken'
      ) || [];
      const todayTaken = todayLogs.length;

      return {
        id: m.id,
        medicationName: m.medication?.name || 'Unknown Medication',
        dosage: m.dosage,
        frequency: `${m.times_per_day}x daily`,
        todayTaken: todayTaken,
        todayScheduled: m.times_per_day,
      };
    });

  // Weekly data for trends chart
  const weeklyData = dashboard?.chart_data.map(item => ({
    day: new Date(item.date).toLocaleDateString('en-US', { weekday: 'short' }),
    adherence: item.score
  })) || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back, {user?.full_name?.split(' ')[0]}!
        </h1>
        <p className="text-slate-500 mt-1">Here's your medication overview for today</p>
      </div>

      {/* VIEW: DASHBOARD OVERVIEW */}
      <div className="space-y-6 animate-fadeIn">
         {/* Statistics Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat, idx) => (
            <StatCard
              key={idx}
              title={stat.title}
              value={stat.value}
              icon={stat.icon}
              color={stat.color}
              subtitle={stat.subtitle}
            />
          ))}
        </div>

        {/* Next Dose Reminder */}
        <Card className="bg-gradient-to-r from-emerald-50 to-blue-50 border-emerald-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-emerald-500 p-3 rounded-lg">
                <Clock className="text-white" size={24} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Next Dose Reminder</h3>
                <p className="text-sm text-slate-600">
                  No upcoming doses scheduled
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Active Medications Preview */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Active Medications</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/patient/medications')}
              className="text-slate-600 hover:text-slate-900"
            >
              View All
            </Button>
          </div>
          <div className="space-y-3">
            {activeMedications.slice(0, 3).map((med) => (
              <div key={med.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <Pill className="text-blue-600" size={16} />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">{med.medicationName}</p>
                    <p className="text-sm text-slate-600">{med.dosage} • {med.frequency}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">
                    {med.todayTaken}/{med.todayScheduled}
                  </p>
                  <p className="text-xs text-slate-500">today</p>
                </div>
              </div>
            ))}
            {activeMedications.length === 0 && (
              <p className="text-center text-slate-500 py-4">No active medications</p>
            )}
          </div>
        </Card>

        {/* Adherence Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Adherence Score */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Adherence Score</h3>
              <span className={`text-sm font-medium ${getScoreColor(adherenceScore)}`}>
                {getScoreLabel(adherenceScore)}
              </span>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">This Week</span>
                <span className="font-semibold text-slate-900">{adherenceScore.toFixed(0)}%</span>
              </div>
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Current Streak</span>
                <span>{dashboard?.weekly_stats.current_streak || 0} days</span>
              </div>
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Best Streak</span>
                <span>{dashboard?.weekly_stats.longest_streak || 0} days</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-300 ${getScoreColor(adherenceScore).replace('text-', 'bg-')}`}
                  style={{ width: `${adherenceScore}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
          </Card>

          {/* Weekly Trends */}
          <Card>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Weekly Trends</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={weeklyData}>
                  <XAxis
                    dataKey="day"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                  />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="adherence"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, stroke: '#10b981', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Medication Adherence Overview */}
        {medicationStats.length > 0 && (
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Medication Adherence</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/patient/adherence')}
                className="text-slate-600 hover:text-slate-900"
              >
                View Details
              </Button>
            </div>
            <div className="space-y-3">
              {medicationStats.map(({ medication, stats }) => (
                <div key={medication.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <Pill className="text-blue-600" size={16} />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{medication.medication?.name}</p>
                      <p className="text-sm text-slate-600">{medication.dosage}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-bold ${getScoreColor(stats.adherence_score)}`}>
                      {stats.adherence_score.toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-500">
                      {stats.total_taken}/{stats.total_scheduled}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
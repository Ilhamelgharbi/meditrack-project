import { useState, useEffect } from 'react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { DashboardLoadingModal } from '../../components/common';
import {
  BarChart3, TrendingUp, Users, Pill, Activity,
  CheckCircle, Target, Zap,
  ArrowUp, ArrowDown, Minus, Filter, Download
} from 'lucide-react';
import { adherenceService } from '../../services/adherence.service';
import type { AnalyticsOverview, AdherenceTrend } from '../../services/adherence.service';

interface PatientSummary {
  patient_id: number;
  patient_name: string;
  adherence_rate: number;
  total_medications: number;
}

export const AdminAnalyticsDashboard = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AdherenceTrend[]>([]);
  const [topPatients, setTopPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedPeriod]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);

      // Calculate date range based on selected period
      const endDate = new Date();
      const startDate = new Date();
      switch (selectedPeriod) {
        case '7d':
          startDate.setDate(endDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(endDate.getDate() - 30);
          break;
        case '90d':
          startDate.setDate(endDate.getDate() - 90);
          break;
      }

      // Fetch analytics data using service methods
      const [dashboardData, trendsData, patientsData] = await Promise.all([
        adherenceService.getAnalyticsOverview(
          startDate.toISOString().split('T')[0],
          endDate.toISOString().split('T')[0]
        ),
        adherenceService.getAdherenceTrends(selectedPeriod === '7d' ? 7 : selectedPeriod === '30d' ? 30 : 90),
        adherenceService.getPatientAdherenceSummaries(30)
      ]);

      // The overview is returned directly, not wrapped in an object
      setOverview(dashboardData);
      setTrends(trendsData);
      setTopPatients(patientsData.slice(0, 5));

    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAdherenceColor = (rate: number) => {
    if (rate >= 90) return 'text-secondary-600';
    if (rate >= 75) return 'text-primary-600';
    if (rate >= 60) return 'text-warning';
    return 'text-error';
  };

  const getAdherenceBgColor = (rate: number) => {
    if (rate >= 90) return 'bg-secondary-50 border-secondary-200';
    if (rate >= 75) return 'bg-primary-50 border-primary-200';
    if (rate >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getTrendIcon = (current: number, previous?: number) => {
    if (!previous) return <Minus className="w-4 h-4 text-gray-400" />;
    if (current > previous) return <ArrowUp className="w-4 h-4 text-green-600" />;
    if (current < previous) return <ArrowDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  if (loading) {
    return <DashboardLoadingModal title="Analytics Dashboard" subtitle="Loading analytics data..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analytics Dashboard</h1>
          <p className="text-slate-500 mt-1">Comprehensive insights into medication adherence and patient management</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
          <Button variant="outline" leftIcon={<Download size={16} />}>
            Export Report
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card variant="elevated" className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-bl-3xl opacity-50"></div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-blue-100`}>
                  <Users className="w-5 h-5 text-blue-600" />
                </div>
                {getTrendIcon(overview.total_patients)}
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">Total Patients</p>
                <h3 className="text-3xl font-bold text-blue-600">{overview.total_patients}</h3>
                <p className="text-xs text-gray-500">Active patients in system</p>
              </div>
            </div>
          </Card>

          <Card variant="elevated" className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-green-100 to-green-200 rounded-bl-3xl opacity-50"></div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-green-100`}>
                  <Pill className="w-5 h-5 text-green-600" />
                </div>
                {getTrendIcon(overview.total_doses_scheduled)}
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">Doses Scheduled</p>
                <h3 className="text-3xl font-bold text-green-600">{overview.total_doses_scheduled}</h3>
                <p className="text-xs text-gray-500">In selected period</p>
              </div>
            </div>
          </Card>

          <Card variant="elevated" className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-purple-100 to-purple-200 rounded-bl-3xl opacity-50"></div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl ${getAdherenceBgColor(overview.average_adherence_rate)}`}>
                  <Target className="w-5 h-5 text-purple-600" />
                </div>
                {getTrendIcon(overview.average_adherence_rate)}
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">Avg Adherence</p>
                <h3 className={`text-3xl font-bold ${getAdherenceColor(overview.average_adherence_rate)}`}>
                  {overview.average_adherence_rate.toFixed(1)}%
                </h3>
                <p className="text-xs text-gray-500">Across all patients</p>
              </div>
            </div>
          </Card>

          <Card variant="elevated" className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-orange-100 to-orange-200 rounded-bl-3xl opacity-50"></div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-orange-100`}>
                  <Activity className="w-5 h-5 text-orange-600" />
                </div>
                {getTrendIcon(overview.total_doses_taken)}
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">Doses Taken</p>
                <h3 className="text-3xl font-bold text-orange-600">{overview.total_doses_taken}</h3>
                <p className="text-xs text-gray-500">Successfully completed</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Adherence Trends Chart */}
        <Card>
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-5 h-5 text-indigo-600" />
            <h2 className="text-xl font-bold text-gray-900">Adherence Trends</h2>
          </div>

          {trends.length > 0 ? (
            <div className="space-y-4">
              {trends.slice(-14).map((trend, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-20 text-sm font-medium text-gray-600">
                    {new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-1000 ${
                            trend.adherence_rate >= 90 ? 'bg-secondary-500' :
                            trend.adherence_rate >= 75 ? 'bg-primary-500' :
                            trend.adherence_rate >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${trend.adherence_rate}%` }}
                        ></div>
                      </div>
                      <div className="w-16 text-right">
                        <span className={`text-sm font-bold ${getAdherenceColor(trend.adherence_rate)}`}>
                          {trend.adherence_rate.toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-20 text-xs text-gray-500 text-right">
                        {trend.doses_taken}/{trend.doses_scheduled}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-center">
              <div>
                <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No trend data available</p>
              </div>
            </div>
          )}
        </Card>

        {/* Top Performing Patients */}
        <Card>
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h2 className="text-xl font-bold text-gray-900">Top Performing Patients</h2>
          </div>

          {topPatients.length > 0 ? (
            <div className="space-y-4">
              {topPatients.map((patient, index) => (
                <div key={patient.patient_id} className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-center w-8 h-8 bg-primary-100 rounded-full">
                    <span className="text-sm font-bold text-primary-600">#{index + 1}</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{patient.patient_name}</h3>
                    <p className="text-sm text-gray-600">{patient.total_medications} medications</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${getAdherenceColor(patient.adherence_rate)}`}>
                      {patient.adherence_rate.toFixed(1)}%
                    </div>
                    <p className="text-xs text-gray-500">adherence</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-center">
              <div>
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No patient data available</p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <Zap className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-gray-900">Quick Actions</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            variant="outline"
            className="h-20 flex-col gap-2"
            onClick={() => window.open('/analytics/adherence', '_blank')}
          >
            <BarChart3 size={20} />
            <span>Detailed Adherence Report</span>
          </Button>

          <Button
            variant="outline"
            className="h-20 flex-col gap-2"
            onClick={() => window.open('/analytics/patients', '_blank')}
          >
            <Users size={20} />
            <span>Patient Demographics</span>
          </Button>

          <Button
            variant="outline"
            className="h-20 flex-col gap-2"
            onClick={() => window.open('/analytics/medications', '_blank')}
          >
            <Pill size={20} />
            <span>Medication Analytics</span>
          </Button>
        </div>
      </Card>
    </div>
  );
};
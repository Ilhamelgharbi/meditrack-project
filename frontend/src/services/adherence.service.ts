// src/services/adherence.service.ts
import api from './api';
import { getUserTimezone, localTimeToUTC } from '../utils/timezone';

export interface MedicationLog {
  id: number;
  patient_medication_id: number;
  patient_id: number;
  scheduled_time: string; // ISO string with timezone
  scheduled_date: string; // ISO date string
  status: string;
  actual_time?: string; // ISO string with timezone
  on_time: boolean;
  minutes_late?: number;
  notes?: string;
  skipped_reason?: string;
  logged_via: string;
  reminder_id?: number;
  created_at: string; // ISO string with timezone
  updated_at?: string; // ISO string with timezone
  medication_name?: string;
  dosage?: string;
  medication_form?: string;
  user_timezone?: string; // User's timezone for display
}

export interface AdherenceStats {
  id: number;
  patient_id: number;
  patient_medication_id?: number;
  period_type: string;
  period_start: string; // ISO date string
  period_end: string; // ISO date string
  total_scheduled: number;
  total_taken: number;
  total_skipped: number;
  total_missed: number;
  adherence_score: number;
  on_time_score: number;
  current_streak: number;
  longest_streak: number;
  calculated_at: string; // ISO string with timezone
  user_timezone?: string; // User's timezone for display
}

export interface AdherenceChartData {
  date: string; // ISO date string
  score: number;
  taken: number;
  scheduled: number;
  skipped?: number;
  missed?: number;
  status: string;
  user_timezone?: string; // User's timezone for display
}

export interface AdherenceDashboard {
  overall_stats: AdherenceStats;
  weekly_stats: AdherenceStats;
  daily_stats: AdherenceStats;
  chart_data: AdherenceChartData[];
  recent_logs: MedicationLog[];
  user_timezone?: string; // User's timezone for display
}

export interface AnalyticsOverview {
  total_patients: number;
  patients_with_logs: number;
  average_adherence_rate: number;
  adherence_distribution: { [key: string]: number };
  total_doses_scheduled: number;
  total_doses_taken: number;
  total_doses_missed: number;
  total_doses_skipped: number;
  period_start: string;
  period_end: string;
}

export interface AdherenceTrend {
  date: string;
  adherence_rate: number;
  doses_scheduled: number;
  doses_taken: number;
}

export interface PatientAdherenceSummary {
  patient_id: number;
  patient_name: string;
  adherence_rate: number;
  total_medications: number;
}

export interface MedicationAdherenceDetail {
  medication_id: number;
  medication_name: string;
  adherence_rate: number;
  total_patients: number;
  total_doses: number;
  doses_taken: number;
}

export interface PatientDemographics {
  total_patients: number;
  age_distribution: { [key: string]: number };
  gender_distribution: { [key: string]: number };
  average_age: number;
}

export interface MedicationUsageStats {
  medication_id: number;
  medication_name: string;
  total_patients: number;
  total_prescriptions: number;
  average_adherence: number;
  usage_trend: { date: string; count: number }[];
}

export const adherenceService = {
  // Get adherence stats for current patient
  getStats: async (
    period: 'daily' | 'weekly' | 'monthly' | 'overall' = 'weekly',
    patientMedicationId?: number
  ): Promise<AdherenceStats> => {
    const params = new URLSearchParams({ period });
    if (patientMedicationId) {
      params.append('patient_medication_id', patientMedicationId.toString());
    }
    const response = await api.get<AdherenceStats>(`/adherence/stats/?${params}`);
    return response.data;
  },

  // Get chart data for visualization
  getChartData: async (days: number = 7): Promise<AdherenceChartData[]> => {
    const response = await api.get<AdherenceChartData[]>(`/adherence/chart/?days=${days}`);
    return response.data;
  },

  // Get complete dashboard data
  getDashboard: async (): Promise<AdherenceDashboard> => {
    const response = await api.get<AdherenceDashboard>('/adherence/dashboard/');
    return response.data;
  },

  // Log a medication dose
  logDose: async (data: {
    patient_medication_id: number;
    scheduled_time: string; // Local time string like "08:00"
    status: 'taken' | 'skipped' | 'missed';
    actual_time?: string; // Local time string like "08:15"
    notes?: string;
    skipped_reason?: string;
  }): Promise<MedicationLog> => {
    // Convert local times to UTC for backend storage
    const userTimezone = getUserTimezone();
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

    const requestData = {
      patient_medication_id: data.patient_medication_id,
      scheduled_time: data.scheduled_time.includes('T')
        ? data.scheduled_time // Already ISO string
        : localTimeToUTC(data.scheduled_time, today, userTimezone).toISOString(),
      status: data.status,
      actual_time: data.actual_time && data.actual_time.includes('T')
        ? data.actual_time // Already ISO string
        : (data.actual_time ? localTimeToUTC(data.actual_time, today, userTimezone).toISOString() : undefined),
      notes: data.notes,
      skipped_reason: data.skipped_reason,
      user_timezone: userTimezone // Include user's timezone for backend reference
    };

    const response = await api.post<MedicationLog>('/adherence/logs', requestData);
    return response.data;
  },

  // Update existing log
  updateLog: async (
    logId: number,
    data: {
      status?: 'taken' | 'skipped' | 'missed';
      actual_time?: string;
      notes?: string;
      skipped_reason?: string;
    }
  ): Promise<MedicationLog> => {
    const response = await api.put<MedicationLog>(`/adherence/logs/${logId}`, data);
    return response.data;
  },

  // Get medication logs
  getLogs: async (params?: {
    patient_medication_id?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<MedicationLog[]> => {
    const query = new URLSearchParams();
    if (params?.patient_medication_id) query.append('patient_medication_id', params.patient_medication_id.toString());
    if (params?.status) query.append('status', params.status);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.skip) query.append('skip', params.skip.toString());
    if (params?.limit) query.append('limit', params.limit.toString());

    const response = await api.get<MedicationLog[]>(`/adherence/logs?${query}`);
    return response.data;
  },

  // Delete medication log
  deleteLog: async (logId: number): Promise<void> => {
    await api.delete(`/adherence/logs/${logId}`);
  },

  // Get adherence stats for a specific patient (admin only)
  getPatientAdherenceStats: async (
    patientId: number,
    period: 'daily' | 'weekly' | 'monthly' | 'overall' = 'weekly',
    patientMedicationId?: number
  ): Promise<AdherenceStats> => {
    const query = new URLSearchParams();
    query.append('period', period);
    if (patientMedicationId) {
      query.append('patient_medication_id', patientMedicationId.toString());
    }
    const response = await api.get<AdherenceStats>(`/adherence/patients/${patientId}/stats?${query}`);
    return response.data;
  },

  // Get patient dashboard (admin only)
  getPatientDashboard: async (patientId: number): Promise<AdherenceDashboard> => {
    const response = await api.get<AdherenceDashboard>(`/adherence/patients/${patientId}/dashboard`);
    return response.data;
  },

  // Get patient logs (admin only)
  getPatientLogs: async (
    patientId: number,
    params?: {
      patient_medication_id?: number;
      status?: string;
      start_date?: string;
      end_date?: string;
      skip?: number;
      limit?: number;
    }
  ): Promise<MedicationLog[]> => {
    const query = new URLSearchParams();
    if (params?.patient_medication_id) query.append('patient_medication_id', params.patient_medication_id.toString());
    if (params?.status) query.append('status', params.status);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.skip) query.append('skip', params.skip.toString());
    if (params?.limit) query.append('limit', params.limit.toString());

    const response = await api.get<MedicationLog[]>(`/adherence/patients/${patientId}/logs?${query}`);
    return response.data;
  },

  // Analytics methods
  getAnalyticsOverview: async (startDate?: string, endDate?: string): Promise<AnalyticsOverview> => {
    const query = new URLSearchParams();
    if (startDate) query.append('start_date', startDate);
    if (endDate) query.append('end_date', endDate);
    const response = await api.get<AnalyticsOverview>(`/analytics/adherence/overview?${query}`);
    return response.data;
  },

  getAdherenceTrends: async (days: number = 30): Promise<AdherenceTrend[]> => {
    const response = await api.get<AdherenceTrend[]>(`/analytics/adherence/trends?days=${days}`);
    return response.data;
  },

  getPatientAdherenceSummaries: async (days: number = 30): Promise<PatientAdherenceSummary[]> => {
    const response = await api.get<PatientAdherenceSummary[]>(`/analytics/adherence/patients?days=${days}`);
    return response.data;
  },

  getMedicationAdherenceDetails: async (days: number = 30): Promise<MedicationAdherenceDetail[]> => {
    const response = await api.get<MedicationAdherenceDetail[]>(`/analytics/adherence/medications?days=${days}`);
    return response.data;
  },

  getPatientDemographics: async (): Promise<PatientDemographics> => {
    const response = await api.get<PatientDemographics>('/analytics/patients/demographics');
    return response.data;
  },

  getMedicationUsageStats: async (): Promise<MedicationUsageStats[]> => {
    const response = await api.get<MedicationUsageStats[]>('/analytics/medications/usage-stats');
    return response.data;
  },
};
// src/types/adherence.types.ts
export interface AdherenceStats {
  id: number;
  patient_id: number;
  patient_medication_id?: number;
  period_type: string;
  period_start: string;
  period_end: string;
  total_scheduled: number;
  total_taken: number;
  total_skipped: number;
  total_missed: number;
  adherence_score: number;
  on_time_score: number;
  current_streak: number;
  longest_streak: number;
  calculated_at: string;
}

export interface AdherenceChartData {
  date: string;
  score: number;
  taken: number;
  scheduled: number;
  status: string;
}

export interface MedicationLog {
  id: number;
  patient_medication_id: number;
  patient_id: number;
  scheduled_time: string;
  scheduled_date: string;
  status: 'taken' | 'skipped' | 'missed';
  actual_time?: string;
  on_time: boolean;
  minutes_late?: number;
  notes?: string;
  skipped_reason?: string;
  logged_via: string;
  reminder_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface AdherenceDashboard {
  overall_stats: AdherenceStats;
  weekly_stats: AdherenceStats;
  daily_stats: AdherenceStats;
  chart_data: AdherenceChartData[];
  recent_logs: MedicationLog[];
}
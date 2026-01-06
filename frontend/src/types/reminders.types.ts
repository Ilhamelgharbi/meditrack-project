// src/types/reminders.types.ts
export const ReminderFrequency = {
  once: "once",
  daily: "daily",
  twice_daily: "twice_daily",
  three_times_daily: "three_times_daily",
  custom: "custom"
} as const;

export type ReminderFrequencyType = typeof ReminderFrequency[keyof typeof ReminderFrequency];

export const ReminderChannel = {
  push: "push",
  email: "email",
  sms: "sms",
  whatsapp: "whatsapp",
  all: "all"
} as const;

export type ReminderChannelType = typeof ReminderChannel[keyof typeof ReminderChannel];

export const ReminderStatus = {
  pending: "pending",
  sent: "sent",
  delivered: "delivered",
  read: "read",
  responded: "responded",
  failed: "failed",
  cancelled: "cancelled"
} as const;

export type ReminderStatusType = typeof ReminderStatus[keyof typeof ReminderStatus];

// Reminder Schedule Types
export interface ReminderScheduleCreate {
  patient_medication_id: number;
  frequency?: ReminderFrequencyType;
  reminder_times: string[]; // ["08:00", "20:00"]
  advance_minutes?: number;
  channel_whatsapp?: boolean;
  channel_sms?: boolean;
  channel_push?: boolean;
  channel_email?: boolean;
  auto_skip_if_taken?: boolean;
  escalate_if_missed?: boolean;
  escalate_delay_minutes?: number;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: string; // "HH:MM"
  quiet_hours_end?: string; // "HH:MM"
  start_date: string; // ISO date string
  end_date?: string; // ISO date string
}

export interface ReminderScheduleUpdate {
  is_active?: boolean;
  frequency?: ReminderFrequencyType;
  reminder_times?: string[];
  advance_minutes?: number;
  channel_whatsapp?: boolean;
  channel_sms?: boolean;
  channel_push?: boolean;
  channel_email?: boolean;
  auto_skip_if_taken?: boolean;
  escalate_if_missed?: boolean;
  escalate_delay_minutes?: number;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  end_date?: string;
}

export interface PatientMedicationInfo {
  id: number;
  medication_id: number;
  dosage: string;
  instructions?: string;
  times_per_day: number;
  start_date: string;
  end_date?: string;
  status: string;
  confirmed_by_patient: boolean;
  medication?: {
    id: number;
    name: string;
    form: string;
  };
}

export interface ReminderScheduleResponse {
  id: number;
  patient_medication_id: number;
  patient_id: number;
  is_active: boolean;
  frequency: ReminderFrequencyType;
  reminder_times: string[];
  advance_minutes: number;
  channel_whatsapp: boolean;
  channel_sms: boolean;
  channel_push: boolean;
  channel_email: boolean;
  auto_skip_if_taken: boolean;
  escalate_if_missed: boolean;
  escalate_delay_minutes: number;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  start_date: string;
  end_date?: string;
  created_at: string;
  updated_at?: string;
  patient_medication?: PatientMedicationInfo;
}

export interface ReminderScheduleDetailed extends ReminderScheduleResponse {
  medication_name: string;
  medication_dosage: string;
  medication_form: string;
}

// Reminder Instance Types
export interface ReminderResponse {
  id: number;
  patient_medication_id: number;
  patient_id: number;
  scheduled_time: string;
  actual_dose_time: string;
  reminder_advance_minutes: number;
  channel: ReminderChannelType;
  status: ReminderStatusType;
  twilio_message_sid?: string;
  twilio_status?: string;
  message_text: string;
  response_text?: string;
  response_received_at?: string;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  retry_count: number;
  created_at: string;
}

export interface ReminderCancel {
  reason?: string;
}

// API Response Types
export interface ReminderScheduleToggleResponse {
  message: string;
  is_active: boolean;
}

export interface ReminderGenerationResponse {
  message: string;
  count: number;
  reminders: ReminderResponse[];
}

// Stats Types
export interface ReminderStats {
  total_scheduled: number;
  sent: number;
  delivered: number;
  responded: number;
  failed: number;
  delivery_rate: number;
  response_rate: number;
}

// Filter Types
export interface ReminderFilters {
  status?: ReminderStatusType;
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface ReminderScheduleFilters {
  active_only?: boolean;
  medication_id?: number;
}

// UI-specific types for better UX
export interface TodayReminder {
  id: number;
  medication_name: string;
  dosage: string;
  scheduled_time: string;
  status: ReminderStatusType;
  channel: ReminderChannelType;
  advance_minutes: number;
  instructions?: string;
  is_overdue: boolean;
  time_until: string; // "in 2 hours", "30 min ago", etc.
}

export interface UpcomingReminder {
  id: number;
  medication_name: string;
  dosage: string;
  scheduled_time: string;
  days_ahead: number;
  channel: ReminderChannelType;
}

export interface ReminderScheduleSummary {
  id: number;
  medication_name: string;
  dosage: string;
  frequency: ReminderFrequencyType;
  reminder_times: string[];
  is_active: boolean;
  next_reminder?: string;
  total_reminders: number;
  completed_reminders: number;
}
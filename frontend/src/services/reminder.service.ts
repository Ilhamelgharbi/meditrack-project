// src/services/reminder.service.ts
import api from './api';
import { medicationService } from './medications.service';
import type {
  ReminderScheduleCreate,
  ReminderScheduleUpdate,
  ReminderScheduleResponse,
  ReminderResponse,
  ReminderCancel,
  ReminderStats,
  ReminderFilters,
  ReminderScheduleFilters,
  TodayReminder,
  UpcomingReminder,
  ReminderScheduleSummary,
  ReminderScheduleToggleResponse,
  ReminderGenerationResponse
} from '../types/reminders.types';

class ReminderService {
  private baseUrl = '/reminders';

  // ==================== REMINDER SCHEDULES ====================

  // Get all reminder schedules for current patient
  async getReminderSchedules(filters?: ReminderScheduleFilters): Promise<ReminderScheduleResponse[]> {
    const params = new URLSearchParams();
    if (filters?.active_only !== undefined) {
      params.append('active_only', filters.active_only.toString());
    }

    const response = await api.get<ReminderScheduleResponse[]>(`${this.baseUrl}/schedules/?${params}`);
    return response.data;
  }

  // Get reminder schedule by ID
  async getReminderSchedule(scheduleId: number): Promise<ReminderScheduleResponse> {
    const response = await api.get<ReminderScheduleResponse>(`${this.baseUrl}/schedules/${scheduleId}`);
    return response.data;
  }

  // Get reminder schedule by medication ID
  async getReminderScheduleByMedication(patientMedicationId: number): Promise<ReminderScheduleResponse | null> {
    try {
      const response = await api.get<ReminderScheduleResponse>(`${this.baseUrl}/schedules/medication/${patientMedicationId}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  // Create new reminder schedule
  async createReminderSchedule(schedule: ReminderScheduleCreate): Promise<ReminderScheduleResponse> {
    const response = await api.post<ReminderScheduleResponse>(`${this.baseUrl}/schedules`, schedule);
    return response.data;
  }

  // Update reminder schedule
  async updateReminderSchedule(scheduleId: number, updates: ReminderScheduleUpdate): Promise<ReminderScheduleResponse> {
    const response = await api.put<ReminderScheduleResponse>(`${this.baseUrl}/schedules/${scheduleId}`, updates);
    return response.data;
  }

  // Delete reminder schedule
  async deleteReminderSchedule(scheduleId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/schedules/${scheduleId}`);
  }

  // Toggle reminder schedule active/inactive
  async toggleReminderSchedule(scheduleId: number, isActive: boolean): Promise<ReminderScheduleToggleResponse> {
    const response = await api.post<ReminderScheduleToggleResponse>(`${this.baseUrl}/schedules/${scheduleId}/toggle`, null, {
      params: { is_active: isActive }
    });
    return response.data;
  }

  // Generate reminders for a schedule
  async generateReminders(scheduleId: number, daysAhead: number = 7): Promise<ReminderGenerationResponse> {
    const response = await api.post<ReminderGenerationResponse>(`${this.baseUrl}/schedules/${scheduleId}/generate`, null, {
      params: { days_ahead: daysAhead }
    });
    return response.data;
  }

  // ==================== REMINDERS ====================

  // Get reminders with filters
  async getReminders(filters?: ReminderFilters): Promise<ReminderResponse[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit?.toString() || '100');

    const response = await api.get<ReminderResponse[]>(`${this.baseUrl}/?${params}`);
    return response.data;
  }

  // Get specific reminder
  async getReminder(reminderId: number): Promise<ReminderResponse> {
    const response = await api.get<ReminderResponse>(`${this.baseUrl}/${reminderId}`);
    return response.data;
  }

  // Cancel a reminder
  async cancelReminder(reminderId: number, cancelData?: ReminderCancel): Promise<ReminderResponse> {
    const response = await api.post<ReminderResponse>(`${this.baseUrl}/${reminderId}/cancel`, cancelData || {});
    return response.data;
  }

  // ==================== STATS ====================

  // Get reminder statistics
  async getReminderStats(days: number = 30): Promise<ReminderStats> {
    const response = await api.get<ReminderStats>(`${this.baseUrl}/stats/summary`, {
      params: { days }
    });
    return response.data;
  }

  // ==================== UI HELPERS ====================

  // Get today's reminders with proper medication data
  async getTodayReminders(): Promise<TodayReminder[]> {
    // Get reminders for today and tomorrow
    const [reminders, medications] = await Promise.all([
      this.getReminders({
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        limit: 50
      }),
      medicationService.getMyMedications()
    ]);

    return reminders.map(reminder => {
      const medication = medications.find(m => m.id === reminder.patient_medication_id);
      return {
        id: reminder.id,
        medication_name: medication?.medication?.name || 'Unknown Medication',
        dosage: medication?.dosage || 'Unknown Dosage',
        scheduled_time: reminder.scheduled_time,
        status: reminder.status,
        channel: reminder.channel,
        advance_minutes: reminder.reminder_advance_minutes,
        instructions: medication?.instructions || '',
        is_overdue: new Date(reminder.scheduled_time) < new Date(),
        time_until: this.calculateTimeUntil(reminder.scheduled_time)
      };
    }).sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime());
  }

// Get upcoming reminders (next 7 days) with proper medication data
  async getUpcomingReminders(): Promise<UpcomingReminder[]> {
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

    // Get both reminders and medications in parallel
    const [reminders, medications] = await Promise.all([
      this.getReminders({
        start_date: new Date().toISOString(),
        end_date: nextWeek,
        status: 'pending',
        limit: 100
      }),
      medicationService.getMyMedications()
    ]);

    return reminders.map(reminder => {
      const medication = medications.find(m => m.id === reminder.patient_medication_id);
      return {
        id: reminder.id,
        medication_name: medication?.medication?.name || 'Unknown Medication',
        dosage: medication?.dosage || 'Unknown Dosage',
        scheduled_time: reminder.scheduled_time,
        days_ahead: Math.ceil((new Date(reminder.scheduled_time).getTime() - Date.now()) / (24 * 60 * 60 * 1000)),
        channel: reminder.channel
      };
    }).sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime());
  }

  // Get reminder schedule summaries with medication data
  async getReminderScheduleSummaries(): Promise<ReminderScheduleSummary[]> {
    const [schedules, medications] = await Promise.all([
      this.getReminderSchedules({ active_only: true }),
      medicationService.getMyMedications()
    ]);

    return schedules.map(schedule => {
      const medication = medications.find(m => m.id === schedule.patient_medication_id);
      return {
        id: schedule.id,
        medication_name: medication?.medication?.name || 'Unknown Medication',
        dosage: medication?.dosage || 'Unknown Dosage',
        frequency: schedule.frequency,
        reminder_times: schedule.reminder_times,
        is_active: schedule.is_active,
        next_reminder: this.calculateNextReminder(schedule),
        total_reminders: 0, // Would need additional API call or calculation
        completed_reminders: 0 // Would need additional API call or calculation
      };
    });
  }

  // Get reminder analytics (combines stats with schedule data)
  async getReminderAnalytics(): Promise<{
    stats: ReminderStats;
    schedules: ReminderScheduleSummary[];
    todayReminders: TodayReminder[];
    upcomingReminders: UpcomingReminder[];
  }> {
    const [stats, schedules, todayReminders, upcomingReminders] = await Promise.all([
      this.getReminderStats(),
      this.getReminderScheduleSummaries(),
      this.getTodayReminders(),
      this.getUpcomingReminders()
    ]);

    return {
      stats,
      schedules,
      todayReminders,
      upcomingReminders
    };
  }

  // ==================== UTILITY METHODS ====================

  private calculateTimeUntil(scheduledTime: string): string {
    const now = new Date();
    const scheduled = new Date(scheduledTime);
    const diffMs = scheduled.getTime() - now.getTime();
    const diffHours = Math.floor(Math.abs(diffMs) / (1000 * 60 * 60));
    const diffMinutes = Math.floor(Math.abs(diffMs) / (1000 * 60)) % 60;

    if (diffMs > 0) {
      if (diffHours > 0) {
        return `in ${diffHours}h ${diffMinutes}m`;
      } else {
        return `in ${diffMinutes}m`;
      }
    } else {
      if (diffHours > 0) {
        return `${diffHours}h ${diffMinutes}m ago`;
      } else {
        return `${diffMinutes}m ago`;
      }
    }
  }

  private calculateNextReminder(schedule: ReminderScheduleResponse): string | undefined {
    if (!schedule.is_active) return undefined;

    const now = new Date();

    // Find next reminder time today or tomorrow
    for (const timeStr of schedule.reminder_times) {
      const [hours, minutes] = timeStr.split(':').map(Number);
      const reminderTime = new Date(now);
      reminderTime.setHours(hours, minutes, 0, 0);

      if (reminderTime > now) {
        return reminderTime.toISOString();
      }

      // Check tomorrow
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(hours, minutes, 0, 0);
      return tomorrow.toISOString();
    }

    return undefined;
  }
}

export const reminderService = new ReminderService();

// src/hooks/useReminders.ts
import { useState, useEffect } from 'react';
import { reminderService } from '../services/reminder.service';
import { medicationService } from '../services/medications.service';
import { useAuth } from './useAuth';
import type {
  ReminderScheduleResponse,
  ReminderResponse,
  ReminderStats,
  TodayReminder,
  ReminderScheduleToggleResponse,
  ReminderGenerationResponse
} from '../types/reminders.types';
import type { PatientMedicationDetailed } from '../types/medications.types';

interface UseRemindersReturn {
  // Data
  schedules: ReminderScheduleResponse[];
  todayReminders: TodayReminder[];
  recentReminders: ReminderResponse[];
  medications: PatientMedicationDetailed[];
  stats: ReminderStats | null;

  // State
  loading: boolean;
  error: string | null;

  // Actions
  refetch: () => Promise<void>;
  createSchedule: (scheduleData: any) => Promise<ReminderScheduleResponse>;
  updateSchedule: (scheduleId: number, updates: any) => Promise<ReminderScheduleResponse>;
  deleteSchedule: (scheduleId: number) => Promise<void>;
  toggleSchedule: (scheduleId: number, isActive: boolean) => Promise<ReminderScheduleToggleResponse>;
  cancelReminder: (reminderId: number, reason?: string) => Promise<void>;
  generateReminders: (scheduleId: number, daysAhead?: number) => Promise<ReminderGenerationResponse>;
  takeMedication: (reminderId: number) => Promise<void>;
  skipMedication: (reminderId: number) => Promise<void>;
  snoozeReminder: (reminderId: number) => Promise<void>;
  viewScheduleDetails: (schedule: ReminderScheduleResponse) => void;
  editSchedule: (schedule: ReminderScheduleResponse) => void;
  cancelSchedule: (scheduleId: number) => Promise<void>;
  getReminder: (reminderId: number) => Promise<ReminderResponse>;
  getScheduleByMedication: (medicationId: number) => Promise<ReminderScheduleResponse | null>;
}

export const useReminders = (): UseRemindersReturn => {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<ReminderScheduleResponse[]>([]);
  const [todayReminders, setTodayReminders] = useState<TodayReminder[]>([]);
  const [recentReminders, setRecentReminders] = useState<ReminderResponse[]>([]);
  const [medications, setMedications] = useState<PatientMedicationDetailed[]>([]);
  const [stats, setStats] = useState<ReminderStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllData = async () => {
    if (!user) {
      setError('User not authenticated');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [
        schedulesData,
        remindersData,
        statsData,
        medicationsData
      ] = await Promise.all([
        reminderService.getReminderSchedules(),
        reminderService.getReminders({ limit: 50 }),
        reminderService.getReminderStats(),
        medicationService.getMyMedications()
      ]);

      setSchedules(schedulesData);
      setRecentReminders(remindersData);
      setStats(statsData);
      setMedications(medicationsData);

      // Process today's reminders
      const todayRemindersData = processTodayReminders(remindersData, medicationsData);
      setTodayReminders(todayRemindersData);

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load reminder data';
      setError(message);
      console.error('Error fetching reminder data:', err);
    } finally {
      setLoading(false);
    }
  };

  const processTodayReminders = (
    reminders: ReminderResponse[],
    medications: PatientMedicationDetailed[]
  ): TodayReminder[] => {
    const today = new Date().toDateString();
    const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000).toDateString();

    return reminders
      .filter(reminder => {
        const reminderDate = new Date(reminder.scheduled_time).toDateString();
        return reminderDate === today || reminderDate === tomorrow;
      })
      .map(reminder => {
        const medication = medications.find(m => m.id === reminder.patient_medication_id);
        return {
          id: reminder.id,
          medication_name: medication?.medication?.name || 'Unknown Medication',
          dosage: medication?.dosage || 'Unknown',
          scheduled_time: reminder.scheduled_time,
          status: reminder.status,
          channel: reminder.channel,
          advance_minutes: reminder.reminder_advance_minutes,
          instructions: medication?.instructions,
          is_overdue: new Date(reminder.scheduled_time) < new Date(),
          time_until: calculateTimeUntil(reminder.scheduled_time)
        };
      })
      .sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime());
  };

  const calculateTimeUntil = (targetTime: string): string => {
    const now = new Date();
    const target = new Date(targetTime);
    const diffMs = target.getTime() - now.getTime();
    const diffHours = Math.floor(Math.abs(diffMs) / (1000 * 60 * 60));
    const diffMinutes = Math.floor(Math.abs(diffMs) / (1000 * 60)) % 60;

    if (diffMs < 0) {
      return diffHours > 0 ? `${diffHours}h ${diffMinutes}m ago` : `${diffMinutes}m ago`;
    } else {
      return diffHours > 0 ? `in ${diffHours}h ${diffMinutes}m` : `in ${diffMinutes}m`;
    }
  };

  const createSchedule = async (scheduleData: any): Promise<ReminderScheduleResponse> => {
    try {
      const newSchedule = await reminderService.createReminderSchedule(scheduleData);
      await fetchAllData(); // Refresh data
      return newSchedule;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create reminder schedule';
      setError(message);
      throw new Error(message);
    }
  };

  const updateSchedule = async (scheduleId: number, updates: any): Promise<ReminderScheduleResponse> => {
    try {
      const updatedSchedule = await reminderService.updateReminderSchedule(scheduleId, updates);
      await fetchAllData(); // Refresh data
      return updatedSchedule;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update reminder schedule';
      setError(message);
      throw new Error(message);
    }
  };

  const deleteSchedule = async (scheduleId: number): Promise<void> => {
    try {
      await reminderService.deleteReminderSchedule(scheduleId);
      await fetchAllData(); // Refresh data
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete reminder schedule';
      setError(message);
      throw new Error(message);
    }
  };

  const toggleSchedule = async (scheduleId: number, isActive: boolean): Promise<ReminderScheduleToggleResponse> => {
    try {
      const result = await reminderService.toggleReminderSchedule(scheduleId, isActive);
      await fetchAllData(); // Refresh data
      return result;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update schedule';
      setError(message);
      throw new Error(message);
    }
  };

  const cancelReminder = async (reminderId: number, reason?: string) => {
    try {
      await reminderService.cancelReminder(reminderId, { reason });
      await fetchAllData(); // Refresh data
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to cancel reminder';
      setError(message);
      throw new Error(message);
    }
  };

  const generateReminders = async (scheduleId: number, daysAhead: number = 7): Promise<ReminderGenerationResponse> => {
    try {
      const result = await reminderService.generateReminders(scheduleId, daysAhead);
      await fetchAllData(); // Refresh data
      return result;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate reminders';
      setError(message);
      throw new Error(message);
    }
  };

  const takeMedication = async (reminderId: number) => {
    try {
      // TODO: Implement take medication API call when backend supports it
      // Placeholder - would call actual API here
      void reminderId;
      await fetchAllData(); // Refresh data
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to mark medication as taken';
      setError(message);
      throw new Error(message);
    }
  };

  const skipMedication = async (reminderId: number) => {
    try {
      // TODO: Implement skip medication API call when backend supports it
      // Placeholder - would call actual API here
      void reminderId;
      await fetchAllData(); // Refresh data
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to skip medication';
      setError(message);
      throw new Error(message);
    }
  };

  const snoozeReminder = async (reminderId: number) => {
    try {
      // TODO: Implement snooze reminder API call when backend supports it
      // Placeholder - would call actual API here
      void reminderId;
      await fetchAllData(); // Refresh data
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to snooze reminder';
      setError(message);
      throw new Error(message);
    }
  };

  const viewScheduleDetails = (schedule: ReminderScheduleResponse) => {
    // TODO: Implement schedule details view
    // Placeholder - would open modal here
    void schedule;
  };

  const editSchedule = (schedule: ReminderScheduleResponse) => {
    // TODO: Implement schedule edit functionality
    // Placeholder - would open edit form here
    void schedule;
  };

  const cancelSchedule = async (scheduleId: number) => {
    try {
      await toggleSchedule(scheduleId, false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to cancel schedule';
      setError(message);
      throw new Error(message);
    }
  };

  const getReminder = async (reminderId: number): Promise<ReminderResponse> => {
    try {
      return await reminderService.getReminder(reminderId);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to get reminder';
      setError(message);
      throw new Error(message);
    }
  };

  const getScheduleByMedication = async (medicationId: number): Promise<ReminderScheduleResponse | null> => {
    try {
      return await reminderService.getReminderScheduleByMedication(medicationId);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to get schedule by medication';
      setError(message);
      throw new Error(message);
    }
  };

  useEffect(() => {
    if (user) {
      fetchAllData();
    } else {
      setLoading(false);
    }
  }, [user]);

  return {
    schedules,
    todayReminders,
    recentReminders,
    medications,
    stats,
    loading,
    error,
    refetch: fetchAllData,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    toggleSchedule,
    cancelReminder,
    generateReminders,
    takeMedication,
    skipMedication,
    snoozeReminder,
    viewScheduleDetails,
    editSchedule,
    cancelSchedule,
    getReminder,
    getScheduleByMedication,
  };
};

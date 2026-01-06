// src/pages/patient/Reminders.tsx
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import {
  Bell, Clock, Settings, Check, X, Calendar, Plus, Pill,
  ChevronLeft, ChevronRight, AlertCircle, CheckCircle, XCircle,
  Smartphone, Mail, Loader2, RefreshCw, SkipForward, Timer
} from 'lucide-react';
import { medicationService } from '../../services/medications.service';
import { adherenceService, type MedicationLog } from '../../services/adherence.service';
import { reminderService } from '../../services/reminder.service';
import type { ReminderScheduleResponse } from '../../types/reminders.types';

// Types
interface TodayReminder {
  id: string;
  patientMedicationId: number;
  medicationName: string;
  dosage: string;
  scheduledTime: string; // HH:MM format
  scheduledDateTime: Date;
  status: 'upcoming' | 'due' | 'overdue' | 'taken' | 'skipped' | 'missed';
  logId?: number; // If already logged
  instructions?: string;
}

interface PatientMedication {
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

type TabType = 'today' | 'calendar' | 'schedules' | 'settings';

const RemindersPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('today');
  const [medications, setMedications] = useState<PatientMedication[]>([]);
  const [reminderSchedules, setReminderSchedules] = useState<ReminderScheduleResponse[]>([]);
  const [todayReminders, setTodayReminders] = useState<TodayReminder[]>([]);
  const [todayLogs, setTodayLogs] = useState<MedicationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  // Calendar state
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  
  // Schedule modal state
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [schedulingMedication, setSchedulingMedication] = useState<PatientMedication | null>(null);
  const [reminderTimes, setReminderTimes] = useState<string[]>([]);
  const [channels, setChannels] = useState<string[]>(['push', 'email']);
  const [editingSchedule, setEditingSchedule] = useState<ReminderScheduleResponse | null>(null);

  // Settings state
  const [notifications, setNotifications] = useState({
    email: true,
    sms: false,
    push: true,
    reminderAdvance: '15'
  });

  // Stats
  const stats = {
    todayTotal: todayReminders.length,
    taken: todayReminders.filter(r => r.status === 'taken').length,
    upcoming: todayReminders.filter(r => ['upcoming', 'due'].includes(r.status)).length,
    missed: todayReminders.filter(r => ['missed', 'overdue'].includes(r.status)).length,
    skipped: todayReminders.filter(r => r.status === 'skipped').length,
  };

  // Fetch all data
  const fetchData = useCallback(async () => {
    if (!user) return;

    try {
      setLoading(true);

      // Fetch medications, schedules, and today's logs in parallel
      const [medicationsData, schedulesData, logsData] = await Promise.all([
        medicationService.getPatientMedications(user.id).catch(() => []),
        reminderService.getReminderSchedules().catch(() => []),
        adherenceService.getLogs({ limit: 50 }).catch(() => [])
      ]);

      setMedications(medicationsData);
      setReminderSchedules(schedulesData);
      
      // Filter today's logs
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const todaysLogs = logsData.filter(log => {
        const logDate = new Date(log.scheduled_time);
        logDate.setHours(0, 0, 0, 0);
        return logDate.getTime() === today.getTime();
      });
      setTodayLogs(todaysLogs);

      // Generate today's reminders from schedules
      const reminders = generateTodayReminders(schedulesData, medicationsData, todaysLogs);
      setTodayReminders(reminders);

    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Generate today's reminders from schedules
  const generateTodayReminders = (
    schedules: ReminderScheduleResponse[],
    meds: PatientMedication[],
    logs: MedicationLog[]
  ): TodayReminder[] => {
    const now = new Date();
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const reminders: TodayReminder[] = [];

    schedules.forEach(schedule => {
      if (!schedule.is_active) return;

      // Get medication info - prioritize schedule.patient_medication
      const medication = schedule.patient_medication || meds.find(m => m.id === schedule.patient_medication_id);
      if (!medication) return;

      const medicationName = medication.medication?.name || 'Unknown Medication';
      const dosage = medication.dosage || '';

      // Generate reminder for each time
      schedule.reminder_times.forEach(timeStr => {
        const [hours, minutes] = timeStr.split(':').map(Number);
        const scheduledDateTime = new Date(today);
        scheduledDateTime.setHours(hours, minutes, 0, 0);

        // Check if already logged
        const existingLog = logs.find(log => {
          const logTime = new Date(log.scheduled_time);
          return log.patient_medication_id === schedule.patient_medication_id &&
                 logTime.getHours() === hours &&
                 logTime.getMinutes() === minutes;
        });

        // Determine status
        let status: TodayReminder['status'] = 'upcoming';
        if (existingLog) {
          status = existingLog.status as 'taken' | 'skipped' | 'missed';
        } else {
          const diffMinutes = (now.getTime() - scheduledDateTime.getTime()) / (1000 * 60);
          if (diffMinutes >= 60) {
            status = 'overdue'; // More than 1 hour past
          } else if (diffMinutes >= -15) {
            status = 'due'; // Within 15 min before to 60 min after
          }
        }

        reminders.push({
          id: `${schedule.id}-${timeStr}`,
          patientMedicationId: schedule.patient_medication_id,
          medicationName,
          dosage,
          scheduledTime: timeStr,
          scheduledDateTime,
          status,
          logId: existingLog?.id,
          instructions: medication.instructions
        });
      });
    });

    // Sort by time
    return reminders.sort((a, b) => a.scheduledDateTime.getTime() - b.scheduledDateTime.getTime());
  };

  // Log medication action
  const handleLogMedication = async (reminder: TodayReminder, action: 'taken' | 'skipped' | 'missed') => {
    setActionLoading(reminder.id);
    try {
      await adherenceService.logDose({
        patient_medication_id: reminder.patientMedicationId,
        scheduled_time: reminder.scheduledDateTime.toISOString(),
        status: action,
        actual_time: action === 'taken' ? new Date().toISOString() : undefined,
        notes: action === 'taken' ? 'Logged from reminders' : undefined,
        skipped_reason: action === 'skipped' ? 'User skipped' : undefined
      });
      
      // Refresh data
      await fetchData();
    } catch (err) {
      console.error('Error logging medication:', err);
      alert('Failed to log medication. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  // Save schedule
  const handleSaveSchedule = async () => {
    if (!schedulingMedication || reminderTimes.length === 0) return;

    setActionLoading('save-schedule');
    try {
      const frequency = schedulingMedication.times_per_day <= 1 ? 'daily' 
        : schedulingMedication.times_per_day === 2 ? 'twice_daily' 
        : schedulingMedication.times_per_day === 3 ? 'three_times_daily' 
        : 'custom';

      if (editingSchedule) {
        await reminderService.updateReminderSchedule(editingSchedule.id, {
          reminder_times: reminderTimes,
          channel_push: channels.includes('push'),
          channel_email: channels.includes('email'),
          channel_sms: channels.includes('sms'),
          is_active: true
        });
      } else {
        const newSchedule = await reminderService.createReminderSchedule({
          patient_medication_id: schedulingMedication.id,
          frequency,
          reminder_times: reminderTimes,
          advance_minutes: 15,
          channel_push: channels.includes('push'),
          channel_email: channels.includes('email'),
          channel_sms: channels.includes('sms'),
          channel_whatsapp: false,
          auto_skip_if_taken: true,
          escalate_if_missed: true,
          escalate_delay_minutes: 30,
          quiet_hours_enabled: false,
          start_date: new Date().toISOString(),
        });
        await reminderService.generateReminders(newSchedule.id, 7);
      }

      setShowScheduleModal(false);
      setSchedulingMedication(null);
      setReminderTimes([]);
      setEditingSchedule(null);
      await fetchData();
    } catch (err) {
      console.error('Failed to save schedule:', err);
      alert('Failed to save schedule. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  // Delete schedule
  const handleDeleteSchedule = async (scheduleId: number) => {
    if (!confirm('Are you sure you want to delete this reminder schedule?')) return;
    
    try {
      await reminderService.deleteReminderSchedule(scheduleId);
      await fetchData();
    } catch (err) {
      console.error('Failed to delete schedule:', err);
      alert('Failed to delete schedule.');
    }
  };

  // Toggle schedule active
  const handleToggleSchedule = async (schedule: ReminderScheduleResponse) => {
    try {
      await reminderService.toggleReminderSchedule(schedule.id, !schedule.is_active);
      await fetchData();
    } catch (err) {
      console.error('Failed to toggle schedule:', err);
    }
  };

  // Format time for display
  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':').map(Number);
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
  };

  // Get status badge
  const getStatusBadge = (status: TodayReminder['status']) => {
    switch (status) {
      case 'taken':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700"><CheckCircle size={12} /> Taken</span>;
      case 'skipped':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700"><SkipForward size={12} /> Skipped</span>;
      case 'missed':
      case 'overdue':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700"><XCircle size={12} /> {status === 'overdue' ? 'Overdue' : 'Missed'}</span>;
      case 'due':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700"><Timer size={12} /> Due Now</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600"><Clock size={12} /> Upcoming</span>;
    }
  };

  // Calendar helpers
  const generateMonthCalendar = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay();
    
    const days: { date: Date; isCurrentMonth: boolean; isToday: boolean; reminders: TodayReminder[] }[] = [];
    
    // Previous month padding
    for (let i = startPadding - 1; i >= 0; i--) {
      const date = new Date(year, month, -i);
      days.push({ date, isCurrentMonth: false, isToday: false, reminders: [] });
    }
    
    // Current month
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    for (let day = 1; day <= lastDay.getDate(); day++) {
      const date = new Date(year, month, day);
      const isToday = date.getTime() === today.getTime();
      days.push({ date, isCurrentMonth: true, isToday, reminders: [] });
    }
    
    // Next month padding
    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      const date = new Date(year, month + 1, i);
      days.push({ date, isCurrentMonth: false, isToday: false, reminders: [] });
    }
    
    return days;
  };

  const getRemindersForDate = (date: Date): { total: number; taken: number } => {
    // For now, just count schedules that would apply to this date
    let total = 0;
    let taken = 0;
    
    reminderSchedules.forEach(schedule => {
      if (!schedule.is_active) return;
      const start = new Date(schedule.start_date);
      const end = schedule.end_date ? new Date(schedule.end_date) : null;
      
      if (date >= start && (!end || date <= end)) {
        total += schedule.reminder_times.length;
      }
    });
    
    // Check logs for taken status
    const dateStr = date.toISOString().split('T')[0];
    todayLogs.forEach(log => {
      const logDate = new Date(log.scheduled_time).toISOString().split('T')[0];
      if (logDate === dateStr && log.status === 'taken') {
        taken++;
      }
    });
    
    return { total, taken };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
          <p className="text-slate-600">Loading your reminders...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Medication Reminders</h1>
          <p className="text-slate-500">Track and manage your medication schedule</p>
        </div>
        <Button onClick={fetchData} variant="secondary" className="flex items-center gap-2">
          <RefreshCw size={16} />
          Refresh
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Pill className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-700">{stats.todayTotal}</p>
              <p className="text-xs text-blue-600">Today's Total</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500 rounded-lg">
              <CheckCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-700">{stats.taken}</p>
              <p className="text-xs text-emerald-600">Taken</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500 rounded-lg">
              <Clock className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-700">{stats.upcoming}</p>
              <p className="text-xs text-amber-600">Upcoming</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500 rounded-lg">
              <AlertCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-700">{stats.missed + stats.skipped}</p>
              <p className="text-xs text-red-600">Missed/Skipped</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
        {[
          { id: 'today', label: 'Today', icon: Bell },
          { id: 'calendar', label: 'Calendar', icon: Calendar },
          { id: 'schedules', label: 'Schedules', icon: Clock },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as TabType)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === id
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Icon size={16} />
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      {/* TODAY TAB */}
      {activeTab === 'today' && (
        <div className="space-y-4">
          {todayReminders.length === 0 ? (
            <Card className="p-8 text-center">
              <Bell className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-700 mb-2">No Reminders Today</h3>
              <p className="text-slate-500 mb-4">You don't have any scheduled medications for today.</p>
              <Button onClick={() => setActiveTab('schedules')}>
                <Plus size={16} className="mr-2" />
                Set Up Reminders
              </Button>
            </Card>
          ) : (
            <div className="space-y-3">
              {todayReminders.map((reminder) => (
                <Card key={reminder.id} className={`p-4 transition-all ${
                  reminder.status === 'due' ? 'ring-2 ring-blue-500 bg-blue-50/50' :
                  reminder.status === 'overdue' ? 'bg-red-50/50' :
                  reminder.status === 'taken' ? 'bg-emerald-50/30' : ''
                }`}>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    {/* Left: Medication Info */}
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      <div className={`p-3 rounded-xl ${
                        reminder.status === 'taken' ? 'bg-emerald-100' :
                        reminder.status === 'due' ? 'bg-blue-100' :
                        reminder.status === 'overdue' ? 'bg-red-100' :
                        'bg-slate-100'
                      }`}>
                        <Pill className={`w-5 h-5 ${
                          reminder.status === 'taken' ? 'text-emerald-600' :
                          reminder.status === 'due' ? 'text-blue-600' :
                          reminder.status === 'overdue' ? 'text-red-600' :
                          'text-slate-500'
                        }`} />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-semibold text-slate-900 truncate">{reminder.medicationName}</h3>
                        <p className="text-sm text-slate-500">{reminder.dosage}</p>
                        {reminder.instructions && (
                          <p className="text-xs text-slate-400 truncate">{reminder.instructions}</p>
                        )}
                      </div>
                    </div>

                    {/* Middle: Time & Status */}
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-lg font-semibold text-slate-700">{formatTime(reminder.scheduledTime)}</span>
                      {getStatusBadge(reminder.status)}
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2 flex-wrap justify-end">
                      {['upcoming', 'due', 'overdue'].includes(reminder.status) ? (
                        <>
                          <Button
                            size="sm"
                            onClick={() => handleLogMedication(reminder, 'taken')}
                            disabled={actionLoading === reminder.id}
                            className="bg-emerald-600 hover:bg-emerald-700"
                          >
                            {actionLoading === reminder.id ? (
                              <Loader2 size={14} className="animate-spin" />
                            ) : (
                              <>
                                <Check size={14} className="mr-1" />
                                Take
                              </>
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleLogMedication(reminder, 'skipped')}
                            disabled={actionLoading === reminder.id}
                          >
                            <X size={14} className="mr-1" />
                            Skip
                          </Button>
                          {reminder.status === 'overdue' && (
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => handleLogMedication(reminder, 'missed')}
                              disabled={actionLoading === reminder.id}
                              className="text-red-600 border-red-200 hover:bg-red-50"
                            >
                              Missed
                            </Button>
                          )}
                        </>
                      ) : (
                        <span className="text-sm text-slate-400 italic">
                          {reminder.status === 'taken' ? 'Completed' : 
                           reminder.status === 'skipped' ? 'Skipped' : 'Logged'}
                        </span>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CALENDAR TAB */}
      {activeTab === 'calendar' && (
        <Card className="p-6">
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
              className="p-2 hover:bg-slate-100 rounded-lg"
            >
              <ChevronLeft size={20} />
            </button>
            <h2 className="text-lg font-semibold text-slate-900">
              {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </h2>
            <button
              onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
              className="p-2 hover:bg-slate-100 rounded-lg"
            >
              <ChevronRight size={20} />
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="p-2 text-center text-xs font-medium text-slate-500 uppercase">
                {day}
              </div>
            ))}
            {generateMonthCalendar().map((day, idx) => {
              const { total, taken } = getRemindersForDate(day.date);
              return (
                <div
                  key={idx}
                  className={`min-h-[80px] p-2 rounded-lg border ${
                    day.isToday ? 'border-blue-500 bg-blue-50' :
                    day.isCurrentMonth ? 'border-slate-200 bg-white' :
                    'border-slate-100 bg-slate-50'
                  }`}
                >
                  <span className={`text-sm font-medium ${
                    day.isToday ? 'text-blue-600' :
                    day.isCurrentMonth ? 'text-slate-700' :
                    'text-slate-400'
                  }`}>
                    {day.date.getDate()}
                  </span>
                  {total > 0 && day.isCurrentMonth && (
                    <div className="mt-1">
                      <div className="flex items-center gap-1 text-xs">
                        <div className={`w-2 h-2 rounded-full ${taken === total ? 'bg-emerald-500' : taken > 0 ? 'bg-amber-500' : 'bg-slate-300'}`} />
                        <span className="text-slate-500">{taken}/{total}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 mt-6 pt-4 border-t text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span>All taken</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <span>Partial</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-slate-300" />
              <span>Scheduled</span>
            </div>
          </div>
        </Card>
      )}

      {/* SCHEDULES TAB */}
      {activeTab === 'schedules' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Reminder Schedules</h2>
            <Button onClick={() => setShowScheduleModal(true)}>
              <Plus size={16} className="mr-2" />
              New Schedule
            </Button>
          </div>

          {reminderSchedules.length === 0 ? (
            <Card className="p-8 text-center">
              <Clock className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-700 mb-2">No Schedules Yet</h3>
              <p className="text-slate-500 mb-4">Set up reminder schedules for your medications.</p>
              <Button onClick={() => setShowScheduleModal(true)}>
                <Plus size={16} className="mr-2" />
                Create Schedule
              </Button>
            </Card>
          ) : (
            <div className="space-y-3">
              {reminderSchedules.map((schedule) => {
                const med = schedule.patient_medication || medications.find(m => m.id === schedule.patient_medication_id);
                return (
                  <Card key={schedule.id} className={`p-4 ${!schedule.is_active ? 'opacity-60' : ''}`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${schedule.is_active ? 'bg-blue-100' : 'bg-slate-100'}`}>
                          <Bell className={`w-5 h-5 ${schedule.is_active ? 'text-blue-600' : 'text-slate-400'}`} />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">
                            {med?.medication?.name || 'Unknown Medication'}
                          </h3>
                          <p className="text-sm text-slate-500">
                            {schedule.reminder_times.map(t => formatTime(t)).join(', ')}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            {schedule.channel_push && <span className="text-xs px-2 py-0.5 bg-slate-100 rounded">Push</span>}
                            {schedule.channel_email && <span className="text-xs px-2 py-0.5 bg-slate-100 rounded">Email</span>}
                            {schedule.channel_sms && <span className="text-xs px-2 py-0.5 bg-slate-100 rounded">SMS</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleToggleSchedule(schedule)}
                        >
                          {schedule.is_active ? 'Pause' : 'Resume'}
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            setEditingSchedule(schedule);
                            setSchedulingMedication(med as PatientMedication);
                            setReminderTimes(schedule.reminder_times);
                            setChannels([
                              ...(schedule.channel_push ? ['push'] : []),
                              ...(schedule.channel_email ? ['email'] : []),
                              ...(schedule.channel_sms ? ['sms'] : []),
                            ]);
                            setShowScheduleModal(true);
                          }}
                        >
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleDeleteSchedule(schedule.id)}
                          className="text-red-600 hover:bg-red-50"
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* SETTINGS TAB */}
      {activeTab === 'settings' && (
        <div className="max-w-2xl space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Notification Channels</h3>
            <div className="space-y-4">
              {[
                { id: 'push', label: 'Push Notifications', desc: 'Receive alerts on your device', icon: Bell },
                { id: 'email', label: 'Email Notifications', desc: 'Get reminders via email', icon: Mail },
                { id: 'sms', label: 'SMS Notifications', desc: 'Text message reminders', icon: Smartphone },
              ].map(({ id, label, desc, icon: Icon }) => (
                <div key={id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white rounded-lg shadow-sm">
                      <Icon size={20} className="text-slate-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{label}</p>
                      <p className="text-xs text-slate-500">{desc}</p>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={notifications[id as keyof typeof notifications] as boolean}
                      onChange={() => setNotifications(prev => ({ ...prev, [id]: !prev[id as keyof typeof notifications] }))}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Reminder Timing</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Send reminder before scheduled time
              </label>
              <select
                className="w-full px-4 py-3 rounded-lg border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500"
                value={notifications.reminderAdvance}
                onChange={(e) => setNotifications(prev => ({ ...prev, reminderAdvance: e.target.value }))}
              >
                <option value="0">At exact time</option>
                <option value="5">5 minutes before</option>
                <option value="15">15 minutes before</option>
                <option value="30">30 minutes before</option>
              </select>
            </div>
            <Button className="mt-4">Save Preferences</Button>
          </Card>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-900">
                  {editingSchedule ? 'Edit Schedule' : 'New Reminder Schedule'}
                </h3>
                <button
                  onClick={() => {
                    setShowScheduleModal(false);
                    setSchedulingMedication(null);
                    setEditingSchedule(null);
                    setReminderTimes([]);
                  }}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Medication Selection */}
              {!schedulingMedication && !editingSchedule && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Select Medication
                  </label>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {medications
                      .filter(m => m.status === 'active' && !reminderSchedules.some(rs => rs.patient_medication_id === m.id))
                      .map(med => (
                        <div
                          key={med.id}
                          onClick={() => setSchedulingMedication(med)}
                          className="p-4 border rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
                        >
                          <p className="font-medium text-slate-900">{med.medication?.name || 'Unknown'}</p>
                          <p className="text-sm text-slate-500">{med.dosage}</p>
                        </div>
                      ))}
                    {medications.filter(m => m.status === 'active' && !reminderSchedules.some(rs => rs.patient_medication_id === m.id)).length === 0 && (
                      <p className="text-center text-slate-500 py-4">
                        All medications already have schedules.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Configure Times */}
              {(schedulingMedication || editingSchedule) && (
                <>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="font-medium text-blue-900">
                      {schedulingMedication?.medication?.name || 'Medication'}
                    </p>
                    <p className="text-sm text-blue-700">{schedulingMedication?.dosage}</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      Reminder Times
                    </label>
                    <div className="space-y-2">
                      {reminderTimes.map((time, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <input
                            type="time"
                            value={time}
                            onChange={(e) => {
                              const newTimes = [...reminderTimes];
                              newTimes[idx] = e.target.value;
                              setReminderTimes(newTimes);
                            }}
                            className="flex-1 px-3 py-2 border rounded-lg"
                          />
                          {reminderTimes.length > 1 && (
                            <button
                              onClick={() => setReminderTimes(reminderTimes.filter((_, i) => i !== idx))}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                            >
                              <X size={16} />
                            </button>
                          )}
                        </div>
                      ))}
                      <button
                        onClick={() => setReminderTimes([...reminderTimes, '08:00'])}
                        className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        <Plus size={16} />
                        Add Time
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      Notification Channels
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {['push', 'email', 'sms'].map(ch => (
                        <label key={ch} className="flex items-center gap-2 px-4 py-2 border rounded-lg cursor-pointer hover:bg-slate-50">
                          <input
                            type="checkbox"
                            checked={channels.includes(ch)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setChannels([...channels, ch]);
                              } else {
                                setChannels(channels.filter(c => c !== ch));
                              }
                            }}
                            className="rounded"
                          />
                          <span className="capitalize text-sm">{ch}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {(schedulingMedication || editingSchedule) && (
              <div className="p-6 border-t bg-slate-50 flex gap-3">
                <Button
                  onClick={handleSaveSchedule}
                  disabled={reminderTimes.length === 0 || actionLoading === 'save-schedule'}
                  className="flex-1"
                >
                  {actionLoading === 'save-schedule' ? (
                    <Loader2 size={16} className="animate-spin mr-2" />
                  ) : (
                    <Check size={16} className="mr-2" />
                  )}
                  {editingSchedule ? 'Update' : 'Create'} Schedule
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSchedulingMedication(null);
                    setEditingSchedule(null);
                    setReminderTimes([]);
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RemindersPage;

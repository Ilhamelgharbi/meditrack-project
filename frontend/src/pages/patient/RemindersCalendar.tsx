// src/pages/patient/RemindersCalendar.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Calendar, Clock, Plus, ChevronLeft, ChevronRight, 
  Check, X, Bell, BellOff, Pill, AlertCircle, 
  Settings, Filter, CalendarDays, List, LayoutGrid
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { DashboardLoadingModal, DashboardErrorModal } from '../../components/common';
import { reminderService } from '../../services/reminder.service';
import { medicationService } from '../../services/medications.service';
import { adherenceService } from '../../services/adherence.service';
import { useNotifications } from '../../contexts/NotificationContext';
import type { ReminderScheduleResponse, ReminderResponse } from '../../types/reminders.types';
import type { PatientMedicationDetailed } from '../../types/medications.types';

interface CalendarReminder {
  id: number;
  medication_name: string;
  dosage: string;
  scheduled_time: string;
  status: 'pending' | 'sent' | 'cancelled' | 'taken' | 'missed' | 'skipped';
  patient_medication_id: number;
}

type ViewMode = 'today' | 'week' | 'month' | 'calendar';
type ReminderStatusFilter = 'pending' | 'sent' | 'cancelled' | 'taken' | 'missed' | 'skipped' | 'all';

const RemindersCalendar: React.FC = () => {
  const { addNotification } = useNotifications();
  const [viewMode, setViewMode] = useState<ViewMode>('today');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [reminders, setReminders] = useState<CalendarReminder[]>([]);
  const [schedules, setSchedules] = useState<ReminderScheduleResponse[]>([]);
  const [medications, setMedications] = useState<PatientMedicationDetailed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<ReminderStatusFilter>('all');

  // Form state for creating schedule
  const [selectedMedicationId, setSelectedMedicationId] = useState<number | null>(null);
  const [reminderTimes, setReminderTimes] = useState<string[]>(['08:00']);
  const [channels, setChannels] = useState<string[]>(['push']);
  const [advanceMinutes, setAdvanceMinutes] = useState(15);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch schedules
      const schedulesData = await reminderService.getReminderSchedules();
      setSchedules(schedulesData);

      // Fetch medications
      const medsData = await medicationService.getMyMedications();
      setMedications(medsData.filter((m: PatientMedicationDetailed) => m.status === 'active'));

      // Fetch reminders for current view
      await fetchReminders();
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load reminder data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchReminders = async () => {
    try {
      const startDate = getViewStartDate();
      const endDate = getViewEndDate();
      
      // Only pass status filter for API-supported statuses
      const apiStatus = ['pending', 'sent', 'cancelled'].includes(filterStatus) 
        ? filterStatus as 'pending' | 'sent' | 'cancelled'
        : undefined;
      
      const remindersData = await reminderService.getReminders({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        status: apiStatus,
      });

      // Transform to CalendarReminder format with medication names
      const transformedReminders: CalendarReminder[] = remindersData.map((r: ReminderResponse) => {
        const med = medications.find(m => m.id === r.patient_medication_id);
        return {
          id: r.id,
          medication_name: med?.medication?.name || 'Unknown Medication',
          dosage: med?.dosage || '',
          scheduled_time: r.scheduled_time,
          status: r.status as CalendarReminder['status'],
          patient_medication_id: r.patient_medication_id,
        };
      });
      
      setReminders(transformedReminders);
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  const getViewStartDate = (): Date => {
    const date = new Date(currentDate);
    if (viewMode === 'today') {
      date.setHours(0, 0, 0, 0);
    } else if (viewMode === 'week') {
      const day = date.getDay();
      date.setDate(date.getDate() - day);
      date.setHours(0, 0, 0, 0);
    } else {
      date.setDate(1);
      date.setHours(0, 0, 0, 0);
    }
    return date;
  };

  const getViewEndDate = (): Date => {
    const date = new Date(currentDate);
    if (viewMode === 'today') {
      date.setHours(23, 59, 59, 999);
    } else if (viewMode === 'week') {
      const day = date.getDay();
      date.setDate(date.getDate() + (6 - day));
      date.setHours(23, 59, 59, 999);
    } else {
      date.setMonth(date.getMonth() + 1, 0);
      date.setHours(23, 59, 59, 999);
    }
    return date;
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchReminders();
  }, [viewMode, currentDate, filterStatus]);

  // Calendar navigation
  const navigatePrev = () => {
    const date = new Date(currentDate);
    if (viewMode === 'today') {
      date.setDate(date.getDate() - 1);
    } else if (viewMode === 'week') {
      date.setDate(date.getDate() - 7);
    } else {
      date.setMonth(date.getMonth() - 1);
    }
    setCurrentDate(date);
  };

  const navigateNext = () => {
    const date = new Date(currentDate);
    if (viewMode === 'today') {
      date.setDate(date.getDate() + 1);
    } else if (viewMode === 'week') {
      date.setDate(date.getDate() + 7);
    } else {
      date.setMonth(date.getMonth() + 1);
    }
    setCurrentDate(date);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };

  // Mark reminder as taken
  const markAsTaken = async (reminder: CalendarReminder) => {
    try {
      await adherenceService.logDose({
        patient_medication_id: reminder.patient_medication_id,
        scheduled_time: reminder.scheduled_time,
        status: 'taken',
        actual_time: new Date().toISOString(),
        notes: 'Logged from reminder calendar',
      });

      addNotification({
        type: 'success',
        title: 'Medication Logged',
        message: `${reminder.medication_name} marked as taken`,
      });

      await fetchReminders();
    } catch (error) {
      console.error('Error marking as taken:', error);
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to log medication',
      });
    }
  };

  // Skip reminder
  const skipReminder = async (reminder: CalendarReminder) => {
    try {
      await reminderService.cancelReminder(reminder.id);
      addNotification({
        type: 'info',
        title: 'Reminder Skipped',
        message: `${reminder.medication_name} reminder skipped`,
      });
      await fetchReminders();
    } catch (error) {
      console.error('Error skipping reminder:', error);
    }
  };

  // Create schedule
  const handleCreateSchedule = async () => {
    if (!selectedMedicationId || reminderTimes.length === 0) return;

    try {
      await reminderService.createReminderSchedule({
        patient_medication_id: selectedMedicationId,
        reminder_times: reminderTimes,
        frequency: 'daily',
        advance_minutes: advanceMinutes,
        start_date: new Date().toISOString().split('T')[0],
        channel_push: channels.includes('push'),
        channel_email: channels.includes('email'),
        channel_sms: channels.includes('sms'),
        channel_whatsapp: channels.includes('whatsapp'),
      });

      addNotification({
        type: 'success',
        title: 'Schedule Created',
        message: 'Reminder schedule created successfully',
      });
      setShowCreateModal(false);
      resetForm();
      await fetchData();
    } catch (error) {
      console.error('Error creating schedule:', error);
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to create schedule',
      });
    }
  };

  // Toggle schedule active status
  const toggleSchedule = async (scheduleId: number, isActive: boolean) => {
    try {
      await reminderService.toggleReminderSchedule(scheduleId, !isActive);
      await fetchData();
    } catch (error) {
      console.error('Error toggling schedule:', error);
    }
  };

  // Delete schedule
  const deleteSchedule = async (scheduleId: number) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    
    try {
      await reminderService.deleteReminderSchedule(scheduleId);
      addNotification({
        type: 'success',
        title: 'Schedule Deleted',
        message: 'Reminder schedule deleted successfully',
      });
      await fetchData();
    } catch (error) {
      console.error('Error deleting schedule:', error);
    }
  };

  const resetForm = () => {
    setSelectedMedicationId(null);
    setReminderTimes(['08:00']);
    setChannels(['push']);
    setAdvanceMinutes(15);
  };

  // Helper to get medication name from schedule
  const getMedicationName = (schedule: ReminderScheduleResponse): string => {
    // Prioritize schedule.patient_medication data, fall back to medications lookup
    const medication = schedule.patient_medication || medications.find(m => m.id === schedule.patient_medication_id);
    return medication?.medication?.name || 'Unknown Medication';
  };

  // Generate calendar days
  const generateCalendarDays = (): Date[] => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay();
    const days: Date[] = [];

    // Previous month padding
    for (let i = startPadding - 1; i >= 0; i--) {
      const date = new Date(year, month, -i);
      days.push(date);
    }

    // Current month
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }

    // Next month padding
    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      days.push(new Date(year, month + 1, i));
    }

    return days;
  };

  // Get reminders for a specific date
  const getRemindersForDate = (date: Date): CalendarReminder[] => {
    return reminders.filter(r => {
      const reminderDate = new Date(r.scheduled_time);
      return reminderDate.toDateString() === date.toDateString();
    });
  };

  // Group reminders by time period
  const groupRemindersByPeriod = (reminders: CalendarReminder[]) => {
    const groups = {
      morning: [] as CalendarReminder[],
      afternoon: [] as CalendarReminder[],
      evening: [] as CalendarReminder[],
      night: [] as CalendarReminder[],
    };

    reminders.forEach(r => {
      const hour = new Date(r.scheduled_time).getHours();
      if (hour >= 5 && hour < 12) groups.morning.push(r);
      else if (hour >= 12 && hour < 17) groups.afternoon.push(r);
      else if (hour >= 17 && hour < 21) groups.evening.push(r);
      else groups.night.push(r);
    });

    return groups;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'taken': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'missed': return 'bg-red-100 text-red-800 border-red-200';
      case 'skipped':
      case 'cancelled': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'pending': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'sent': return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'taken': return <Check className="w-4 h-4" />;
      case 'missed': return <AlertCircle className="w-4 h-4" />;
      case 'skipped':
      case 'cancelled': return <X className="w-4 h-4" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      default: return <Bell className="w-4 h-4" />;
    }
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentDate.getMonth();
  };

  if (loading) {
    return <DashboardLoadingModal title="Medication Reminders" subtitle="Loading your reminder schedule..." />;
  }

  if (error) {
    return <DashboardErrorModal title="Medication Reminders" error={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Medication Reminders</h1>
          <p className="text-slate-500 mt-1">Manage your medication schedule and track doses</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowSettingsModal(true)}>
            <Settings className="w-4 h-4 mr-2" />
            Schedules
          </Button>
          <Button variant="primary" size="sm" onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Schedule
          </Button>
        </div>
      </div>

      {/* View Mode Tabs & Navigation */}
      <Card className="p-4">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* View Tabs */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            {(['today', 'week', 'month', 'calendar'] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === mode
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {mode === 'today' && <CalendarDays className="w-4 h-4 inline mr-1" />}
                {mode === 'week' && <List className="w-4 h-4 inline mr-1" />}
                {mode === 'month' && <LayoutGrid className="w-4 h-4 inline mr-1" />}
                {mode === 'calendar' && <Calendar className="w-4 h-4 inline mr-1" />}
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={navigatePrev}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="font-medium text-gray-900 min-w-50 text-center">
                {viewMode === 'today' && currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                {viewMode === 'week' && `Week of ${getViewStartDate().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`}
                {(viewMode === 'month' || viewMode === 'calendar') && currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
              </span>
              <button
                onClick={navigateNext}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            <Button variant="outline" size="sm" onClick={goToToday}>
              Today
            </Button>
          </div>

          {/* Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as ReminderStatusFilter)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="taken">Taken</option>
              <option value="missed">Missed</option>
              <option value="skipped">Skipped</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Calendar Grid View */}
      {viewMode === 'calendar' && (
        <Card className="p-6">
          <div className="grid grid-cols-7 gap-1">
            {/* Day headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {generateCalendarDays().map((date, idx) => {
              const dayReminders = getRemindersForDate(date);
              const hasPending = dayReminders.some(r => r.status === 'pending');
              const hasMissed = dayReminders.some(r => r.status === 'missed');
              const allTaken = dayReminders.length > 0 && dayReminders.every(r => r.status === 'taken');

              return (
                <button
                  key={idx}
                  onClick={() => {
                    setSelectedDate(date);
                    setCurrentDate(date);
                    setViewMode('today');
                  }}
                  className={`
                    min-h-20 p-2 border rounded-lg transition-all text-left
                    ${isCurrentMonth(date) ? 'bg-white' : 'bg-gray-50'}
                    ${isToday(date) ? 'border-blue-500 border-2' : 'border-gray-100'}
                    ${selectedDate?.toDateString() === date.toDateString() ? 'ring-2 ring-blue-300' : ''}
                    hover:border-blue-300
                  `}
                >
                  <div className={`text-sm font-medium ${
                    isToday(date) ? 'text-blue-600' : 
                    isCurrentMonth(date) ? 'text-gray-900' : 'text-gray-400'
                  }`}>
                    {date.getDate()}
                  </div>
                  {dayReminders.length > 0 && (
                    <div className="mt-1 space-y-1">
                      {dayReminders.slice(0, 2).map((r, i) => (
                        <div
                          key={i}
                          className={`text-xs px-1.5 py-0.5 rounded truncate ${getStatusColor(r.status)}`}
                        >
                          {r.medication_name}
                        </div>
                      ))}
                      {dayReminders.length > 2 && (
                        <div className="text-xs text-gray-500">
                          +{dayReminders.length - 2} more
                        </div>
                      )}
                    </div>
                  )}
                  {/* Status indicators */}
                  {dayReminders.length > 0 && (
                    <div className="flex gap-1 mt-1">
                      {hasMissed && <span className="w-2 h-2 rounded-full bg-red-500" />}
                      {hasPending && <span className="w-2 h-2 rounded-full bg-blue-500" />}
                      {allTaken && <span className="w-2 h-2 rounded-full bg-emerald-500" />}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </Card>
      )}

      {/* Today/Week/Month List View */}
      {(viewMode === 'today' || viewMode === 'week' || viewMode === 'month') && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-4">
            {reminders.length === 0 ? (
              <Card className="p-12 text-center">
                <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Reminders</h3>
                <p className="text-gray-500 mb-4">
                  {viewMode === 'today' ? "You don't have any reminders scheduled for today." : "No reminders found for this period."}
                </p>
                <Button variant="primary" onClick={() => setShowCreateModal(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Schedule
                </Button>
              </Card>
            ) : (
              <>
                {/* Group by time period for today view */}
                {viewMode === 'today' ? (
                  Object.entries(groupRemindersByPeriod(reminders)).map(([period, periodReminders]) => {
                    if (periodReminders.length === 0) return null;
                    return (
                      <Card key={period} className="p-4">
                        <h3 className="font-medium text-gray-900 mb-3 capitalize flex items-center gap-2">
                          <span className={`w-3 h-3 rounded-full ${
                            period === 'morning' ? 'bg-amber-400' :
                            period === 'afternoon' ? 'bg-orange-400' :
                            period === 'evening' ? 'bg-purple-400' : 'bg-indigo-400'
                          }`}></span>
                          {period}
                        </h3>
                        <div className="space-y-3">
                          {periodReminders.map(reminder => (
                            <ReminderCard
                              key={reminder.id}
                              reminder={reminder}
                              onMarkTaken={() => markAsTaken(reminder)}
                              onSkip={() => skipReminder(reminder)}
                              getStatusColor={getStatusColor}
                              getStatusIcon={getStatusIcon}
                            />
                          ))}
                        </div>
                      </Card>
                    );
                  })
                ) : (
                  /* List view for week/month */
                  <Card className="divide-y divide-gray-100">
                    {reminders.map(reminder => (
                      <div key={reminder.id} className="p-4">
                        <ReminderCard
                          reminder={reminder}
                          onMarkTaken={() => markAsTaken(reminder)}
                          onSkip={() => skipReminder(reminder)}
                          getStatusColor={getStatusColor}
                          getStatusIcon={getStatusIcon}
                          showDate
                        />
                      </div>
                    ))}
                  </Card>
                )}
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Quick Stats */}
            <Card className="p-4">
              <h3 className="font-medium text-gray-900 mb-4">Summary</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {reminders.filter(r => r.status === 'pending').length}
                  </div>
                  <div className="text-xs text-gray-600">Upcoming</div>
                </div>
                <div className="text-center p-3 bg-emerald-50 rounded-lg">
                  <div className="text-2xl font-bold text-emerald-600">
                    {reminders.filter(r => r.status === 'taken').length}
                  </div>
                  <div className="text-xs text-gray-600">Taken</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {reminders.filter(r => r.status === 'missed').length}
                  </div>
                  <div className="text-xs text-gray-600">Missed</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-600">
                    {reminders.filter(r => r.status === 'skipped' || r.status === 'cancelled').length}
                  </div>
                  <div className="text-xs text-gray-600">Skipped</div>
                </div>
              </div>
            </Card>

            {/* Active Schedules */}
            <Card className="p-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-medium text-gray-900">Active Schedules</h3>
                <button
                  onClick={() => setShowSettingsModal(true)}
                  className="text-blue-600 text-sm hover:underline"
                >
                  Manage
                </button>
              </div>
              <div className="space-y-3">
                {schedules.filter(s => s.is_active).length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No active schedules
                  </p>
                ) : (
                  schedules.filter(s => s.is_active).slice(0, 5).map(schedule => (
                    <div
                      key={schedule.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-sm text-gray-900">
                          {getMedicationName(schedule)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {schedule.reminder_times?.join(', ')}
                        </div>
                      </div>
                      <button
                        onClick={() => toggleSchedule(schedule.id, schedule.is_active)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <BellOff className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Create Schedule Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Reminder Schedule</h2>
            
            <div className="space-y-4">
              {/* Medication Select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Medication
                </label>
                <select
                  value={selectedMedicationId || ''}
                  onChange={(e) => setSelectedMedicationId(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select medication...</option>
                  {medications.map(med => (
                    <option key={med.id} value={med.id}>
                      {med.medication?.name} - {med.dosage}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reminder Times */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reminder Times
                </label>
                {reminderTimes.map((time, idx) => (
                  <div key={idx} className="flex gap-2 mb-2">
                    <input
                      type="time"
                      value={time}
                      onChange={(e) => {
                        const newTimes = [...reminderTimes];
                        newTimes[idx] = e.target.value;
                        setReminderTimes(newTimes);
                      }}
                      className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    {reminderTimes.length > 1 && (
                      <button
                        onClick={() => setReminderTimes(reminderTimes.filter((_, i) => i !== idx))}
                        className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setReminderTimes([...reminderTimes, '12:00'])}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Time
                </Button>
              </div>

              {/* Advance Notice */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notify me before
                </label>
                <select
                  value={advanceMinutes}
                  onChange={(e) => setAdvanceMinutes(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={5}>5 minutes</option>
                  <option value={10}>10 minutes</option>
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                </select>
              </div>

              {/* Channels */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notification Channels
                </label>
                <div className="flex flex-wrap gap-2">
                  {['push', 'email', 'sms', 'whatsapp'].map(channel => (
                    <button
                      key={channel}
                      onClick={() => {
                        if (channels.includes(channel)) {
                          setChannels(channels.filter(c => c !== channel));
                        } else {
                          setChannels([...channels, channel]);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                        channels.includes(channel)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {channel.charAt(0).toUpperCase() + channel.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="ghost" onClick={() => { setShowCreateModal(false); resetForm(); }}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleCreateSchedule}>
                Create Schedule
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Manage Schedules Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Manage Schedules</h2>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {schedules.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No reminder schedules created yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {schedules.map(schedule => (
                  <div
                    key={schedule.id}
                    className={`p-4 rounded-lg border ${schedule.is_active ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900 flex items-center gap-2">
                          <Pill className="w-4 h-4 text-blue-600" />
                          {getMedicationName(schedule)}
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          Times: {schedule.reminder_times?.join(', ') || 'Not set'}
                        </div>
                        <div className="text-sm text-gray-500">
                          Frequency: {schedule.frequency || 'Daily'}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => toggleSchedule(schedule.id, schedule.is_active)}
                          className={`p-2 rounded-lg transition-colors ${
                            schedule.is_active
                              ? 'bg-blue-600 text-white hover:bg-blue-700'
                              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                          }`}
                        >
                          {schedule.is_active ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => deleteSchedule(schedule.id)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end mt-6">
              <Button variant="primary" onClick={() => { setShowSettingsModal(false); setShowCreateModal(true); }}>
                <Plus className="w-4 h-4 mr-2" />
                Add New Schedule
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

// Reminder Card Component
interface ReminderCardProps {
  reminder: CalendarReminder;
  onMarkTaken: () => void;
  onSkip: () => void;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ReactNode;
  showDate?: boolean;
}

const ReminderCard: React.FC<ReminderCardProps> = ({
  reminder,
  onMarkTaken,
  onSkip,
  getStatusColor,
  getStatusIcon,
  showDate = false,
}) => {
  const scheduledTime = new Date(reminder.scheduled_time);
  const isOverdue = scheduledTime < new Date();
  const isPending = reminder.status === 'pending';

  return (
    <div className={`flex items-center justify-between p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow ${isOverdue && isPending ? 'border-amber-200' : 'border-gray-100'}`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${getStatusColor(reminder.status)}`}>
          <Pill className="w-5 h-5" />
        </div>
        <div>
          <div className="font-medium text-gray-900">{reminder.medication_name}</div>
          <div className="text-sm text-gray-500">
            {reminder.dosage}
            {showDate && (
              <span className="ml-2">
                • {scheduledTime.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <div className="text-right">
          <div className="font-medium text-gray-900">
            {scheduledTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </div>
          <div className={`text-xs px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${getStatusColor(reminder.status)}`}>
            {getStatusIcon(reminder.status)}
            {reminder.status.charAt(0).toUpperCase() + reminder.status.slice(1)}
          </div>
        </div>
        
        {isPending && (
          <div className="flex gap-1">
            <button
              onClick={onMarkTaken}
              className="p-2 bg-emerald-100 text-emerald-600 rounded-lg hover:bg-emerald-200 transition-colors"
              title="Mark as taken"
            >
              <Check className="w-4 h-4" />
            </button>
            <button
              onClick={onSkip}
              className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
              title="Skip"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RemindersCalendar;

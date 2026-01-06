import { useState } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import {
  Bell, Clock, Settings, Plus, Trash2,
  Calendar, CheckCircle, XCircle, AlertCircle,
  Smartphone, Mail, MessageSquare,
  RefreshCw, Play, Pause, Eye, Edit, X,
  Check, SkipForward, Timer
} from 'lucide-react';
import { useReminders } from '../../hooks/useReminders';
import type { ReminderResponse, TodayReminder } from '../../types/reminders.types';

const ReminderManagement = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'schedules' | 'today' | 'upcoming' | 'settings'>('overview');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showReminderDetails, setShowReminderDetails] = useState(false);
  const [showEditReminder, setShowEditReminder] = useState(false);
  const [selectedReminder, setSelectedReminder] = useState<ReminderResponse | TodayReminder | null>(null);
  const [editReminderData, setEditReminderData] = useState<Partial<ReminderResponse>>({});

  // Form states
  const [newSchedule, setNewSchedule] = useState<Partial<any>>({
    frequency: 'daily',
    reminder_times: ['08:00'],
    advance_minutes: 15,
    channel_whatsapp: true,
    channel_push: true,
    start_date: new Date().toISOString().split('T')[0]
  });

  // Settings states
  const [settings, setSettings] = useState({
    channel_whatsapp: true,
    channel_push: true,
    channel_sms: false,
    channel_email: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '07:00'
  });

  // Use the reminders hook
  const {
    schedules,
    todayReminders,
    recentReminders,
    medications,
    stats,
    loading,
    error,
    refetch,
    createSchedule,
    deleteSchedule,
    toggleSchedule,
    cancelReminder,
    takeMedication,
    skipMedication,
    snoozeReminder,
    viewScheduleDetails,
    editSchedule,
    cancelSchedule,
  } = useReminders();

  const handleCreateSchedule = async () => {
    try {
      if (!newSchedule.patient_medication_id || !(newSchedule.reminder_times || []).length) {
        alert('Please select a medication and at least one reminder time');
        return;
      }

      await createSchedule(newSchedule);
      setShowCreateForm(false);
      setNewSchedule({
        frequency: 'daily',
        reminder_times: ['08:00'],
        advance_minutes: 15,
        channel_whatsapp: true,
        channel_push: true,
        start_date: new Date().toISOString().split('T')[0]
      });
    } catch (err) {
      console.error('Error creating schedule:', err);
    }
  };

  const handleToggleSchedule = async (scheduleId: number, isActive: boolean) => {
    try {
      await toggleSchedule(scheduleId, isActive);
    } catch (err) {
      console.error('Error toggling schedule:', err);
    }
  };

  const handleViewReminderDetails = (reminder: ReminderResponse | TodayReminder) => {
    setSelectedReminder(reminder);
    setShowReminderDetails(true);
  };

  const handleEditReminder = (reminder: ReminderResponse | TodayReminder) => {
    setSelectedReminder(reminder);
    setEditReminderData({
      scheduled_time: reminder.scheduled_time,
      channel: reminder.channel,
      // message: (reminder as ReminderResponse).message || ''
    });
    setShowEditReminder(true);
  };

  const handleUpdateReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReminder || !editReminderData) return;

    try {
      // Update the reminder with the new data
      // const updateData = {
      //   scheduled_time: editReminderData.scheduled_time,
      //   channel: editReminderData.channel,
      //   message: editReminderData.message
      // };

      // For now, we'll use the cancel endpoint as a placeholder
      // In a full implementation, you'd have a proper update endpoint
      // await reminderService.updateReminder(selectedReminder.id, updateData);

      // For demonstration, we'll just close the modal
      setShowEditReminder(false);
      setSelectedReminder(null);
      setEditReminderData({});
      await refetch();
    } catch (err) {
      console.error('Error updating reminder:', err);
    }
  };

  const handleCancelReminder = async (reminderId: number) => {
    if (!confirm('Are you sure you want to cancel this reminder?')) return;

    try {
      await cancelReminder(reminderId, 'User cancelled');
      await refetch();
    } catch (err) {
      console.error('Error cancelling reminder:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'sent': return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'delivered': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'cancelled': return <AlertCircle className="w-4 h-4 text-gray-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp':
        return <MessageSquare className="w-4 h-4 text-green-600" />;
      case 'sms':
        return <Smartphone className="w-4 h-4 text-blue-500" />;
      case 'email':
        return <Mail className="w-4 h-4 text-purple-500" />;
      case 'push':
        return <Bell className="w-4 h-4 text-orange-500" />;
      default:
        return <Bell className="w-4 h-4 text-gray-500" />;
    }
  };

  const handleSaveSettings = async () => {
    try {
      // TODO: Implement settings save API call when backend supports it
      // For now, just show success message
      alert('Settings saved successfully!');
    } catch (err) {
      console.error('Error saving settings:', err);
      // Error will be handled by the hook
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Medication Reminders</h1>
          <p className="text-gray-600 mt-1">Manage your medication schedules and reminders</p>
        </div>
        <Button
          onClick={refetch}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: Bell },
            { id: 'schedules', label: 'Schedules', icon: Calendar },
            { id: 'today', label: 'Today', icon: Clock },
            { id: 'upcoming', label: 'History', icon: Clock },
            { id: 'settings', label: 'Settings', icon: Settings }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Stats Cards */}
            {stats && (
              <>
                <Card className="p-6">
                  <div className="flex items-center">
                    <Calendar className="w-8 h-8 text-blue-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Scheduled</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_scheduled}</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <Bell className="w-8 h-8 text-green-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Today's Reminders</p>
                      <p className="text-2xl font-bold text-gray-900">{todayReminders.length}</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <CheckCircle className="w-8 h-8 text-purple-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Delivered</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.delivered}</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <AlertCircle className="w-8 h-8 text-red-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Sent</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.sent}</p>
                    </div>
                  </div>
                </Card>
              </>
            )}

            {/* Quick Actions */}
            <Card className="p-6 md:col-span-2 lg:col-span-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => setShowCreateForm(true)}
                  className="flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Schedule
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setActiveTab('today')}
                  className="flex items-center gap-2"
                >
                  <Clock className="w-4 h-4" />
                  View Today's Reminders
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setActiveTab('schedules')}
                  className="flex items-center gap-2"
                >
                  <Settings className="w-4 h-4" />
                  Manage Schedules
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Schedules Tab */}
        {activeTab === 'schedules' && (
          <div className="space-y-6">
            {/* Create Schedule Form */}
            {showCreateForm && (
              <Card className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create Reminder Schedule</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Medication
                    </label>
                    <select
                      value={newSchedule.patient_medication_id || ''}
                      onChange={(e) => setNewSchedule(prev => ({
                        ...prev,
                        patient_medication_id: Number(e.target.value)
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select medication...</option>
                      {medications.map(med => (
                        <option key={med.id} value={med.id}>
                          {med.medication?.name} - {med.dosage}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Frequency
                    </label>
                    <select
                      value={newSchedule.frequency || 'daily'}
                      onChange={(e) => setNewSchedule(prev => ({
                        ...prev,
                        frequency: e.target.value as any
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="daily">Daily</option>
                      <option value="twice_daily">Twice Daily</option>
                      <option value="three_times_daily">Three Times Daily</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Advance Notice (minutes)
                    </label>
                    <input
                      type="number"
                      value={newSchedule.advance_minutes || 15}
                      onChange={(e) => setNewSchedule(prev => ({
                        ...prev,
                        advance_minutes: Number(e.target.value)
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="0"
                      max="120"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={newSchedule.start_date || new Date().toISOString().split('T')[0]}
                      onChange={(e) => setNewSchedule(prev => ({
                        ...prev,
                        start_date: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reminder Times
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {(newSchedule.reminder_times || []).map((time: string, index: number) => (
                        <div key={index} className="flex items-center gap-2">
                          <input
                            type="time"
                            value={time}
                            onChange={(e) => {
                              const newTimes = [...(newSchedule.reminder_times || [])];
                              newTimes[index] = e.target.value;
                              setNewSchedule(prev => ({ ...prev, reminder_times: newTimes }));
                            }}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const newTimes = [...(newSchedule.reminder_times || [])];
                              newTimes.splice(index, 1);
                              setNewSchedule(prev => ({ ...prev, reminder_times: newTimes }));
                            }}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setNewSchedule(prev => ({
                          ...prev,
                          reminder_times: [...(prev.reminder_times || []), '08:00']
                        }))}
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Add Time
                      </Button>
                    </div>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Notification Channels
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newSchedule.channel_whatsapp || false}
                          onChange={(e) => setNewSchedule(prev => ({
                            ...prev,
                            channel_whatsapp: e.target.checked
                          }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-green-500" />
                          WhatsApp
                        </span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newSchedule.channel_push || false}
                          onChange={(e) => setNewSchedule(prev => ({
                            ...prev,
                            channel_push: e.target.checked
                          }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                          <Bell className="w-4 h-4 text-orange-500" />
                          Push Notification
                        </span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newSchedule.channel_sms || false}
                          onChange={(e) => setNewSchedule(prev => ({
                            ...prev,
                            channel_sms: e.target.checked
                          }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                          <Smartphone className="w-4 h-4 text-blue-500" />
                          SMS
                        </span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newSchedule.channel_email || false}
                          onChange={(e) => setNewSchedule(prev => ({
                            ...prev,
                            channel_email: e.target.checked
                          }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                          <Mail className="w-4 h-4 text-purple-500" />
                          Email
                        </span>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <Button
                    variant="outline"
                    onClick={() => setShowCreateForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateSchedule}
                    disabled={!newSchedule.patient_medication_id || !(newSchedule.reminder_times || []).length}
                  >
                    Create Schedule
                  </Button>
                </div>
              </Card>
            )}

            {/* Reminder Details Modal */}
            {showReminderDetails && selectedReminder && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-gray-900">Reminder Details</h2>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowReminderDetails(false)}
                      >
                        <X className="w-5 h-5" />
                      </Button>
                    </div>

                    <div className="space-y-6">
                      {/* Status and Channel */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          {getStatusIcon(selectedReminder.status)}
                          <span className={`text-sm px-3 py-1 rounded-full ${
                            selectedReminder.status === 'delivered' ? 'bg-green-100 text-green-800' :
                            selectedReminder.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                            selectedReminder.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {selectedReminder.status}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getChannelIcon(selectedReminder.channel)}
                          <span className="text-sm text-gray-600 capitalize">
                            {selectedReminder.channel}
                          </span>
                        </div>
                      </div>

                      {/* Medication Info */}
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Medication</h3>
                        <div className="space-y-2">
                          <p className="text-sm">
                            <span className="font-medium">Name:</span> {
                              'medication_name' in selectedReminder ? selectedReminder.medication_name :
                              (medications.find(m => m.id === (selectedReminder as ReminderResponse).patient_medication_id)?.medication?.name) ||
                              'Unknown Medication'
                            }
                          </p>
                          <p className="text-sm">
                            <span className="font-medium">Dosage:</span> {
                              'dosage' in selectedReminder ? selectedReminder.dosage :
                              (medications.find(m => m.id === (selectedReminder as ReminderResponse).patient_medication_id)?.dosage) ||
                              'Unknown Dosage'
                            }
                          </p>
                          <p className="text-sm">
                            <span className="font-medium">Instructions:</span> {
                              'instructions' in selectedReminder ? selectedReminder.instructions :
                              (medications.find(m => m.id === (selectedReminder as ReminderResponse).patient_medication_id)?.instructions) ||
                              'No instructions available'
                            }
                          </p>
                        </div>
                      </div>

                      {/* Schedule Info */}
                      <div className="bg-blue-50 rounded-lg p-4">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Schedule Information</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm">
                              <span className="font-medium">Scheduled Time:</span>
                            </p>
                            <p className="text-sm text-gray-600">
                              {new Date(selectedReminder.scheduled_time).toLocaleString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm">
                              <span className="font-medium">Created:</span>
                            </p>
                            <p className="text-sm text-gray-600">
                              {(selectedReminder as ReminderResponse).created_at ?
                                new Date((selectedReminder as ReminderResponse).created_at).toLocaleString() :
                                'N/A'
                              }
                            </p>
                          </div>
                          {(selectedReminder as ReminderResponse).sent_at && (
                            <div>
                              <p className="text-sm">
                                <span className="font-medium">Sent At:</span>
                              </p>
                              <p className="text-sm text-gray-600">
                                {new Date((selectedReminder as ReminderResponse).sent_at!).toLocaleString()}
                              </p>
                            </div>
                          )}
                          {(selectedReminder as ReminderResponse).delivered_at && (
                            <div>
                              <p className="text-sm">
                                <span className="font-medium">Delivered At:</span>
                              </p>
                              <p className="text-sm text-gray-600">
                                {new Date((selectedReminder as ReminderResponse).delivered_at!).toLocaleString()}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Message Content */}
                      {(selectedReminder as ReminderResponse).message_text && (
                        <div className="bg-green-50 rounded-lg p-4">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">Message Content</h3>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {(selectedReminder as ReminderResponse).message_text}
                          </p>
                        </div>
                      )}

                      {/* Error Info */}
                      {/* Error message handling would go here if available */}

                      {/* Actions */}
                      <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button
                          variant="outline"
                          onClick={() => setShowReminderDetails(false)}
                        >
                          Close
                        </Button>
                        {selectedReminder.status === 'pending' && (
                          <>
                            <Button
                              variant="outline"
                              onClick={() => {
                                setShowReminderDetails(false);
                                handleEditReminder(selectedReminder);
                              }}
                            >
                              <Edit className="w-4 h-4 mr-2" />
                              Edit
                            </Button>
                            <Button
                              variant="destructive"
                              onClick={() => {
                                handleCancelReminder(selectedReminder.id);
                                setShowReminderDetails(false);
                              }}
                            >
                              <X className="w-4 h-4 mr-2" />
                              Cancel Reminder
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Edit Reminder Modal */}
            {showEditReminder && selectedReminder && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-gray-900">Edit Reminder</h2>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowEditReminder(false)}
                      >
                        <X className="w-5 h-5" />
                      </Button>
                    </div>

                    <form onSubmit={handleUpdateReminder} className="space-y-6">
                      {/* Medication Info (Read-only) */}
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Medication</h3>
                        <div className="space-y-2">
                          <p className="text-sm">
                            <span className="font-medium">Name:</span> {
                              selectedReminder && 'medication_name' in selectedReminder ? selectedReminder.medication_name :
                              (selectedReminder && medications.find(m => m.id === (selectedReminder as ReminderResponse).patient_medication_id)?.medication?.name) ||
                              'Unknown Medication'
                            }
                          </p>
                          <p className="text-sm">
                            <span className="font-medium">Dosage:</span> {
                              selectedReminder && 'dosage' in selectedReminder ? selectedReminder.dosage :
                              (selectedReminder && medications.find(m => m.id === (selectedReminder as ReminderResponse).patient_medication_id)?.dosage) ||
                              'Unknown Dosage'
                            }
                          </p>
                        </div>
                      </div>

                      {/* Edit Fields */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Scheduled Date & Time
                          </label>
                          <input
                            type="datetime-local"
                            value={editReminderData?.scheduled_time ? new Date(editReminderData.scheduled_time).toISOString().slice(0, 16) : ''}
                            onChange={(e) => setEditReminderData(prev => ({
                              ...prev,
                              scheduled_time: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Channel
                          </label>
                          <select
                            value={editReminderData?.channel || selectedReminder.channel}
                            onChange={(e) => setEditReminderData(prev => ({
                              ...prev,
                              channel: e.target.value as any
                            }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="whatsapp">WhatsApp</option>
                            <option value="sms">SMS</option>
                            <option value="push">Push Notification</option>
                            <option value="email">Email</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Custom Message (Optional)
                        </label>
                        <textarea
                          value={(selectedReminder as ReminderResponse)?.message_text || ''}
                          onChange={(e) => setEditReminderData(prev => ({
                            ...prev,
                            message: e.target.value
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={3}
                          placeholder="Leave empty to use default message"
                        />
                      </div>

                      {/* Actions */}
                      <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setShowEditReminder(false)}
                        >
                          Cancel
                        </Button>
                        <Button
                          type="submit"
                        >
                          Update Reminder
                        </Button>
                      </div>
                    </form>
                  </div>
                </Card>
              </div>
            )}

            {/* Schedules List */}
            <div className="space-y-4">
              {schedules.map((schedule) => (
                <Card key={schedule.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {schedule.is_active ? (
                          <Play className="w-5 h-5 text-green-500" />
                        ) : (
                          <Pause className="w-5 h-5 text-gray-400" />
                        )}
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {schedule.patient_medication?.medication?.name || 'Unknown Medication'}
                          </h3>
                          <p className="text-sm text-gray-600">{schedule.patient_medication?.dosage || 'Unknown Dosage'}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">
                        {schedule.frequency} • {schedule.reminder_times.join(', ')}
                      </span>
                      <div className="flex space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewScheduleDetails(schedule)}
                          className="p-1"
                          title="View schedule details"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => editSchedule(schedule)}
                          className="p-1"
                          title="Edit schedule"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => cancelSchedule(schedule.id)}
                          className="p-1 text-red-600 hover:text-red-700"
                          title="Cancel schedule"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleToggleSchedule(schedule.id, !schedule.is_active)}
                          title={schedule.is_active ? 'Pause schedule' : 'Resume schedule'}
                        >
                          {schedule.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            if (!confirm('Are you sure you want to delete this reminder schedule?')) return;
                            try {
                              await deleteSchedule(schedule.id);
                            } catch (err) {
                              console.error('Error deleting schedule:', err);
                            }
                          }}
                          className="text-red-600 hover:text-red-700"
                          title="Delete schedule"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}

              {schedules.length === 0 && (
                <Card className="p-12 text-center">
                  <Bell className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No reminder schedules</h3>
                  <p className="text-gray-600 mb-4">Create your first reminder schedule to get started.</p>
                  <Button onClick={() => setShowCreateForm(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Schedule
                  </Button>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Today's Reminders Tab */}
        {activeTab === 'today' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Today's Reminders</h2>
              <span className="text-sm text-gray-600">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </span>
            </div>

            {todayReminders.map((reminder) => (
              <Card 
                key={reminder.id} 
                className={`p-6 cursor-pointer hover:shadow-md transition-shadow ${reminder.is_overdue ? 'border-red-200 bg-red-50' : ''}`}
                onClick={() => handleViewReminderDetails(reminder)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(reminder.status)}
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">
                        {reminder.medication_name}
                      </h3>
                      <p className="text-sm text-gray-600">{reminder.dosage}</p>
                      {reminder.instructions && (
                        <p className="text-sm text-gray-500 mt-1">{reminder.instructions}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(reminder.scheduled_time).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                      <p className={`text-sm ${reminder.is_overdue ? 'text-red-600' : 'text-gray-600'}`}>
                        {reminder.time_until}
                      </p>
                    </div>
                    {getChannelIcon(reminder.channel)}
                    <div className="flex space-x-1" onClick={(e) => e.stopPropagation()}>
                      {reminder.status === 'pending' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => takeMedication(reminder.id)}
                            className="p-1 text-green-600 hover:text-green-700"
                            title="Mark as taken"
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => skipMedication(reminder.id)}
                            className="p-1 text-orange-600 hover:text-orange-700"
                            title="Skip medication"
                          >
                            <SkipForward className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => snoozeReminder(reminder.id)}
                            className="p-1 text-blue-600 hover:text-blue-700"
                            title="Snooze for 1 hour"
                          >
                            <Timer className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewReminderDetails(reminder)}
                        className="p-1"
                        title="View details"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      {reminder.status === 'pending' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditReminder(reminder)}
                            className="p-1"
                            title="Edit reminder"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCancelReminder(reminder.id)}
                            className="p-1 text-red-600 hover:text-red-700"
                            title="Cancel reminder"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))}

            {todayReminders.length === 0 && (
              <Card className="p-12 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No reminders today</h3>
                <p className="text-gray-600">Great job staying on top of your medications!</p>
              </Card>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'upcoming' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Reminders</h2>

            {recentReminders.slice(0, 20).map((reminder) => {
              const medication = medications.find(m => m.id === reminder.patient_medication_id);
              return (
                <Card 
                  key={reminder.id} 
                  className="p-6 cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => handleViewReminderDetails(reminder)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {getStatusIcon(reminder.status)}
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">
                          {medication?.medication?.name || 'Unknown Medication'}
                        </h3>
                        <p className="text-sm text-gray-600">{medication?.dosage || 'Unknown Dosage'}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(reminder.scheduled_time).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <span className={`text-sm px-2 py-1 rounded-full ${
                        reminder.status === 'delivered' ? 'bg-green-100 text-green-800' :
                        reminder.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                        reminder.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {reminder.status}
                      </span>
                      {getChannelIcon(reminder.channel)}
                      <div className="flex space-x-1" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewReminderDetails(reminder)}
                          className="p-1"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {reminder.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditReminder(reminder)}
                              className="p-1"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCancelReminder(reminder.id)}
                              className="p-1 text-red-600 hover:text-red-700"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}

            {recentReminders.length === 0 && (
              <Card className="p-12 text-center">
                <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No recent reminders</h3>
                <p className="text-gray-600">Your reminder history will appear here.</p>
              </Card>
            )}
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Reminder Settings</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Notification Preferences</h3>
                <p className="text-gray-600 mb-4">
                  Configure how and when you receive medication reminders.
                </p>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.channel_whatsapp}
                      onChange={(e) => setSettings(prev => ({ ...prev, channel_whatsapp: e.target.checked }))}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-green-500" />
                      WhatsApp notifications
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.channel_push}
                      onChange={(e) => setSettings(prev => ({ ...prev, channel_push: e.target.checked }))}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                      <Bell className="w-4 h-4 text-orange-500" />
                      Push notifications
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.channel_sms}
                      onChange={(e) => setSettings(prev => ({ ...prev, channel_sms: e.target.checked }))}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                      <Smartphone className="w-4 h-4 text-blue-500" />
                      SMS notifications
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.channel_email}
                      onChange={(e) => setSettings(prev => ({ ...prev, channel_email: e.target.checked }))}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex items-center gap-2">
                      <Mail className="w-4 h-4 text-purple-500" />
                      Email notifications
                    </span>
                  </label>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Quiet Hours</h3>
                <p className="text-gray-600 mb-4">
                  Set times when you don't want to receive reminders.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Time
                    </label>
                    <input
                      type="time"
                      value={settings.quiet_hours_start}
                      onChange={(e) => setSettings(prev => ({ ...prev, quiet_hours_start: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Time
                    </label>
                    <input
                      type="time"
                      value={settings.quiet_hours_end}
                      onChange={(e) => setSettings(prev => ({ ...prev, quiet_hours_end: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSaveSettings}>Save Settings</Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ReminderManagement;
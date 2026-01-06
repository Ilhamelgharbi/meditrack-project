import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import {
  Bell, Clock, Eye, Calendar,
  CheckCircle, XCircle
} from 'lucide-react';
import { reminderService } from '../../services/reminder.service';
import { formatInUserTimezone } from '../../utils/timezone';
import type { ReminderScheduleResponse, ReminderResponse } from '../../types/reminders.types';

const SimpleTablesPage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [schedules, setSchedules] = useState<ReminderScheduleResponse[]>([]);
  const [reminders, setReminders] = useState<ReminderResponse[]>([]);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    if (!user) return;

    try {
      setLoading(true);

      // Fetch reminder schedules
      const schedulesData = await reminderService.getReminderSchedules();
      setSchedules(schedulesData);

      // Fetch reminders
      const remindersData = await reminderService.getReminders({
        limit: 200
      });
      setReminders(remindersData);

    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
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
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reminder Tables</h1>
          <p className="text-gray-600 mt-1">Raw data from reminder_schedules and reminders tables</p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <Eye className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Reminder Schedules Table */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Reminder Schedules Table</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient Med ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Active</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Frequency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Times</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Advance Min</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Channels</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {schedules.map((schedule) => (
                <tr key={schedule.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{schedule.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{schedule.patient_medication_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{schedule.patient_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {schedule.is_active ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{schedule.frequency}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {schedule.reminder_times.join(', ')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{schedule.advance_minutes}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {[
                      schedule.channel_push && 'Push',
                      schedule.channel_email && 'Email',
                      schedule.channel_sms && 'SMS',
                      schedule.channel_whatsapp && 'WhatsApp'
                    ].filter(Boolean).join(', ') || 'None'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatInUserTimezone(schedule.start_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {schedule.end_date ? formatInUserTimezone(schedule.end_date) : 'None'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {schedules.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No reminder schedules found
          </div>
        )}
      </Card>

      {/* Reminders Table */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Reminders Table</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Schedule ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scheduled Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Channels</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sent At</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reminders.map((reminder) => (
                <tr key={reminder.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{reminder.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{reminder.patient_medication_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {reminder.scheduled_time ? formatInUserTimezone(reminder.scheduled_time) : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      reminder.status === 'sent' ? 'bg-green-100 text-green-800' :
                      reminder.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      reminder.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {reminder.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {reminder.channel}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {reminder.sent_at ? formatInUserTimezone(reminder.sent_at) : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate">
                    {reminder.message_text || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {reminders.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No reminders found
          </div>
        )}
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center">
            <Calendar className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Total Schedules</p>
              <p className="text-2xl font-bold">{schedules.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <Bell className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Active Schedules</p>
              <p className="text-2xl font-bold">{schedules.filter(s => s.is_active).length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-purple-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Total Reminders</p>
              <p className="text-2xl font-bold">{reminders.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-orange-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Delivered Reminders</p>
              <p className="text-2xl font-bold">{reminders.filter(r => r.status === 'delivered').length}</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SimpleTablesPage;
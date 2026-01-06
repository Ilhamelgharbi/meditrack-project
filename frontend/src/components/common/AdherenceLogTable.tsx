// src/components/common/AdherenceLogTable.tsx
import React, { useState } from 'react';
import { Card } from './Card';
import {
  CheckCircle, Clock, XCircle, Loader, Activity,
  Edit, Trash2, Search
} from 'lucide-react';

interface MedicationLog {
  id: number;
  medication_name?: string;
  dosage?: string;
  scheduled_time: string;
  actual_time?: string;
  status: string;
  notes?: string;
  created_at?: string;
  patient_medication_id?: number;
}

interface AdherenceLogTableProps {
  logs: MedicationLog[];
  title?: string;
  subtitle?: string;
  className?: string;
  showFilters?: boolean;
  showActions?: boolean;
  onEdit?: (log: MedicationLog) => void;
  onDelete?: (log: MedicationLog) => void;
  loading?: boolean;
}

export const AdherenceLogTable: React.FC<AdherenceLogTableProps> = ({
  logs,
  title = "Medication Logs History",
  subtitle = "Complete history of your medication doses",
  className = '',
  showFilters = true,
  showActions = false,
  onEdit,
  onDelete,
  loading = false
}) => {
  const [statusFilter, setStatusFilter] = useState<'all' | 'taken' | 'skipped' | 'missed'>('all');
  const [medicationFilter, setMedicationFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredLogs = logs.filter((log) => {
    const matchesSearch = log.medication_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.dosage?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || log.status === statusFilter;
    const matchesMedication = medicationFilter === 'all' || log.patient_medication_id?.toString() === medicationFilter;
    return matchesSearch && matchesStatus && matchesMedication;
  });

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'taken':
        return { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Taken' };
      case 'skipped':
        return { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50', label: 'Skipped' };
      case 'missed':
        return { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: 'Missed' };
      default:
        return { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-50', label: 'Unknown' };
    }
  };

  const uniqueMedications = Array.from(
    new Set(logs.map(log => log.patient_medication_id).filter(Boolean))
  );

  if (loading) {
    return (
      <Card variant="elevated" className={className}>
        <div className="flex items-center justify-center h-64">
          <Loader className="animate-spin text-primary-600" size={32} />
        </div>
      </Card>
    );
  }

  return (
    <Card variant="elevated" className={className}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Activity className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            <p className="text-sm text-gray-600">{subtitle}</p>
          </div>
        </div>
      </div>

      {showFilters && (
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search medications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="taken">Taken</option>
            <option value="skipped">Skipped</option>
            <option value="missed">Missed</option>
          </select>
          {uniqueMedications.length > 1 && (
            <select
              value={medicationFilter}
              onChange={(e) => setMedicationFilter(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Medications</option>
              {uniqueMedications.map((medId) => {
                const log = logs.find(l => l.patient_medication_id === medId);
                return (
                  <option key={medId} value={medId?.toString()}>
                    {log?.medication_name} - {log?.dosage}
                  </option>
                );
              })}
            </select>
          )}
        </div>
      )}

      {filteredLogs.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="mx-auto text-gray-300 mb-4" size={48} />
          <p className="text-gray-600 mb-2">No medication logs found</p>
          <p className="text-sm text-gray-500">
            {logs.length === 0 ? 'Start by logging your first dose' : 'Try adjusting your filters'}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Medication</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scheduled Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
                {showActions && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredLogs.map((log) => {
                const statusConfig = getStatusConfig(log.status);
                const StatusIcon = statusConfig.icon;

                return (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{log.medication_name || 'Unknown'}</p>
                        <p className="text-xs text-gray-500">{log.dosage}</p>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.scheduled_time).toLocaleString()}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.actual_time ? new Date(log.actual_time).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}>
                        <StatusIcon size={12} />
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-900 max-w-xs truncate">
                      {log.notes || '-'}
                    </td>
                    {showActions && (
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          {onEdit && (
                            <button
                              onClick={() => onEdit(log)}
                              className="text-primary-600 hover:text-primary-800 p-1 rounded"
                              title="Edit"
                            >
                              <Edit size={16} />
                            </button>
                          )}
                          {onDelete && (
                            <button
                              onClick={() => onDelete(log)}
                              className="text-red-600 hover:text-red-800 p-1 rounded"
                              title="Delete"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};
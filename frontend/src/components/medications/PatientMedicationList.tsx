import React, { useState, useMemo } from 'react';
import { CheckCircle, StopCircle, Pill } from 'lucide-react';
import type { MedicationListProps } from './types';
import { PatientMedicationCard } from './PatientMedicationCard';
import { MedicationSearchFilter } from './MedicationSearchFilter';
import { MedicationLoadingState } from './MedicationLoadingState';
import { MedicationEmptyState } from './MedicationEmptyState';
import { MedicationDashboardStats } from './MedicationDashboardStats';
import type { PatientMedicationDetailed } from '../../types/medications.types';
import { Card } from '../common/Card';

interface PatientMedicationListProps extends Omit<MedicationListProps, 'onEdit' | 'onDelete'> {
  onActivate?: (medication: PatientMedicationDetailed) => void;
}

export const PatientMedicationList: React.FC<PatientMedicationListProps> = ({
  medications,
  onView,
  onActivate,
  loading = false,
  showActions = true,
  compact = false,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'pending' | 'stopped'>('all');

  // Separate stopped medications
  const stoppedMedications = useMemo(() => {
    return medications.filter(med => med.status === 'stopped');
  }, [medications]);

  const filteredMedications = useMemo(() => {
    const medsToFilter = statusFilter === 'stopped' ? stoppedMedications : 
                         statusFilter === 'all' ? medications : 
                         medications.filter(m => m.status === statusFilter);
    
    return medsToFilter.filter(med => {
      const matchesSearch = med.medication?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           med.dosage?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           false;
      return matchesSearch;
    });
  }, [medications, stoppedMedications, searchTerm, statusFilter]);

  // When showing 'all', split into active/pending and stopped
  const showSeparateSections = statusFilter === 'all';
  const filteredActive = useMemo(() => {
    if (!showSeparateSections) return [];
    return filteredMedications.filter(m => m.status === 'active' || m.status === 'pending');
  }, [filteredMedications, showSeparateSections]);

  const filteredStopped = useMemo(() => {
    if (!showSeparateSections) return [];
    return filteredMedications.filter(m => m.status === 'stopped');
  }, [filteredMedications, showSeparateSections]);

  const statusCounts = useMemo(() => {
    return {
      all: medications.length,
      active: medications.filter(m => m.status === 'active').length,
      pending: medications.filter(m => m.status === 'pending').length,
      stopped: medications.filter(m => m.status === 'stopped').length,
    };
  }, [medications]);

  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(status as 'all' | 'active' | 'pending' | 'stopped');
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Dashboard Statistics */}
      <MedicationDashboardStats
        total={statusCounts.all}
        active={statusCounts.active}
        pending={statusCounts.pending}
        stopped={statusCounts.stopped}
      />

      {/* Search and Filter Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
        <MedicationSearchFilter
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          statusFilter={statusFilter}
          onStatusFilterChange={handleStatusFilterChange}
          placeholder="Search by name or dosage..."
        />
      </div>

      {/* Loading State */}
      {loading && (
        <MedicationLoadingState />
      )}

      {/* Medications Display */}
      {!loading && showSeparateSections ? (
        <>
          {/* Active & Pending Medications Section */}
          <Card>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Pill size={20} className="text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Active Medications</h3>
                <p className="text-sm text-slate-500">{filteredActive.length} medication{filteredActive.length !== 1 ? 's' : ''}</p>
              </div>
            </div>
            
            {filteredActive.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredActive.map((medication) => (
                  <PatientMedicationCard
                    key={medication.id}
                    medication={medication}
                    onView={onView}
                    onActivate={onActivate}
                    showActions={showActions}
                    compact={compact}
                    className="h-full"
                  />
                ))}
              </div>
            ) : (
              <MedicationEmptyState
                title="No active medications"
                message={searchTerm ? 'Try adjusting your search terms' : 'Your active medications will appear here'}
                icon={CheckCircle}
              />
            )}
          </Card>

          {/* Stopped Medications Section */}
          {(filteredStopped.length > 0 || stoppedMedications.length > 0) && (
            <Card>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                  <StopCircle size={20} className="text-slate-500" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Stopped Medications</h3>
                  <p className="text-sm text-slate-500">{filteredStopped.length} medication{filteredStopped.length !== 1 ? 's' : ''} no longer active</p>
                </div>
              </div>
              
              {filteredStopped.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredStopped.map((medication) => (
                    <PatientMedicationCard
                      key={medication.id}
                      medication={medication}
                      onView={onView}
                      showActions={showActions}
                      compact={compact}
                      className="h-full opacity-75"
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 text-center py-4">No stopped medications match your search</p>
              )}
            </Card>
          )}
        </>
      ) : !loading && (
        /* Single filtered view */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedications.map((medication) => (
            <PatientMedicationCard
              key={medication.id}
              medication={medication}
              onView={onView}
              onActivate={onActivate}
              showActions={showActions}
              compact={compact}
              className="h-full"
            />
          ))}

          {filteredMedications.length === 0 && (
            <div className="col-span-full">
              <MedicationEmptyState
                title={statusFilter === 'pending' ? 'No pending medications' : statusFilter === 'active' ? 'No active medications' : statusFilter === 'stopped' ? 'No stopped medications' : 'No medications found'}
                message={searchTerm ? 'Try adjusting your search terms' : 'Your medications will appear here once prescribed'}
                icon={CheckCircle}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
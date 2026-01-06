import React, { useState, useMemo } from 'react';
import { Search, Filter } from 'lucide-react';
import type { AdminMedicationListProps } from './types';
import { AdminMedicationCard } from './AdminMedicationCard';

export const AdminMedicationList: React.FC<AdminMedicationListProps> = ({
  medications,
  onView,
  onEdit,
  onDelete,
  loading = false,
  emptyMessage = 'No medications found',
  showActions = true,
  compact = false,
  searchTerm = '',
  onSearchChange,
  className = ''
}) => {
  const [localSearchTerm, setLocalSearchTerm] = useState(searchTerm);
  const [selectedForm, setSelectedForm] = useState<string>('all');

  // Handle search term changes
  const handleSearchChange = (term: string) => {
    setLocalSearchTerm(term);
    onSearchChange?.(term);
  };

  // Filter medications based on search term and form
  const filteredMedications = useMemo(() => {
    return medications.filter(medication => {
      const matchesSearch = medication.name.toLowerCase().includes(localSearchTerm.toLowerCase()) ||
                           medication.form.toLowerCase().includes(localSearchTerm.toLowerCase()) ||
                           (medication.default_dosage && medication.default_dosage.toLowerCase().includes(localSearchTerm.toLowerCase()));

      const matchesForm = selectedForm === 'all' || medication.form === selectedForm;

      return matchesSearch && matchesForm;
    });
  }, [medications, localSearchTerm, selectedForm]);

  // Get unique forms for filter dropdown
  const availableForms = useMemo(() => {
    const forms = [...new Set(medications.map(med => med.form))];
    return forms.sort();
  }, [medications]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-10 bg-slate-200 rounded-lg w-80 animate-pulse"></div>
          <div className="h-10 bg-slate-200 rounded-lg w-32 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 animate-pulse">
              <div className="h-24 bg-slate-200 rounded-lg mb-4"></div>
              <div className="h-4 bg-slate-200 rounded mb-2"></div>
              <div className="h-3 bg-slate-200 rounded mb-4"></div>
              <div className="flex gap-2">
                <div className="h-8 bg-slate-200 rounded flex-1"></div>
                <div className="h-8 bg-slate-200 rounded flex-1"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Search and Filter Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-4 flex-1">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search medications..."
              value={localSearchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>

          {/* Form Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <select
              value={selectedForm}
              onChange={(e) => setSelectedForm(e.target.value)}
              className="pl-9 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors appearance-none bg-white"
            >
              <option value="all">All Forms</option>
              {availableForms.map(form => (
                <option key={form} value={form} className="capitalize">{form}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Results Count */}
        <div className="text-sm text-slate-600">
          {filteredMedications.length} of {medications.length} medications
        </div>
      </div>

      {/* Medications Grid */}
      {filteredMedications.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedications.map((medication) => (
            <AdminMedicationCard
              key={medication.id}
              medication={medication}
              onView={onView}
              onEdit={onEdit}
              onDelete={onDelete}
              showActions={showActions}
              compact={compact}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No medications found</h3>
          <p className="text-slate-600 max-w-md mx-auto">
            {localSearchTerm || selectedForm !== 'all'
              ? 'Try adjusting your search terms or filters.'
              : emptyMessage
            }
          </p>
          {(localSearchTerm || selectedForm !== 'all') && (
            <button
              onClick={() => {
                setLocalSearchTerm('');
                setSelectedForm('all');
                handleSearchChange('');
              }}
              className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </div>
  );
};
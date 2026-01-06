// src/components/medications/MedicationSearchFilter.tsx
import React from 'react';
import { Search, Filter } from 'lucide-react';

interface MedicationSearchFilterProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  statusFilter?: string;
  onStatusFilterChange?: (status: string) => void;
  availableStatuses?: string[];
  placeholder?: string;
  className?: string;
}

export const MedicationSearchFilter: React.FC<MedicationSearchFilterProps> = ({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  availableStatuses = ['all', 'active', 'pending', 'stopped'],
  placeholder = 'Search medications...',
  className = ''
}) => {
  return (
    <div className={`flex flex-col sm:flex-row gap-4 ${className}`}>
      {/* Search Input */}
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
        <input
          type="text"
          placeholder={placeholder}
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white"
        />
      </div>

      {/* Status Filter */}
      {onStatusFilterChange && (
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="pl-10 pr-8 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white appearance-none cursor-pointer"
          >
            {availableStatuses.map((status) => (
              <option key={status} value={status}>
                {status === 'all' ? 'All Status' : status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};
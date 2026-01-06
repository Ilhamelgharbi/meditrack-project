import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Pill, Plus, Eye, Clock, Calendar, RotateCcw } from 'lucide-react';

export interface SimpleMedicationData {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'pending' | 'completed';
  dosage?: string;
  timesPerDay?: number;
  startDate?: string;
  instructions?: string;
}

interface SimpleMedicationListProps {
  medications: SimpleMedicationData[];
  onAddMedication?: () => void;
  onEditMedication?: (medication: SimpleMedicationData) => void;
  onStopMedication?: (medication: SimpleMedicationData) => void;
  onViewDetails?: (medication: SimpleMedicationData) => void;
  onReactivateMedication?: (medication: SimpleMedicationData) => void;
  showActions?: boolean;
  title?: string;
}

export const SimpleMedicationList: React.FC<SimpleMedicationListProps> = ({
  medications,
  onAddMedication,
  onEditMedication,
  onStopMedication,
  onViewDetails,
  onReactivateMedication,
  showActions = true,
  title = "Active Medications"
}) => {
  if (!medications || medications.length === 0) {
    return (
      <Card title={title}>
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Pill size={32} className="text-slate-400" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 mb-2">No Medications Found</h3>
          <p className="text-slate-500 mb-6 max-w-md mx-auto">
            {title.toLowerCase().includes('active')
              ? "This patient has no active medication prescriptions."
              : "This patient has no medications in this category."
            }
          </p>
          {showActions && onAddMedication && title.toLowerCase().includes('active') && (
            <Button leftIcon={<Plus size={18} />} onClick={onAddMedication} className="bg-blue-600 hover:bg-blue-700">
              Add First Medication
            </Button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card title={title}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {medications.map((medication, index) => (
          <div
            key={medication.id || index}
            className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            {/* Header with icon and status */}
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <Pill size={24} className="text-blue-600" />
              </div>
              <span className={`px-2 py-1 text-xs font-bold rounded-full border ${
                medication.status === 'active'
                  ? 'bg-green-100 text-green-700 border-green-200'
                  : medication.status === 'inactive'
                  ? 'bg-red-100 text-red-700 border-red-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}>
                {medication.status.toUpperCase()}
              </span>
            </div>

            {/* Medication Name */}
            <h4 className="font-semibold text-slate-900 mb-2 text-lg leading-tight">
              {medication.name}
            </h4>

            {/* Key Information */}
            <div className="space-y-2 mb-4">
              {medication.dosage && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Pill size={14} className="text-slate-400" />
                  <span>{medication.dosage}</span>
                </div>
              )}

              {medication.timesPerDay && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Clock size={14} className="text-slate-400" />
                  <span>{medication.timesPerDay} times daily</span>
                </div>
              )}

              {medication.startDate && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Calendar size={14} className="text-slate-400" />
                  <span>Started {new Date(medication.startDate).toLocaleDateString()}</span>
                </div>
              )}
            </div>

            {/* Instructions (truncated) */}
            {medication.instructions && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-blue-800 overflow-hidden" style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical' as const
                }}>
                  {medication.instructions}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            {showActions && (
              <div className="flex gap-2 pt-2 border-t border-slate-100">
                {onViewDetails && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    onClick={() => onViewDetails(medication)}
                  >
                    <Eye size={14} className="mr-1" />
                    View
                  </Button>
                )}
                <div className="flex gap-1">
                  {onEditMedication && medication.status !== 'inactive' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-slate-600 hover:text-slate-700 hover:bg-slate-50"
                      onClick={() => onEditMedication(medication)}
                    >
                      Edit
                    </Button>
                  )}
                  {onReactivateMedication && medication.status === 'inactive' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-green-600 hover:text-green-700 hover:bg-green-50"
                      onClick={() => onReactivateMedication(medication)}
                    >
                      <RotateCcw size={14} className="mr-1" />
                      Reactivate
                    </Button>
                  )}
                  {onStopMedication && medication.status === 'active' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => onStopMedication(medication)}
                    >
                      Stop
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};
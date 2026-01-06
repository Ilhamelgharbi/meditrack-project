import React from 'react';
import { AlertCircle, Heart, Activity, Scissors, Stethoscope, Plus, Edit2 } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface MedicalHistoryCardProps {
  medicalHistory: {
    allergies: string;
    heartConditions: string;
    conditions: string;
    surgeries: string;
    chronicDiseases: string;
  };
  onUpdateClick?: () => void;
}

export const MedicalHistoryCard: React.FC<MedicalHistoryCardProps> = ({
  medicalHistory,
  onUpdateClick
}) => {
  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">Medical History</h3>
          {onUpdateClick && (
            <Button variant="ghost" className="text-blue-600 text-sm h-8" onClick={onUpdateClick}>
              <Edit2 size={14} className="mr-2"/> Update
            </Button>
          )}
        </div>
        <div className="space-y-6">
        {/* Allergies */}
        <div>
          <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 mb-3">
            <AlertCircle size={16} className="text-amber-500" />
            Allergies
          </h4>
          <div className="flex flex-wrap gap-2">
            {medicalHistory.allergies.split(',').map((allergy, i) => (
              <span key={i} className="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-sm font-medium border border-amber-100">
                {allergy.trim()}
              </span>
            ))}
            <button className="w-8 h-8 rounded-full border border-dashed border-slate-300 flex items-center justify-center text-slate-400 hover:border-blue-400 hover:text-blue-500 transition-colors">
              <Plus size={14} />
            </button>
          </div>
        </div>

        <div className="w-full h-px bg-slate-100"></div>

        {/* Conditions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 mb-3">
              <Heart size={16} className="text-red-500" />
              Heart Conditions
            </h4>
            <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
              {medicalHistory.heartConditions}
            </p>
          </div>
          <div>
            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 mb-3">
              <Activity size={16} className="text-blue-500" />
              Asthma / Respiratory
            </h4>
            <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
              {medicalHistory.conditions}
            </p>
          </div>
          <div>
            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 mb-3">
              <Scissors size={16} className="text-slate-500" />
              Surgeries
            </h4>
            <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
              {medicalHistory.surgeries}
            </p>
          </div>
          <div>
            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 mb-3">
              <Stethoscope size={16} className="text-emerald-500" />
              Chronic Diseases
            </h4>
            <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
              {medicalHistory.chronicDiseases}
            </p>
          </div>
        </div>
        </div>
      </div>
    </Card>
  );
};

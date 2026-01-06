import React from 'react';
import { Calendar, Weight, Ruler, Droplet, Brain } from 'lucide-react';
import { Card } from '../common/Card';

interface VitalsCardProps {
  vitals: {
    age: string;
    weight: string;
    height: string;
    bloodType: string;
  };
}

export const VitalsCard: React.FC<VitalsCardProps> = ({ vitals }) => {
  return (
    <Card title="Personal Vitals">
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-2 mb-2 text-slate-400">
            <Calendar size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Age</span>
          </div>
          <p className="text-xl font-bold text-slate-900">{vitals.age} <span className="text-xs font-normal text-slate-500">yrs</span></p>
        </div>
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-2 mb-2 text-slate-400">
            <Weight size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Weight</span>
          </div>
          <p className="text-xl font-bold text-slate-900">{vitals.weight} <span className="text-xs font-normal text-slate-500">kg</span></p>
        </div>
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-2 mb-2 text-slate-400">
            <Ruler size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Height</span>
          </div>
          <p className="text-xl font-bold text-slate-900">{vitals.height} <span className="text-xs font-normal text-slate-500">cm</span></p>
        </div>
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-2 mb-2 text-slate-400">
            <Droplet size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Blood</span>
          </div>
          <p className="text-xl font-bold text-slate-900">{vitals.bloodType}</p>
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-100">
        <div className="flex items-start gap-3">
          <Brain size={20} className="text-blue-600 mt-1" />
          <div>
            <h4 className="text-sm font-bold text-blue-900">RAG Context Active</h4>
            <p className="text-xs text-blue-700 mt-1 leading-relaxed">
              This data helps your AI Assistant provide personalized medical advice and accurate health monitoring.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

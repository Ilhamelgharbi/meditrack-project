import React from 'react';
import { FileText, Upload, Download, X } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface MedicalReport {
  id: number;
  name: string;
  date: string;
  type: string;
  size: string;
}

interface MedicalReportsCardProps {
  reports: MedicalReport[];
  onUploadClick?: () => void;
  onDeleteReport?: (id: number) => void;
}

export const MedicalReportsCard: React.FC<MedicalReportsCardProps> = ({
  reports,
  onUploadClick,
  onDeleteReport
}) => {
  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Medical Reports</h3>
            <p className="text-sm text-slate-500">Upload new reports to update your AI health context</p>
          </div>
          {onUploadClick && (
            <Button leftIcon={<Upload size={16} />} className="h-9 text-sm px-4" onClick={onUploadClick}>
              Upload Report
            </Button>
          )}
        </div>
        <div className="space-y-3">
        {reports.map((report) => (
          <div key={report.id} className="flex items-center justify-between p-4 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-slate-50 transition-all group">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-red-50 text-red-500 flex items-center justify-center">
                <FileText size={20} />
              </div>
              <div>
                <p className="font-bold text-slate-900 text-sm">{report.name}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                  <span>{report.date}</span>
                  <span>•</span>
                  <span>{report.type}</span>
                  <span>•</span>
                  <span>{report.size}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 text-slate-400 hover:text-blue-600 hover:bg-white rounded-lg transition-colors">
                <Download size={18} />
              </button>
              {onDeleteReport && (
                <button
                  onClick={() => onDeleteReport(report.id)}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-white rounded-lg transition-colors"
                >
                  <X size={18} />
                </button>
              )}
            </div>
          </div>
        ))}
        </div>
      </div>
    </Card>
  );
};

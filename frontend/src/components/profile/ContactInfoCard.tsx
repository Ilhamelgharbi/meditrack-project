import React from 'react';
import { Mail, Smartphone } from 'lucide-react';
import { Card } from '../common/Card';

interface ContactInfoCardProps {
  email: string;
  phone?: string;
}

export const ContactInfoCard: React.FC<ContactInfoCardProps> = ({ email, phone }) => {
  return (
    <Card title="Contact Information">
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors">
          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
            <Mail size={18} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Email Address</p>
            <p className="text-sm font-semibold text-slate-900">{email}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors">
          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
            <Smartphone size={18} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Phone Number</p>
            <p className="text-sm font-semibold text-slate-900">{phone || '+1 (555) 000-0000'}</p>
          </div>
        </div>
      </div>
    </Card>
  );
};

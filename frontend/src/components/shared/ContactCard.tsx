import React from 'react';
import {Card} from '../common/Card';

export interface ContactItem {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  value: string;
  color?: string;
}

interface ContactCardProps {
  title?: string;
  contacts: ContactItem[];
  className?: string;
}

export const ContactCard: React.FC<ContactCardProps> = ({
  title = "Contact Information",
  contacts,
  className = ''
}) => {
  return (
    <Card title={title} className={className}>
      <div className="space-y-4">
        {contacts.map((contact, index) => (
          <div key={index} className="flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors">
            <div className={`w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 ${contact.color || ''}`}>
              <contact.icon size={18} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">{contact.label}</p>
              <p className="text-sm font-semibold text-slate-900">{contact.value}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
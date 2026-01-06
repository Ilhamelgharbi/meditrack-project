// src/components/common/Card.tsx
import type { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
  title?: string;
  subtitle?: string;
}

export const Card = ({ 
  children, 
  variant = 'default', 
  title,
  subtitle,
  className = '', 
  ...props 
}: CardProps) => {
  const variants = {
    default: 'bg-white rounded-xl',
    bordered: 'bg-white border-2 border-gray-200 rounded-xl',
    elevated: 'bg-white rounded-xl shadow-lg',
  };

  return (
    <div 
      className={`${variants[variant]} ${className}`}
      {...props}
    >
      {title && (
        <div className="p-6 pb-0">
          <h3 className="text-lg font-semibold text-slate-900 mb-1">{title}</h3>
          {subtitle && <p className="text-sm text-slate-600">{subtitle}</p>}
        </div>
      )}
      <div className={title ? 'p-6 pt-4' : 'p-6'}>
        {children}
      </div>
    </div>
  );
};
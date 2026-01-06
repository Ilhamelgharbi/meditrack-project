// src/components/medications/MedicationImage.tsx
import React from 'react';
import { Pill } from 'lucide-react';
import type { MedicationImageProps } from './types';

const sizeClasses = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
  xl: 'w-20 h-20'
};

export const MedicationImage: React.FC<MedicationImageProps> = ({
  src,
  alt,
  size = 'md',
  className = '',
  fallbackIcon: FallbackIcon = Pill
}) => {
  const sizeClass = sizeClasses[size];

  if (src) {
    return (
      <img
        src={src}
        alt={alt}
        className={`${sizeClass} rounded-lg object-cover ${className}`}
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const parent = target.parentElement;
          if (parent) {
            const fallback = parent.querySelector('.fallback-icon') as HTMLElement;
            if (fallback) fallback.style.display = 'flex';
          }
        }}
      />
    );
  }

  return (
    <div className={`${sizeClass} rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center ${className} fallback-icon`}>
      <FallbackIcon size={size === 'sm' ? 16 : size === 'md' ? 20 : size === 'lg' ? 24 : 28} className="text-blue-400" />
    </div>
  );
};
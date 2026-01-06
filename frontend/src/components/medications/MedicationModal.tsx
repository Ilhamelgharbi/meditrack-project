// UNUSED COMPONENT - This component is not used anywhere in the codebase
// src/components/medications/MedicationModal.tsx
import React from 'react';
import { X } from 'lucide-react';
import { MedicationImage } from './MedicationImage';

interface MedicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  image?: {
    src?: string;
    alt: string;
  };
  children: React.ReactNode;
  actions?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl'
};

export const MedicationModal: React.FC<MedicationModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  image,
  children,
  actions,
  size = 'lg'
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className={`bg-white w-full ${sizeClasses[size]} rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]`}>
        {/* Modal Header */}
        {(image || title) && (
          <div className="h-48 relative bg-slate-100 flex-shrink-0">
            {image && (
              <div className="absolute inset-0 flex items-center justify-center">
                <MedicationImage
                  src={image.src}
                  alt={image.alt}
                  size="xl"
                  className="opacity-80"
                />
              </div>
            )}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 bg-black/20 hover:bg-black/40 text-white rounded-full backdrop-blur-sm transition-colors"
            >
              <X size={20} />
            </button>
            {(title || subtitle) && (
              <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/60 to-transparent p-6">
                <h2 className="text-3xl font-bold text-white mb-2">{title}</h2>
                {subtitle && (
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-white/20 backdrop-blur-md rounded text-white text-sm font-medium border border-white/10">
                      {subtitle}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto">
          {children}
        </div>

        {/* Modal Actions */}
        {actions && (
          <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};
import React from 'react';

interface PatientAvatarProps {
  fullName?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const PatientAvatar: React.FC<PatientAvatarProps> = ({
  fullName = 'Patient',
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-24 h-24'
  };

  const imgSize = size === 'lg' ? 'w-full h-full' : sizeClasses[size];

  return (
    <div className={`${sizeClasses[size]} rounded-full bg-slate-100 border-4 border-white shadow-md overflow-hidden flex-shrink-0 ${className}`}>
      <img
        src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${fullName}`}
        alt={fullName}
        className={`${imgSize} object-cover`}
      />
    </div>
  );
};

export default PatientAvatar;
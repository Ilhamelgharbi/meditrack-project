import React from 'react';

interface AgeDisplayProps {
  dateOfBirth?: string;
  className?: string;
  showLabel?: boolean;
}

const AgeDisplay: React.FC<AgeDisplayProps> = ({
  dateOfBirth,
  className = '',
  showLabel = true
}) => {
  const calculateAge = (dateOfBirth?: string): number | null => {
    if (!dateOfBirth) return null;
    const birth = new Date(dateOfBirth);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  const age = calculateAge(dateOfBirth);

  if (!age) return null;

  return (
    <span className={`flex items-center gap-1 ${className}`}>
      {showLabel && <span>Age:</span>}
      {age} yrs
    </span>
  );
};

export default AgeDisplay;
// src/utils/formatters.ts

export const formatAge = (dateOfBirth?: string, withLabel: boolean = true): string => {
  if (!dateOfBirth) return 'Not set';
  
  const birth = new Date(dateOfBirth);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return withLabel ? `${age} yrs` : `${age}`;
};

export const formatWeight = (weight?: number): string => {
  if (!weight) return 'Not set';
  return `${weight}`;
};

export const formatHeight = (height?: number): string => {
  if (!height) return 'Not set';
  return `${height}`;
};

export const formatBloodType = (bloodType?: string): string => {
  if (!bloodType) return 'Not set';
  return bloodType;
};

export const formatPhone = (phone?: string): string => {
  if (!phone) return 'Not provided';
  return phone;
};

export const formatDate = (date?: string): string => {
  if (!date) return 'Not set';
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export const formatGender = (gender?: string): string => {
  if (!gender) return 'Not specified';
  return gender.charAt(0).toUpperCase() + gender.slice(1);
};

export const formatStatus = (status: string): string => {
  switch (status) {
    case 'stable':
      return 'Stable';
    case 'critical':
      return 'Critical';
    case 'under_observation':
      return 'Under Observation';
    default:
      return status;
  }
};
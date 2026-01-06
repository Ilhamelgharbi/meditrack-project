// src/components/common/AdherenceColorUtils.ts
export const getAdherenceColor = (score: number): string => {
  if (score >= 90) return 'text-green-600';
  if (score >= 75) return 'text-blue-600';
  if (score >= 60) return 'text-yellow-600';
  return 'text-red-600';
};

export const getAdherenceBgColor = (score: number): string => {
  if (score >= 90) return 'bg-green-50 border-green-200';
  if (score >= 75) return 'bg-blue-50 border-blue-200';
  if (score >= 60) return 'bg-yellow-50 border-yellow-200';
  return 'bg-red-50 border-red-200';
};

export const getAdherenceIcon = (score: number) => {
  if (score >= 90) return 'Star';
  if (score >= 75) return 'TrendingUp';
  if (score >= 60) return 'Activity';
  return 'AlertCircle';
};

export const getAdherenceLabel = (score: number): string => {
  if (score >= 90) return 'Excellent';
  if (score >= 75) return 'Good';
  if (score >= 60) return 'Fair';
  return 'Needs Attention';
};

export const getAdherenceBarColor = (score: number): string => {
  if (score >= 90) return 'bg-green-500';
  if (score >= 75) return 'bg-blue-500';
  if (score >= 60) return 'bg-yellow-500';
  return 'bg-red-500';
};
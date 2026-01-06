// src/utils/timezone.ts
import { formatInTimeZone, toZonedTime } from 'date-fns-tz';
import { parseISO } from 'date-fns';

/**
 * Get user's timezone from localStorage or default to browser timezone
 */
export const getUserTimezone = (): string => {
  // Try to get from localStorage first
  const stored = localStorage.getItem('user_timezone');
  if (stored) return stored;

  // Fall back to browser timezone
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

/**
 * Set user's timezone preference
 */
export const setUserTimezone = (timezone: string): void => {
  localStorage.setItem('user_timezone', timezone);
};

/**
 * Format a UTC date string in the user's timezone
 */
export const formatInUserTimezone = (dateStr: string, timezone?: string): string => {
  const tz = timezone || getUserTimezone();
  try {
    const date = parseISO(dateStr);
    return formatInTimeZone(date, tz, 'yyyy-MM-dd HH:mm:ssXXX');
  } catch (error) {
    console.warn('Error formatting date in timezone:', error);
    return dateStr; // Return original string if parsing fails
  }
};

/**
 * Format date for display (short weekday format)
 */
export const formatDateForDisplay = (dateStr: string, timezone?: string): string => {
  const tz = timezone || getUserTimezone();
  try {
    const date = parseISO(dateStr);
    return formatInTimeZone(date, tz, 'EEE'); // Mon, Tue, etc.
  } catch (error) {
    console.warn('Error formatting date for display:', error);
    return 'Invalid Date';
  }
};

/**
 * Get current time in user's timezone
 */
export const getCurrentTimeInTimezone = (timezone?: string): string => {
  const tz = timezone || getUserTimezone();
  return formatInTimeZone(new Date(), tz, 'HH:mm');
};

/**
 * Check if a date is during DST in the given timezone
 */
export const isDST = (date: Date, timezone: string): boolean => {
  try {
    const jan = new Date(date.getFullYear(), 0, 1);
    const jul = new Date(date.getFullYear(), 6, 1);

    const janOffset = formatInTimeZone(jan, timezone, 'xxx'); // +01:00 format
    const julOffset = formatInTimeZone(jul, timezone, 'xxx');

    // If January and July have different offsets, there's DST
    return janOffset !== julOffset;
  } catch (error) {
    console.warn('Error checking DST:', error);
    return false;
  }
};

/**
 * Get DST warning message if applicable
 */
export const getDSTWarning = (date: Date, timezone: string): string | null => {
  if (!isDST(date, timezone)) return null;

  // Check if date is near DST transition (within 1 week)
  const now = new Date();
  const diff = Math.abs(date.getTime() - now.getTime());
  const oneWeek = 7 * 24 * 60 * 60 * 1000;

  if (diff > oneWeek) return null;

  return 'Note: This date falls during Daylight Saving Time transition period.';
};

/**
 * Convert local time string (HH:mm) to UTC DateTime
 */
export const localTimeToUTC = (timeStr: string, dateStr: string, timezone?: string): Date => {
  const tz = timezone || getUserTimezone();
  const dateTimeStr = `${dateStr}T${timeStr}:00`;
  return toZonedTime(dateTimeStr, tz);
};

/**
 * Convert UTC DateTime to local time string in user's timezone
 */
export const utcToLocalTime = (utcDate: Date, timezone?: string): string => {
  const tz = timezone || getUserTimezone();
  return formatInTimeZone(utcDate, tz, 'HH:mm');
};
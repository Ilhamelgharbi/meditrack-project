// src/contexts/NotificationContext.tsx
import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { reminderService } from '../services/reminder.service';
import type { TodayReminder } from '../types/reminders.types';

// Notification types
export interface Notification {
  id: string;
  type: 'reminder' | 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
  medicationId?: number;
  reminderId?: number;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  showToast: boolean;
  currentToast: Notification | null;
  dismissToast: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: React.ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showToast, setShowToast] = useState(false);
  const [currentToast, setCurrentToast] = useState<Notification | null>(null);
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reminderCheckRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const checkedRemindersRef = useRef<Set<number>>(new Set());

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      read: false,
    };

    setNotifications(prev => [newNotification, ...prev]);

    // Show toast for new notification
    setCurrentToast(newNotification);
    setShowToast(true);

    // Auto-dismiss toast after 5 seconds
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    toastTimeoutRef.current = setTimeout(() => {
      setShowToast(false);
    }, 5000);

    // Play notification sound for reminders
    if (notification.type === 'reminder') {
      playNotificationSound();
    }
  }, []);

  const playNotificationSound = () => {
    try {
      // Create a simple notification sound using Web Audio API
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 880; // A5 note
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      console.log('Could not play notification sound:', error);
    }
  };

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const dismissToast = useCallback(() => {
    setShowToast(false);
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  // Check for upcoming medication reminders
  const checkForReminders = useCallback(async () => {
    try {
      const todayReminders = await reminderService.getTodayReminders();
      const now = new Date();

      todayReminders.forEach((reminder: TodayReminder) => {
        const scheduledTime = new Date(reminder.scheduled_time);
        const advanceMinutes = reminder.advance_minutes || 15;
        const notifyTime = new Date(scheduledTime.getTime() - advanceMinutes * 60 * 1000);

        // Check if we should notify (within 1 minute of notify time)
        const timeDiff = notifyTime.getTime() - now.getTime();
        
        if (
          timeDiff >= 0 &&
          timeDiff <= 60000 &&
          reminder.status === 'pending' &&
          !checkedRemindersRef.current.has(reminder.id)
        ) {
          checkedRemindersRef.current.add(reminder.id);
          
          addNotification({
            type: 'reminder',
            title: 'Medication Reminder',
            message: `Time to take ${reminder.medication_name} (${reminder.dosage}) in ${advanceMinutes} minutes`,
            actionUrl: '/patient/reminders',
            actionLabel: 'View Reminders',
            medicationId: reminder.id,
            reminderId: reminder.id,
          });

          // Also request browser notification permission and show
          requestBrowserNotification(
            'Medication Reminder',
            `Time to take ${reminder.medication_name} (${reminder.dosage}) in ${advanceMinutes} minutes`
          );
        }
      });
    } catch (error) {
      console.error('Error checking reminders:', error);
    }
  }, [addNotification]);

  const requestBrowserNotification = async (title: string, body: string) => {
    if (!('Notification' in window)) return;

    if (Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'medication-reminder',
      });
    } else if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        new Notification(title, {
          body,
          icon: '/favicon.ico',
          badge: '/favicon.ico',
          tag: 'medication-reminder',
        });
      }
    }
  };

  // Set up reminder checking interval
  useEffect(() => {
    // Check immediately on mount
    checkForReminders();

    // Check every minute
    reminderCheckRef.current = setInterval(checkForReminders, 60000);

    return () => {
      if (reminderCheckRef.current) {
        clearInterval(reminderCheckRef.current);
      }
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, [checkForReminders]);

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        addNotification,
        markAsRead,
        markAllAsRead,
        removeNotification,
        clearAll,
        showToast,
        currentToast,
        dismissToast,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

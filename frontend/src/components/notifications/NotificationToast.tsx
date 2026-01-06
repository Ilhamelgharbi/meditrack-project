// src/components/notifications/NotificationToast.tsx
import React from 'react';
import { useNotifications } from '../../contexts/NotificationContext';
import { X, Bell, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const NotificationToast: React.FC = () => {
  const { showToast, currentToast, dismissToast, markAsRead } = useNotifications();
  const navigate = useNavigate();

  if (!showToast || !currentToast) return null;

  const handleAction = () => {
    if (currentToast.actionUrl) {
      navigate(currentToast.actionUrl);
    }
    markAsRead(currentToast.id);
    dismissToast();
  };

  const getIcon = () => {
    switch (currentToast.type) {
      case 'reminder':
        return <Bell className="w-6 h-6 text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-6 h-6 text-amber-500" />;
      case 'error':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      case 'info':
      default:
        return <Info className="w-6 h-6 text-blue-500" />;
    }
  };

  const getBgColor = () => {
    switch (currentToast.type) {
      case 'reminder':
        return 'bg-blue-50 border-blue-200';
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
      <div
        className={`
          max-w-sm w-full rounded-xl border shadow-lg p-4
          ${getBgColor()}
          transform transition-all duration-300 ease-out
        `}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {getIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-slate-900">
              {currentToast.title}
            </h4>
            <p className="mt-1 text-sm text-slate-600 line-clamp-2">
              {currentToast.message}
            </p>
            {currentToast.actionUrl && (
              <button
                onClick={handleAction}
                className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                {currentToast.actionLabel || 'View Details'} →
              </button>
            )}
          </div>
          <button
            onClick={dismissToast}
            className="flex-shrink-0 p-1 rounded-lg hover:bg-black/5 transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Add to your global CSS or tailwind config:
// @keyframes slide-in-right {
//   from {
//     transform: translateX(100%);
//     opacity: 0;
//   }
//   to {
//     transform: translateX(0);
//     opacity: 1;
//   }
// }
// .animate-slide-in-right {
//   animation: slide-in-right 0.3s ease-out;
// }

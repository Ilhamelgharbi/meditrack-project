import { useState, useRef, useEffect } from "react";
import { Bell, ChevronDown, Menu, X, Pill, User, LogOut, Check } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { useNotifications } from "../../contexts/NotificationContext";
import type { Notification } from "../../contexts/NotificationContext";
import PatientAvatar from "../../components/patient/PatientAvatar";

interface NavbarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (state: boolean) => void;
}

export default function Navbar({ sidebarOpen, setSidebarOpen }: NavbarProps) {
  const { user, logout } = useAuth();
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification } = useNotifications();
  const navigate = useNavigate();
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [notificationDropdownOpen, setNotificationDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);
  const notificationRef = useRef<HTMLDivElement | null>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setProfileDropdownOpen(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setNotificationDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleNotificationClick = (notification: Notification) => {
    markAsRead(notification.id);
    if (notification.actionUrl) {
      navigate(notification.actionUrl);
    }
    setNotificationDropdownOpen(false);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'reminder':
        return <Bell className="w-4 h-4 text-blue-500" />;
      case 'success':
        return <Check className="w-4 h-4 text-emerald-500" />;
      case 'warning':
        return <Bell className="w-4 h-4 text-amber-500" />;
      case 'error':
        return <Bell className="w-4 h-4 text-red-500" />;
      default:
        return <Bell className="w-4 h-4 text-gray-500" />;
    }
  };

  const profilePath = user?.role === 'admin' ? '/admin/profile' : '/patient/profile';
  const medicationsPath = user?.role === 'admin' ? '/admin/medications' : '/patient/medications';

  return (
    <header className="bg-white h-20 border-b border-slate-100 flex items-center justify-between px-8 sticky top-0 z-40 shadow-sm">

      {/* Sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Right section */}
      <div className="flex items-center gap-6">

        {/* Notification button */}
        <div className="relative" ref={notificationRef}>
          <button 
            onClick={() => setNotificationDropdownOpen(!notificationDropdownOpen)}
            className="relative p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 min-w-[18px] h-[18px] bg-red-500 rounded-full border-2 border-white text-white text-xs flex items-center justify-center font-medium">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Dropdown */}
          {notificationDropdownOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">Notifications</h3>
                {unreadCount > 0 && (
                  <button 
                    onClick={markAllAsRead}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Mark all as read
                  </button>
                )}
              </div>

              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    <Bell className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    <p className="text-sm">No notifications yet</p>
                  </div>
                ) : (
                  notifications.slice(0, 10).map((notification) => (
                    <div 
                      key={notification.id}
                      className={`p-3 border-b border-slate-50 hover:bg-slate-50 cursor-pointer flex items-start gap-3 ${
                        !notification.read ? 'bg-blue-50/50' : ''
                      }`}
                      onClick={() => handleNotificationClick(notification)}
                    >
                      <div className="p-2 bg-slate-100 rounded-lg">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${!notification.read ? 'font-semibold' : ''} text-slate-900 truncate`}>
                          {notification.title}
                        </p>
                        <p className="text-xs text-slate-500 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          {new Date(notification.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeNotification(notification.id);
                        }}
                        className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))
                )}
              </div>

              {notifications.length > 0 && (
                <div className="p-3 border-t border-slate-100 text-center">
                  <Link 
                    to={user?.role === 'patient' ? '/patient/reminders' : '/admin/dashboard'}
                    onClick={() => setNotificationDropdownOpen(false)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View all reminders
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="h-8 w-[1px] bg-slate-200"></div>

        {/* Profile */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
            className="flex items-center gap-3 p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <div className="hidden md:flex flex-col text-right">
              <p className="text-sm font-semibold text-slate-900">{user?.full_name}</p>
              <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
            </div>

            {/* Avatar */}
            <PatientAvatar fullName={user?.full_name} size="md" />

            <ChevronDown
              size={16}
              className={`text-slate-500 transition-transform ${profileDropdownOpen ? "rotate-180" : ""}`}
            />
          </button>

          {/* Dropdown */}
          {profileDropdownOpen && (
            <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden">
              <div className="p-4 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-900">{user?.full_name}</p>
                <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
              </div>

              <div className="py-2">

                <Link
                  to={medicationsPath}
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <Pill size={16} />
                  <span>Medications</span>
                </Link>

                <Link
                  to={profilePath}
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <User size={16} />
                  <span>Profile</span>
                </Link>

                <button
                  onClick={logout}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                >
                  <LogOut size={16} />
                  <span>Logout</span>
                </button>

              </div>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}

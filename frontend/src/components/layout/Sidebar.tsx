import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  Home,
  Users,
  Pill,
  TrendingUp,
  Clock,
  User,
  LogOut,
  BarChart3,
  Bot,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

interface SidebarProps {
  sidebarOpen: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ sidebarOpen }) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const adminNavItems = [
    { path: "/admin/dashboard", icon: Home, label: "Dashboard" },
    { path: "/admin/patients", icon: Users, label: "Patients" },
    { path: "/admin/medications", icon: Pill, label: "Medications" },
    { path: "/admin/adherence", icon: TrendingUp, label: "Adherence" },
    { path: "/admin/analytics", icon: BarChart3, label: "Analytics" },
    { path: "/admin/assistant", icon: Bot, label: "AI Assistant" },
    { path: "/admin/profile", icon: User, label: "Profile" },
  ];

  const patientNavItems = [
    { path: "/patient/dashboard", icon: Home, label: "Dashboard" },
    { path: "/patient/medications", icon: Pill, label: "Medications" },
    { path: "/patient/reminders", icon: Clock, label: "Reminders" },
    { path: "/patient/adherence", icon: TrendingUp, label: "Adherence" },
    { path: "/patient/assistant", icon: Bot, label: "AI Assistant" },
    { path: "/patient/profile", icon: User, label: "Profile" },
  ];

  const navItems = user?.role === "admin" ? adminNavItems : patientNavItems;

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-50 bg-[#1A2B44] text-white 
        transition-all duration-300 ease-in-out shadow-xl
        ${sidebarOpen ? "w-64" : "w-20"} overflow-hidden
      `}
    >
      {/* Logo */}
      <div className="p-6 border-b border-white/10 flex items-center gap-3 h-20">
        <div className="bg-[#2A7EF0] p-2 rounded-lg">
          <Activity size={24} className="text-white" />
        </div>
        {sidebarOpen && <span className="font-bold text-xl tracking-tight font-heading">MediTrack AI</span>}
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 group
                ${
                  isActive 
                    ? 'bg-[#2A7EF0] text-white shadow-lg shadow-blue-900/20' 
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }
              `}
            >
              <Icon size={20} className={isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'} />
              {sidebarOpen && <span className="font-medium">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User / Logout */}
      <div className="absolute bottom-0 w-full border-t border-white/10 bg-[#152338]">
        <div className="p-4">
          <button
            onClick={logout}
            className="flex items-center gap-4 px-4 py-3 w-full rounded-lg text-red-400 hover:bg-red-500/10 transition-all duration-200"
          >
            <LogOut size={20} />
            {sidebarOpen && <span className="font-medium">Logout</span>}
          </button>
        </div>
      </div>
    </aside>
  );
};

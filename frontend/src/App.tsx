// src/App.tsx
// Complete routing with all pages for MediTrack AI
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ProtectedRoute, AuthRedirect } from './components/auth/ProtectedRoute';
import { DashboardLayout } from './components/layout/DashboardLayout';

// Public Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';

// Patient Pages
import { PatientDashboard } from './pages/patient/Dashboard';
import PatientProfile from './pages/patient/Profile';
import MedicationsPage from './pages/patient/Medications';
import { PatientAdherence } from './pages/patient/Adherence';
import RemindersCalendar from './pages/patient/RemindersCalendar';
import AIAssistant from './pages/patient/AIAssistant';

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard';
import AdminProfile from './pages/admin/Profile';
import PatientsList from './pages/admin/PatientsList';
import PatientDetails from './pages/admin/PatientDetails';
import Medications from './pages/admin/Medications';
import { AdminAdherenceDashboard } from './pages/admin/AdherenceDashboard';
import { PatientAdherenceDetails } from './pages/admin/PatientAdherenceDetails';
import { AdminAnalyticsDashboard } from './pages/admin/AdminAnalyticsDashboard';
import AdminAIAssistant from './pages/admin/AIAssistant';

// Notification Component
import { NotificationToast } from './components/notifications/NotificationToast';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <NotificationToast />
          <Routes>
            {/* ==================== PUBLIC ROUTES ==================== */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={
              <AuthRedirect>
                <Login />
              </AuthRedirect>
            } />
            <Route path="/register" element={
              <AuthRedirect>
                <Register />
              </AuthRedirect>
            } />

            {/* ==================== PATIENT ROUTES ==================== */}
            <Route
              path="/patient/dashboard"
              element={
                <ProtectedRoute allowedRoles={['patient']}>
                  <DashboardLayout>
                    <PatientDashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/medications"
              element={
                <ProtectedRoute allowedRoles={['patient']}>
                  <DashboardLayout>
                    <MedicationsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/reminders"
              element={
                <ProtectedRoute allowedRoles={['patient']}>
                  <DashboardLayout>
                    <RemindersCalendar />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/adherence"
              element={
                <ProtectedRoute allowedRoles={['patient']}>
                  <DashboardLayout>
                    <PatientAdherence />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/profile"
              element={
                <ProtectedRoute allowedRoles={['patient']}>
                  <DashboardLayout>
                    <PatientProfile />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/assistant"
              element={
                <ProtectedRoute allowedRoles={['patient']}>
                  <DashboardLayout>
                    <AIAssistant />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            {/* ==================== ADMIN ROUTES ==================== */}
            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <AdminDashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/patients"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <PatientsList />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/patients/:id"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <PatientDetails />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/medications"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <Medications />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/adherence"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <AdminAdherenceDashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/adherence/:patientId"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <PatientAdherenceDetails />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <AdminAnalyticsDashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/profile"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <AdminProfile />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/assistant"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <DashboardLayout>
                    <AdminAIAssistant />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            {/* ==================== FALLBACK ==================== */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
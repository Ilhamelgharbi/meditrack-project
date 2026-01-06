import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { UserHeader } from '../../components/shared/UserHeader';
import { AdminProfileEditModal } from '../../components/profile/AdminProfileEditModal';
import type { AdminProfileData } from '../../components/profile/AdminProfileEditModal';
import { AdminBioCard } from '../../components/profile/AdminBioCard';
import { AdminSettingsCard } from '../../components/profile/AdminSettingsCard';
import { ContactCard } from '../../components/shared/ContactCard';
import { Mail, Smartphone } from 'lucide-react';

const AdminProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Mock admin data - in a real app, this would come from an API
  const [adminData, setAdminData] = useState<AdminProfileData>({
    fullName: user?.full_name || 'Dr. Sarah Johnson',
    email: user?.email || 'sarah.johnson@meditrack.com',
    specialty: 'Cardiology',
    hospital: 'City General Hospital',
    licenseNumber: 'MD123456789',
    bio: 'Board-certified cardiologist with over 15 years of experience in cardiovascular medicine. Specializes in preventive cardiology, heart failure management, and interventional procedures. Committed to providing compassionate, evidence-based care to improve patient outcomes.'
  });

  const [settings, setSettings] = useState({
    emailNotifications: true,
    smsNotifications: false,
    twoFactorAuth: true,
    darkMode: false
  });

  const handleEditSave = (data: AdminProfileData) => {
    setAdminData(data);
    // In a real app, you would save this to an API
  };

  const handleSettingsChange = (setting: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      [setting]: value
    }));
    // In a real app, you would save this to an API
  };

  return (

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <UserHeader
          variant="admin"
          user={{
            fullName: adminData.fullName,
            email: adminData.email,
            role: 'admin',
            specialty: adminData.specialty,
            hospital: adminData.hospital
          }}
          onEditClick={() => setIsEditModalOpen(true)}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <AdminBioCard
              bio={adminData.bio}
              specialty={adminData.specialty}
              hospital={adminData.hospital}
              licenseNumber={adminData.licenseNumber}
            />

            <ContactCard
              contacts={[
                {
                  icon: Mail,
                  label: 'Email Address',
                  value: adminData.email
                },
                {
                  icon: Smartphone,
                  label: 'Phone Number',
                  value: '+1 (555) 123-4567'
                }
              ]}
            />
          </div>

          <div className="space-y-6">
            <AdminSettingsCard
              settings={settings}
              onSettingsChange={handleSettingsChange}
            />
          </div>
        </div>

        <AdminProfileEditModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          onSave={handleEditSave}
          initialData={adminData}
        />
      </div>

  );
};

export default AdminProfilePage;

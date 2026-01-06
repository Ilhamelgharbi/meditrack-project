// src/pages/auth/Register.tsx
import { Link } from 'react-router-dom';
import { Activity, ArrowLeft } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { RegisterForm } from '../../components/auth/RegisterForm';

export const Register = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
        >
          <ArrowLeft size={20} />
          <span>Back to home</span>
        </Link>

        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="bg-blue-600 p-3 rounded-xl shadow-lg">
              <Activity className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create your account</h1>
          <p className="text-gray-600">Join MediTrack AI to start managing your medications</p>
        </div>

        <Card variant="elevated" className="p-8">
          <RegisterForm />
        </Card>
      </div>
    </div>
  );
};
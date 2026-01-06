// src/pages/auth/Login.tsx
import { Link } from 'react-router-dom';
import { Activity, ArrowLeft } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { LoginForm } from '../../components/auth/LoginForm';

export const Login = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome back</h1>
          <p className="text-gray-600">Sign in to your MediTrack AI account</p>
        </div>

        <Card variant="elevated" className="p-8">
          <LoginForm />
        </Card>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Demo accounts available for testing
          </p>
        </div>
      </div>
    </div>
  );
};
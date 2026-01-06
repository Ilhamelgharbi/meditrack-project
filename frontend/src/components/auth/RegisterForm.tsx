// src/components/auth/RegisterForm.tsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Lock, User, Phone, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import type { RegisterData, UserRole } from '../../types/auth.types';


export const RegisterForm = () => {
  const { register } = useAuth();
  const [formData, setFormData] = useState<RegisterData>({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    role: 'patient',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.full_name) {
      newErrors.full_name = 'Full name is required';
    } else if (formData.full_name.length < 2) {
      newErrors.full_name = 'Name must be at least 2 characters';
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (formData.phone && !/^\+?[\d\s-()]+$/.test(formData.phone)) {
      newErrors.phone = 'Invalid phone number format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (formData.password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!validateForm()) return;

    setIsLoading(true);
    try {
      await register(formData);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Registration failed. Please try again.';
      setErrors({ general: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {errors.general && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-red-900">Registration Failed</h4>
            <p className="text-sm text-red-700 mt-1">{errors.general}</p>
          </div>
        </div>
      )}

      <Input
        type="text"
        label="Full Name"
        placeholder="John Doe"
        value={formData.full_name}
        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
        error={errors.full_name}
        leftIcon={<User size={20} />}
        required
      />

      <Input
        type="email"
        label="Email Address"
        placeholder="you@example.com"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        error={errors.email}
        leftIcon={<Mail size={20} />}
        required
      />

      <Input
        type="tel"
        label="Phone Number"
        placeholder="+1 (555) 000-0000"
        value={formData.phone}
        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
        error={errors.phone}
        leftIcon={<Phone size={20} />}
        helperText="Optional"
      />

      <div className="grid grid-cols-2 gap-4">
        <Input
          type="password"
          label="Password"
          placeholder="••••••••"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          error={errors.password}
          leftIcon={<Lock size={20} />}
          required
        />

        <Input
          type="password"
          label="Confirm Password"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={errors.confirmPassword}
          leftIcon={<Lock size={20} />}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Account Type
        </label>
        <div className="grid grid-cols-2 gap-4">
          {(['patient', 'admin'] as UserRole[]).map((role) => (
            <label
              key={role}
              className={`
                flex items-center justify-center p-3 rounded-lg border-2 cursor-pointer transition-all
                ${formData.role === role
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <input
                type="radio"
                name="role"
                value={role}
                checked={formData.role === role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                className="sr-only"
              />
              <span className="font-medium capitalize">{role}</span>
            </label>
          ))}
        </div>
      </div>

      <Button type="submit" variant="primary" fullWidth isLoading={isLoading}>
        Create Account
      </Button>

      <p className="text-center text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold">
          Sign in
        </Link>
      </p>
    </form>
  );
};
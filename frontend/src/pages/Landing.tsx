// src/pages/Landing.tsx
import { Link } from 'react-router-dom';
import { Activity, Bell, BarChart3, MessageSquare, Calendar, ArrowRight, Camera, Mic, Heart, Check } from 'lucide-react';
import { Button } from '../components/common/Button';

export const Landing = () => {
  const features = [
    {
      icon: <Bell className="w-6 h-6" />,
      title: 'Smart Reminders',
      description: 'Never miss a dose with intelligent, personalized medication reminders via push, SMS, or WhatsApp.',
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: 'Adherence Tracking',
      description: 'Monitor your medication compliance with detailed analytics and insights to stay on track.',
    },
    {
      icon: <MessageSquare className="w-6 h-6" />,
      title: 'AI Assistant',
      description: 'Get instant answers about medications, side effects, drug interactions, and health questions.',
    },
    {
      icon: <Calendar className="w-6 h-6" />,
      title: 'Schedule Management',
      description: 'Organize your medication schedule with an intuitive calendar view for easy tracking.',
    },
    {
      icon: <Camera className="w-6 h-6" />,
      title: 'Pill Identification',
      description: 'Identify unknown pills by simply taking a photo. Our AI analyzes and matches medications.',
    },
    {
      icon: <Mic className="w-6 h-6" />,
      title: 'Voice Commands',
      description: 'Use voice to ask questions, log medications, or set reminders hands-free.',
    },
  ];

  const howItWorks = [
    {
      step: '01',
      title: 'Sign Up',
      description: 'Create your free account in seconds. No credit card required.',
    },
    {
      step: '02',
      title: 'Add Medications',
      description: 'Your doctor assigns medications or you can add them yourself.',
    },
    {
      step: '03',
      title: 'Set Reminders',
      description: 'Configure personalized reminder schedules that work for you.',
    },
    {
      step: '04',
      title: 'Track & Improve',
      description: 'Log doses, track adherence, and improve your health outcomes.',
    },
  ];

  const testimonials = [
    {
      quote: "MediTrack AI has completely changed how I manage my medications. I haven't missed a dose in months!",
      author: "Sarah M.",
      role: "Patient",
    },
    {
      quote: "The pill identification feature saved me when I mixed up my medications. Incredible technology!",
      author: "James R.",
      role: "Patient",
    },
    {
      quote: "As a healthcare provider, I can now monitor my patients' adherence in real-time. Game changer.",
      author: "Dr. Emily K.",
      role: "Physician",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navbar */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">MediTrack AI</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link to="/register">
                <Button variant="primary">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Your Personal
              <span className="text-blue-600"> Medication</span>
              <br />
              Management Assistant
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Track medications, receive smart reminders, and improve adherence with AI-powered insights.
              Take control of your health journey today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button variant="primary" size="lg" rightIcon={<ArrowRight size={20} />}>
                  Start Free Trial
                </Button>
              </Link>
              <Button variant="outline" size="lg">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Stay Healthy
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive medication management tools designed for patients and healthcare providers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="p-6 rounded-2xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300 bg-white"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Get started in just a few simple steps and take control of your medication management.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {howItWorks.map((item, index) => (
              <div key={index} className="relative text-center">
                <div className="text-6xl font-bold text-blue-100 mb-4">{item.step}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Features Showcase */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="text-blue-600 font-semibold uppercase tracking-wide text-sm">AI-Powered</span>
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mt-2 mb-6">
                Intelligent Health Companion
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Our advanced AI assistant understands your health needs and provides personalized support through text, voice, and image recognition.
              </p>
              <ul className="space-y-4">
                {[
                  'Ask health questions in natural language',
                  'Identify pills from photos using AI vision',
                  'Get drug interaction warnings instantly',
                  'Voice-enabled for hands-free access',
                  'RAG-powered medical knowledge base',
                ].map((item, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <div className="w-6 h-6 bg-emerald-100 rounded-full flex items-center justify-center">
                      <Check className="w-4 h-4 text-emerald-600" />
                    </div>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
              <Link to="/register" className="inline-block mt-8">
                <Button variant="primary" rightIcon={<ArrowRight size={20} />}>
                  Try AI Assistant
                </Button>
              </Link>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-blue-600 to-violet-600 rounded-3xl p-8 text-white">
                <div className="bg-white/10 backdrop-blur rounded-2xl p-6 space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                      <span className="text-sm">You</span>
                    </div>
                    <div className="bg-white/20 rounded-2xl rounded-tl-none px-4 py-3">
                      <p className="text-sm">What are the side effects of Metformin?</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 flex-row-reverse">
                    <div className="w-8 h-8 bg-emerald-400 rounded-full flex items-center justify-center">
                      <MessageSquare className="w-4 h-4" />
                    </div>
                    <div className="bg-white/20 rounded-2xl rounded-tr-none px-4 py-3">
                      <p className="text-sm">Common side effects of Metformin include nausea, stomach upset, and diarrhea. These usually improve over time...</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Loved by Patients & Providers
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex gap-1 mb-4">
                  {[1, 2, 3, 4, 5].map(star => (
                    <Heart key={star} className="w-5 h-5 fill-red-400 text-red-400" />
                  ))}
                </div>
                <p className="text-gray-700 mb-6 italic">"{testimonial.quote}"</p>
                <div>
                  <p className="font-semibold text-gray-900">{testimonial.author}</p>
                  <p className="text-sm text-gray-500">{testimonial.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12 shadow-2xl">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Ready to Transform Your Health Management?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join thousands of patients and healthcare providers using MediTrack AI.
            </p>
            <Link to="/register">
              <Button
                variant="secondary"
                size="lg"
                className="bg-white text-blue-600 hover:bg-gray-100"
                rightIcon={<ArrowRight size={20} />}
              >
                Create Free Account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold">MediTrack AI</span>
          </div>
          <p className="text-gray-400 mb-4">
            Empowering patients with intelligent medication management.
          </p>
          <p className="text-sm text-gray-500">
            © 2026 MediTrack AI. All rights reserved. | Your health, intelligently managed.
          </p>
        </div>
      </footer>
    </div>
  );
};
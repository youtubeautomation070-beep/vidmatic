import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { toast } from 'sonner';
import { PlayCircle, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const Auth = () => {
  const navigate = useNavigate();
  const [isSignup, setIsSignup] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  
  const handleGoogleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };
  
  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const endpoint = isSignup ? '/auth/signup' : '/auth/login';
      const response = await api.post(endpoint, formData);
      
      toast.success(isSignup ? 'Account created!' : 'Logged in successfully');
      navigate('/dashboard', { state: { user: response.data.user } });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-[#0a0a0c] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Glows */}
      <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px]"></div>
        <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-fuchsia-600/10 blur-[120px]"></div>
      </div>
      
      {/* Back to Home */}
      <div className="absolute top-6 left-6 cursor-pointer" onClick={() => navigate('/')}>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-gradient-primary flex items-center justify-center text-white">
            <PlayCircle className="w-4 h-4" />
          </div>
          <span className="font-semibold tracking-tighter text-sm text-white">VIDMATIC</span>
        </div>
      </div>
      
      <div className="glass-card w-full max-w-md rounded-2xl p-8 shadow-2xl relative overflow-hidden fade-in" data-testid="auth-form">
        {/* Glow effect inside card */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-indigo-500/20 rounded-full blur-[50px]"></div>
        
        <div className="text-center mb-8 relative z-10">
          <h2 className="text-2xl font-semibold tracking-tight text-white mb-2">
            {isSignup ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className="text-sm text-zinc-400">
            {isSignup ? 'Start creating amazing videos today' : 'Enter your details to access your workspace'}
          </p>
        </div>
        
        {/* Social Login */}
        <button
          onClick={handleGoogleLogin}
          className="w-full bg-zinc-800/50 border border-zinc-700 hover:bg-zinc-700/50 text-white rounded-lg py-2.5 flex items-center justify-center gap-3 text-sm font-medium transition-colors mb-6"
          data-testid="google-login-btn"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>
        
        <div className="flex items-center gap-4 mb-6">
          <div className="h-px bg-zinc-800 flex-1"></div>
          <span className="text-xs text-zinc-500">OR</span>
          <div className="h-px bg-zinc-800 flex-1"></div>
        </div>
        
        {/* Email/Password Form */}
        <form onSubmit={handleEmailAuth} className="space-y-4 relative z-10">
          {isSignup && (
            <div>
              <Label className="block text-xs font-medium text-zinc-300 mb-1.5">Full Name</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <Input
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-500"
                  required={isSignup}
                  data-testid="name-input"
                />
              </div>
            </div>
          )}
          
          <div>
            <Label className="block text-xs font-medium text-zinc-300 mb-1.5">Email Address</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-500"
                required
                data-testid="email-input"
              />
            </div>
          </div>
          
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <Label className="block text-xs font-medium text-zinc-300">Password</Label>
              {!isSignup && (
                <button
                  type="button"
                  onClick={() => navigate('/reset-password')}
                  className="text-xs text-indigo-400 hover:text-indigo-300"
                >
                  Forgot password?
                </button>
              )}
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-10 py-2.5 text-sm text-white placeholder-zinc-500"
                required
                data-testid="password-input"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {isSignup && (
              <p className="text-xs text-zinc-500 mt-1">At least 8 characters with letters and numbers</p>
            )}
          </div>
          
          {!isSignup && (
            <div className="flex items-center gap-2 pt-2">
              <input type="checkbox" id="remember" className="w-4 h-4" />
              <label htmlFor="remember" className="text-xs text-zinc-400 select-none cursor-pointer">
                Remember me for 30 days
              </label>
            </div>
          )}
          
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-primary text-white font-medium rounded-lg py-2.5 mt-4 hover:shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all text-sm disabled:opacity-50"
            data-testid="submit-btn"
          >
            {loading ? 'Processing...' : (isSignup ? 'Create Account' : 'Sign In')}
          </Button>
        </form>
        
        <div className="mt-6 text-center text-xs text-zinc-400">
          <span>{isSignup ? 'Already have an account?' : "Don't have an account?"}</span>{' '}
          <button
            onClick={() => setIsSignup(!isSignup)}
            className="text-indigo-400 hover:text-indigo-300 font-medium ml-1"
            data-testid="toggle-auth-btn"
          >
            {isSignup ? 'Sign in' : 'Sign up'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;
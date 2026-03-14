import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { toast } from 'sonner';
import { PlayCircle, Mail, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const PasswordReset = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleRequestReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.post('/auth/password-reset/request', { email });
      toast.success('Reset link sent! Check your email.');
      if (response.data.reset_token) {
        setResetToken(response.data.reset_token);
      }
      setStep(2);
    } catch (error) {
      toast.error('Failed to send reset link');
    } finally {
      setLoading(false);
    }
  };
  
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await api.post('/auth/password-reset/confirm', {
        reset_token: resetToken,
        new_password: newPassword
      });
      toast.success('Password reset successful!');
      navigate('/auth');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Password reset failed');
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
      
      {/* Back Button */}
      <div className="absolute top-6 left-6 cursor-pointer" onClick={() => navigate('/auth')}>
        <div className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
          <span className="text-sm font-medium">Back to Login</span>
        </div>
      </div>
      
      <div className="glass-card w-full max-w-md rounded-2xl p-8 shadow-2xl relative overflow-hidden fade-in">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold tracking-tight text-white mb-2">Reset Password</h2>
          <p className="text-sm text-zinc-400">
            {step === 1 ? 'Enter your email to receive reset instructions' : 'Enter your new password'}
          </p>
        </div>
        
        {step === 1 ? (
          <form onSubmit={handleRequestReset} className="space-y-4">
            <div>
              <Label className="block text-xs font-medium text-zinc-300 mb-1.5">Email Address</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-500"
                  required
                />
              </div>
            </div>
            
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-primary text-white font-medium rounded-lg py-2.5 hover:shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all text-sm disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Reset Link'}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <Label className="block text-xs font-medium text-zinc-300 mb-1.5">Reset Token</Label>
              <Input
                type="text"
                placeholder="Enter token from email"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-500"
                required
              />
            </div>
            
            <div>
              <Label className="block text-xs font-medium text-zinc-300 mb-1.5">New Password</Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-500"
                required
              />
              <p className="text-xs text-zinc-500 mt-1">At least 8 characters with letters and numbers</p>
            </div>
            
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-primary text-white font-medium rounded-lg py-2.5 hover:shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all text-sm disabled:opacity-50"
            >
              {loading ? 'Resetting...' : 'Reset Password'}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
};

export default PasswordReset;
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../utils/api';
import { toast } from 'sonner';
import { Crown } from 'lucide-react';

const Billing = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    fetchUser();
    
    // Check for session_id from Stripe redirect
    const params = new URLSearchParams(location.search);
    const sessionId = params.get('session_id');
    if (sessionId) {
      checkPaymentStatus(sessionId);
    }
  }, [location]);
  
  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      navigate('/');
    }
  };
  
  const checkPaymentStatus = async (sessionId) => {
    setLoading(true);
    try {
      const response = await api.get(`/payments/checkout/status/${sessionId}`);
      if (response.data.payment_status === 'paid') {
        toast.success('Payment successful! Your subscription is now active.');
        fetchUser();
      }
    } catch (error) {
      console.error('Payment status check failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleUpgrade = async (planId) => {
    setLoading(true);
    try {
      const originUrl = window.location.origin;
      const response = await api.post('/payments/checkout/session', {
        plan_id: planId,
        origin_url: originUrl
      });
      
      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start checkout');
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="glass-card rounded-2xl p-8 border border-zinc-800 relative overflow-hidden mb-8">
          <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <Crown className="w-32 h-32 text-indigo-500" />
          </div>
          <div className="relative z-10">
            <div className="inline-block bg-indigo-500/20 text-indigo-400 text-xs font-semibold px-2 py-1 rounded mb-4">CURRENT PLAN</div>
            <h2 className="text-3xl font-semibold text-white tracking-tight mb-2">
              {user?.subscription_plan === 'free_trial' && 'Free Trial'}
              {user?.subscription_plan === 'pro_monthly' && 'Pro Monthly'}
              {user?.subscription_plan === 'pro_yearly' && 'Pro Yearly'}
            </h2>
            <p className="text-sm text-zinc-400 mb-6">Active subscription</p>
            
            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 mb-6 max-w-md">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-zinc-300 font-medium">Credits Usage</span>
                <span className="text-white">{user?.video_credits + user?.free_video_credits || 0} remaining</span>
              </div>
              {user?.free_video_credits > 0 && (
                <p className="text-xs text-emerald-400 mt-2">+ {user.free_video_credits} bonus credits from referrals!</p>
              )}
            </div>
            
            {user?.subscription_plan === 'free_trial' && (
              <div className="flex gap-4">
                <button 
                  onClick={() => handleUpgrade('pro_monthly')}
                  disabled={loading}
                  className="bg-white text-black font-medium px-6 py-2 rounded-lg hover:bg-zinc-200 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Processing...' : 'Upgrade to Pro Monthly ($11/mo)'}
                </button>
                <button 
                  onClick={() => handleUpgrade('pro_yearly')}
                  disabled={loading}
                  className="bg-transparent border border-zinc-700 text-zinc-300 font-medium px-6 py-2 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Processing...' : 'Upgrade to Pro Yearly ($19/mo)'}
                </button>
              </div>
            )}
          </div>
        </div>
        
        <button 
          onClick={() => navigate('/dashboard')}
          className="bg-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-500"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default Billing;
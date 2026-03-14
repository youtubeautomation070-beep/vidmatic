import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, CheckCircle, XCircle, Clock, DollarSign, Users, Video } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';

const Admin = () => {
  const navigate = useNavigate();
  const [pendingPayments, setPendingPayments] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [adminNotes, setAdminNotes] = useState('');
  
  useEffect(() => {
    fetchPendingPayments();
    fetchStats();
  }, []);
  
  const fetchPendingPayments = async () => {
    try {
      const response = await api.get('/payments/pending');
      setPendingPayments(response.data.pending_payments);
    } catch (error) {
      console.error('Failed to fetch pending payments:', error);
    }
  };
  
  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };
  
  const handleVerifyPayment = async (transactionId, approved) => {
    setLoading(true);
    try {
      await api.post('/payments/verify', {
        transaction_id: transactionId,
        approved,
        admin_notes: adminNotes || null
      });
      
      toast.success(approved ? 'Payment approved!' : 'Payment rejected');
      setSelectedPayment(null);
      setAdminNotes('');
      fetchPendingPayments();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to verify payment');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-2 rounded-lg text-xs font-medium mb-6 flex items-center gap-2">
          <Shield className="w-4 h-4" />
          Admin privileges active. Changes here affect the global platform.
        </div>
        
        <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
        <p className="text-zinc-400 mb-8">Manage platform users, payments, and content</p>
        
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="glass-card p-4 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-indigo-500/10 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Total Users</p>
                  <p className="text-2xl font-bold text-white">{stats.total_users}</p>
                </div>
              </div>
            </div>
            
            <div className="glass-card p-4 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                  <Video className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Total Videos</p>
                  <p className="text-2xl font-bold text-white">{stats.total_videos}</p>
                </div>
              </div>
            </div>
            
            <div className="glass-card p-4 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Active Subs</p>
                  <p className="text-2xl font-bold text-white">{stats.active_subscriptions}</p>
                </div>
              </div>
            </div>
            
            <div className="glass-card p-4 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-orange-500/10 rounded-lg flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-400">Revenue</p>
                  <p className="text-2xl font-bold text-white">${stats.total_revenue.toFixed(0)}</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Pending Payment Verifications */}
        <div className="glass-card rounded-2xl p-6 border border-zinc-800 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Clock className="w-6 h-6 text-yellow-400" />
              Pending Payment Verifications ({pendingPayments.length})
            </h2>
          </div>
          
          {pendingPayments.length === 0 ? (
            <p className="text-zinc-400 text-center py-8">No pending payments to verify</p>
          ) : (
            <div className="space-y-4">
              {pendingPayments.map(payment => (
                <div key={payment.transaction_id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <p className="text-white font-semibold">{payment.plan.replace('_', ' ').toUpperCase()}</p>
                        <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full">
                          {payment.payment_method.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-400">
                        Amount: {payment.amount} {payment.currency} • 
                        User: {payment.metadata?.user_email || 'N/A'} • 
                        Date: {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                      {payment.transaction_hash && (
                        <p className="text-xs text-zinc-500 mt-1">Hash: {payment.transaction_hash}</p>
                      )}
                      {payment.user_notes && (
                        <p className="text-xs text-zinc-400 mt-1 italic">Note: {payment.user_notes}</p>
                      )}
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        onClick={() => setSelectedPayment(payment)}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 text-sm rounded-lg"
                      >
                        Review
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Review Modal */}
        {selectedPayment && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="glass-card max-w-2xl w-full rounded-2xl p-6 border border-zinc-800">
              <h3 className="text-xl font-semibold mb-4">Review Payment</h3>
              
              <div className="bg-zinc-900 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-zinc-400 mb-1">Transaction ID</p>
                    <p className="text-white font-mono">{selectedPayment.transaction_id}</p>
                  </div>
                  <div>
                    <p className="text-zinc-400 mb-1">Plan</p>
                    <p className="text-white">{selectedPayment.plan.replace('_', ' ').toUpperCase()}</p>
                  </div>
                  <div>
                    <p className="text-zinc-400 mb-1">Amount</p>
                    <p className="text-white font-semibold">{selectedPayment.amount} {selectedPayment.currency}</p>
                  </div>
                  <div>
                    <p className="text-zinc-400 mb-1">Payment Method</p>
                    <p className="text-white">{selectedPayment.payment_method.replace('_', ' ').toUpperCase()}</p>
                  </div>
                  <div>
                    <p className="text-zinc-400 mb-1">User Email</p>
                    <p className="text-white">{selectedPayment.metadata?.user_email || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-zinc-400 mb-1">Date</p>
                    <p className="text-white">{new Date(selectedPayment.created_at).toLocaleString()}</p>
                  </div>
                </div>
                
                {selectedPayment.transaction_hash && (
                  <div className="mt-4">
                    <p className="text-zinc-400 text-xs mb-1">Transaction Hash</p>
                    <p className="text-white text-xs font-mono break-all">{selectedPayment.transaction_hash}</p>
                  </div>
                )}
                
                {selectedPayment.user_notes && (
                  <div className="mt-4">
                    <p className="text-zinc-400 text-xs mb-1">User Notes</p>
                    <p className="text-white text-sm">{selectedPayment.user_notes}</p>
                  </div>
                )}
              </div>
              
              <div className="mb-4">
                <label className="block text-sm text-zinc-300 mb-2">Admin Notes (Optional)</label>
                <Textarea
                  rows={3}
                  placeholder="Add notes about this verification..."
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  className="bg-zinc-900 border-zinc-800 text-white"
                />
              </div>
              
              <div className="flex gap-3">
                <Button
                  onClick={() => handleVerifyPayment(selectedPayment.transaction_id, true)}
                  disabled={loading}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-6 py-2 rounded-lg flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  {loading ? 'Processing...' : 'Approve Payment'}
                </Button>
                <Button
                  onClick={() => handleVerifyPayment(selectedPayment.transaction_id, false)}
                  disabled={loading}
                  className="flex-1 bg-red-600 hover:bg-red-500 text-white font-medium px-6 py-2 rounded-lg flex items-center justify-center gap-2"
                >
                  <XCircle className="w-4 h-4" />
                  {loading ? 'Processing...' : 'Reject Payment'}
                </Button>
                <Button
                  onClick={() => {
                    setSelectedPayment(null);
                    setAdminNotes('');
                  }}
                  variant="outline"
                  className="border-zinc-700 text-white hover:bg-zinc-800"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
        
        <button 
          onClick={() => navigate('/dashboard')}
          className="bg-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-500 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default Admin;
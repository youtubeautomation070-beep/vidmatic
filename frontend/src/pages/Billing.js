import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../utils/api';
import { toast } from 'sonner';
import { Crown, Copy, Upload, CheckCircle, Clock, XCircle, Wallet, CreditCard } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';

const Billing = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [paymentMethods, setPaymentMethods] = useState({});
  const [plans, setPlans] = useState({});
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [selectedCurrency, setSelectedCurrency] = useState('usd');
  const [currentTransaction, setCurrentTransaction] = useState(null);
  const [proofFile, setProofFile] = useState(null);
  const [transactionHash, setTransactionHash] = useState('');
  const [notes, setNotes] = useState('');
  const [transactions, setTransactions] = useState([]);
  
  useEffect(() => {
    fetchUser();
    fetchPaymentMethods();
    fetchTransactions();
  }, []);
  
  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      navigate('/');
    }
  };
  
  const fetchPaymentMethods = async () => {
    try {
      const response = await api.get('/payments/methods');
      setPaymentMethods(response.data.payment_methods);
      setPlans(response.data.plans);
    } catch (error) {
      console.error('Failed to fetch payment methods:', error);
    }
  };
  
  const fetchTransactions = async () => {
    try {
      const response = await api.get('/payments/my-transactions');
      setTransactions(response.data.transactions);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    }
  };
  
  const handleSelectPlan = (planId) => {
    setSelectedPlan(planId);
    setCurrentTransaction(null);
  };
  
  const handleCreatePayment = async () => {
    if (!selectedPlan || !selectedMethod) {
      toast.error('Please select a plan and payment method');
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.post('/payments/create', {
        plan_id: selectedPlan,
        payment_method: selectedMethod,
        currency: selectedCurrency
      });
      
      setCurrentTransaction(response.data);
      toast.success('Payment initiated! Please complete payment and upload proof.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create payment');
    } finally {
      setLoading(false);
    }
  };
  
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setProofFile(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  
  const handleUploadProof = async () => {
    if (!proofFile) {
      toast.error('Please select a payment proof image');
      return;
    }
    
    setLoading(true);
    try {
      await api.post('/payments/upload-proof', {
        transaction_id: currentTransaction.transaction_id,
        proof_base64: proofFile,
        transaction_hash: transactionHash || null,
        notes: notes || null
      });
      
      toast.success('Payment proof uploaded! Waiting for admin verification.');
      setCurrentTransaction(null);
      setProofFile(null);
      setTransactionHash('');
      setNotes('');
      fetchTransactions();
      fetchUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload proof');
    } finally {
      setLoading(false);
    }
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };
  
  const getStatusBadge = (status) => {
    const badges = {
      'pending': { icon: Clock, color: 'text-yellow-400 bg-yellow-500/10', text: 'Pending' },
      'pending_verification': { icon: Clock, color: 'text-blue-400 bg-blue-500/10', text: 'Verifying' },
      'paid': { icon: CheckCircle, color: 'text-emerald-400 bg-emerald-500/10', text: 'Paid' },
      'failed': { icon: XCircle, color: 'text-red-400 bg-red-500/10', text: 'Failed' }
    };
    const badge = badges[status] || badges.pending;
    const Icon = badge.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3 h-3" />
        {badge.text}
      </span>
    );
  };
  
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Current Plan Card */}
        <div className="glass-card rounded-2xl p-6 md:p-8 border border-zinc-800 relative overflow-hidden mb-8">
          <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <Crown className="w-32 h-32 text-indigo-500" />
          </div>
          <div className="relative z-10">
            <div className="inline-block bg-indigo-500/20 text-indigo-400 text-xs font-semibold px-2 py-1 rounded mb-4">CURRENT PLAN</div>
            <h2 className="text-2xl md:text-3xl font-semibold text-white tracking-tight mb-2">
              {user?.subscription_plan === 'free_trial' && 'Free Trial'}
              {user?.subscription_plan === 'pro_monthly' && 'Pro Monthly'}
              {user?.subscription_plan === 'pro_yearly' && 'Pro Yearly'}
            </h2>
            <p className="text-sm text-zinc-400 mb-6">Active subscription</p>
            
            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 mb-6 max-w-md">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-zinc-300 font-medium">Credits Usage</span>
                <span className="text-white font-semibold">{user?.video_credits + user?.free_video_credits || 0} remaining</span>
              </div>
              {user?.free_video_credits > 0 && (
                <p className="text-xs text-emerald-400 mt-2">+ {user.free_video_credits} bonus credits from referrals!</p>
              )}
            </div>
            
            {!currentTransaction && (
              <Button 
                onClick={() => navigate('/dashboard')}
                className="bg-white text-black font-medium px-6 py-2 rounded-lg hover:bg-zinc-200 transition-colors"
              >
                Back to Dashboard
              </Button>
            )}
          </div>
        </div>
        
        {/* Upgrade Section */}
        {!currentTransaction && user?.subscription_plan === 'free_trial' && (
          <div className="mb-8">
            <h3 className="text-xl font-semibold mb-4">Upgrade Your Plan</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {Object.entries(plans).filter(([key]) => key !== 'free_trial').map(([key, plan]) => (
                <div 
                  key={key}
                  onClick={() => handleSelectPlan(key)}
                  className={`glass-card p-6 rounded-xl cursor-pointer transition-all ${
                    selectedPlan === key ? 'border-2 border-indigo-500 shadow-lg shadow-indigo-500/20' : 'border border-zinc-800'
                  }`}
                >
                  <h4 className="text-lg font-semibold text-white mb-2">
                    {key === 'pro_monthly' ? 'Pro Monthly' : 'Pro Yearly'}
                    {key === 'pro_yearly' && <span className="ml-2 text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full">Save 34%</span>}
                  </h4>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-3xl font-bold text-white">${plan.amount_usd}</span>
                    <span className="text-sm text-zinc-400">or PKR {plan.amount_pkr}</span>
                  </div>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                      {plan.credits} videos per {plan.duration}
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                      All premium features
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                      Priority support
                    </li>
                  </ul>
                </div>
              ))}
            </div>
            
            {selectedPlan && (
              <>
                {/* Currency Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-zinc-300 mb-2">Select Currency</label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setSelectedCurrency('usd')}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        selectedCurrency === 'usd' 
                          ? 'bg-indigo-600 text-white' 
                          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                      }`}
                    >
                      USD
                    </button>
                    <button
                      onClick={() => setSelectedCurrency('pkr')}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        selectedCurrency === 'pkr' 
                          ? 'bg-indigo-600 text-white' 
                          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                      }`}
                    >
                      PKR
                    </button>
                  </div>
                </div>
                
                {/* Payment Methods */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-3">Select Payment Method</label>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                    {Object.entries(paymentMethods).map(([key, method]) => (
                      <button
                        key={key}
                        onClick={() => setSelectedMethod(key)}
                        className={`p-4 rounded-lg text-left transition-all ${
                          selectedMethod === key
                            ? 'bg-indigo-600 text-white border-2 border-indigo-500'
                            : 'bg-zinc-800 text-zinc-300 border border-zinc-700 hover:bg-zinc-700'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {(key.includes('usdt') || key.includes('bank')) && <Wallet className="w-5 h-5" />}
                          {(key.includes('jazz') || key.includes('easy')) && <CreditCard className="w-5 h-5" />}
                          <span className="font-semibold">{method.name}</span>
                        </div>
                        {method.network && <p className="text-xs opacity-75">{method.network}</p>}
                      </button>
                    ))}
                  </div>
                  
                  <Button
                    onClick={handleCreatePayment}
                    disabled={!selectedPlan || !selectedMethod || loading}
                    className="w-full md:w-auto bg-gradient-primary text-white font-medium px-8 py-3 rounded-lg hover:shadow-lg disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : 'Proceed to Payment'}
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
        
        {/* Payment Details (After creating payment) */}
        {currentTransaction && (
          <div className="glass-card rounded-2xl p-6 md:p-8 border border-indigo-500 mb-8 animate-in fade-in duration-300">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Wallet className="w-6 h-6 text-indigo-400" />
              Payment Instructions
            </h3>
            
            <div className="bg-zinc-900 rounded-xl p-6 mb-6">
              <div className="flex flex-col md:flex-row gap-6">
                {/* QR Code */}
                <div className="flex-shrink-0">
                  <img 
                    src={currentTransaction.method_details.qr_code} 
                    alt="QR Code"
                    className="w-48 h-48 bg-white p-2 rounded-lg"
                  />
                </div>
                
                {/* Payment Details */}
                <div className="flex-1">
                  <h4 className="text-lg font-semibold mb-4 text-white">{currentTransaction.method_details.name}</h4>
                  
                  {currentTransaction.method_details.wallet_address && (
                    <div className="mb-4">
                      <label className="text-xs text-zinc-400 block mb-1">Wallet Address</label>
                      <div className="flex items-center gap-2 bg-zinc-800 p-3 rounded-lg">
                        <code className="text-sm text-white flex-1 truncate">{currentTransaction.method_details.wallet_address}</code>
                        <button 
                          onClick={() => copyToClipboard(currentTransaction.method_details.wallet_address)}
                          className="text-indigo-400 hover:text-indigo-300"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      {currentTransaction.method_details.network && (
                        <p className="text-xs text-zinc-500 mt-1">Network: {currentTransaction.method_details.network}</p>
                      )}
                    </div>
                  )}
                  
                  {currentTransaction.method_details.account_number && (
                    <div className="mb-4">
                      <label className="text-xs text-zinc-400 block mb-1">Account Number</label>
                      <div className="flex items-center gap-2 bg-zinc-800 p-3 rounded-lg">
                        <code className="text-sm text-white flex-1">{currentTransaction.method_details.account_number}</code>
                        <button 
                          onClick={() => copyToClipboard(currentTransaction.method_details.account_number)}
                          className="text-indigo-400 hover:text-indigo-300"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      {currentTransaction.method_details.account_name && (
                        <p className="text-xs text-zinc-500 mt-1">Name: {currentTransaction.method_details.account_name}</p>
                      )}
                    </div>
                  )}
                  
                  {currentTransaction.method_details.iban && (
                    <div className="mb-4">
                      <label className="text-xs text-zinc-400 block mb-1">IBAN</label>
                      <div className="flex items-center gap-2 bg-zinc-800 p-3 rounded-lg">
                        <code className="text-sm text-white flex-1">{currentTransaction.method_details.iban}</code>
                        <button 
                          onClick={() => copyToClipboard(currentTransaction.method_details.iban)}
                          className="text-indigo-400 hover:text-indigo-300"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )}
                  
                  <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-3">
                    <p className="text-lg font-semibold text-white mb-1">Amount to Pay</p>
                    <p className="text-2xl font-bold text-indigo-400">{currentTransaction.amount} {currentTransaction.currency}</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 p-4 bg-zinc-800 rounded-lg">
                <p className="text-sm text-zinc-300">{currentTransaction.method_details.instructions}</p>
              </div>
            </div>
            
            {/* Upload Proof Section */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold">Upload Payment Proof</h4>
              
              <div>
                <label className="block text-sm text-zinc-300 mb-2">Payment Screenshot/Receipt</label>
                <Input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="bg-zinc-900 border-zinc-800 text-white"
                />
              </div>
              
              {(selectedMethod === 'usdt_bep20' || selectedMethod === 'usdt_trc20') && (
                <div>
                  <label className="block text-sm text-zinc-300 mb-2">Transaction Hash (Optional)</label>
                  <Input
                    type="text"
                    placeholder="0x..."
                    value={transactionHash}
                    onChange={(e) => setTransactionHash(e.target.value)}
                    className="bg-zinc-900 border-zinc-800 text-white"
                  />
                </div>
              )}
              
              <div>
                <label className="block text-sm text-zinc-300 mb-2">Additional Notes (Optional)</label>
                <Textarea
                  rows={3}
                  placeholder="Any additional information..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="bg-zinc-900 border-zinc-800 text-white"
                />
              </div>
              
              <div className="flex gap-3">
                <Button
                  onClick={handleUploadProof}
                  disabled={!proofFile || loading}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                >
                  <Upload className="w-4 h-4" />
                  {loading ? 'Uploading...' : 'Submit Proof'}
                </Button>
                <Button
                  onClick={() => setCurrentTransaction(null)}
                  variant="outline"
                  className="border-zinc-700 text-white hover:bg-zinc-800"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {/* Transaction History */}
        {transactions.length > 0 && (
          <div className="glass-card rounded-2xl p-6 border border-zinc-800">
            <h3 className="text-xl font-semibold mb-4">Payment History</h3>
            <div className="space-y-3">
              {transactions.map(txn => (
                <div key={txn.transaction_id} className="bg-zinc-900 rounded-lg p-4 flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">{txn.plan.replace('_', ' ').toUpperCase()}</p>
                    <p className="text-sm text-zinc-400">{txn.amount} {txn.currency} • {new Date(txn.created_at).toLocaleDateString()}</p>
                    {txn.admin_notes && <p className="text-xs text-zinc-500 mt-1">Note: {txn.admin_notes}</p>}
                  </div>
                  <div>
                    {getStatusBadge(txn.payment_status)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Billing;
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';

const Admin = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white p-8">
      <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-2 rounded-lg text-xs font-medium mb-6 flex items-center gap-2">
        <Shield className="w-4 h-4" />
        Admin privileges active. Changes here affect the global platform.
      </div>
      
      <h1 className="text-3xl font-bold mb-4">Admin Dashboard</h1>
      <p className="text-zinc-400 mb-8">Manage platform users and content</p>
      
      <button 
        onClick={() => navigate('/dashboard')}
        className="bg-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-500"
      >
        Back to Dashboard
      </button>
    </div>
  );
};

export default Admin;
import React from 'react';
import { useNavigate } from 'react-router-dom';

const Library = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white p-8">
      <h1 className="text-3xl font-bold mb-4">My Videos</h1>
      <p className="text-zinc-400 mb-8">Your video library will appear here</p>
      <button 
        onClick={() => navigate('/dashboard')}
        className="bg-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-500"
      >
        Back to Dashboard
      </button>
    </div>
  );
};

export default Library;
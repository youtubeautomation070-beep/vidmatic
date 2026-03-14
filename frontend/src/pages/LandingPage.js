import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, Video, ImageIcon, Search, Calendar, BarChart3, UserCircle, Sparkles } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  
  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };
  
  return (
    <div className="antialiased selection:bg-indigo-500/30 selection:text-indigo-200 flex flex-col min-h-screen relative overflow-x-hidden bg-[#0a0a0c]">
      {/* Background Glows */}
      <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px]"></div>
        <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-fuchsia-600/10 blur-[120px]"></div>
      </div>
      
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md bg-gradient-primary flex items-center justify-center text-white">
              <PlayCircle className="w-5 h-5" />
            </div>
            <span className="font-bold tracking-tighter text-lg text-white">VIDMATIC</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-zinc-400 hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="text-sm text-zinc-400 hover:text-white transition-colors">Pricing</a>
            <a href="#faq" className="text-sm text-zinc-400 hover:text-white transition-colors">FAQ</a>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={handleLogin}
              className="text-sm text-zinc-300 hover:text-white transition-colors"
            >
              Sign In
            </button>
            <button 
              onClick={handleLogin}
              className="bg-gradient-primary text-white font-medium px-6 py-2 rounded-full hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-300 text-sm"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>
      
      {/* Hero Section */}
      <main className="flex-1 pt-32 pb-20 px-6 max-w-7xl mx-auto w-full flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-8 animate-pulse">
          <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
          Vidmatic AI v2.0 is live
        </div>
        
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-semibold tracking-tight leading-tight mb-6 max-w-4xl text-white">
          Turn Any Idea into a YouTube Video <span className="text-gradient">— Instantly.</span>
        </h1>
        
        <p className="text-base md:text-lg text-zinc-400 max-w-2xl mb-10 leading-relaxed">
          The all-in-one automation platform for creators. Generate faceless videos, stunning thumbnails, and SEO-optimized metadata from a single prompt. Publish directly to your channel.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center">
          <button 
            onClick={handleLogin}
            className="w-full sm:w-auto bg-gradient-primary text-white font-medium px-8 py-3.5 rounded-full hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-300 text-sm"
            data-testid="hero-get-started-btn"
          >
            Start Your Free Trial
          </button>
          <button className="w-full sm:w-auto glass-card text-white font-medium px-8 py-3.5 rounded-full hover:bg-zinc-800/50 transition-all duration-300 flex items-center justify-center gap-2 text-sm">
            <PlayCircle className="w-5 h-5" />
            View Demo Dashboard
          </button>
        </div>
        
        {/* Dashboard Mockup */}
        <div className="mt-20 w-full relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-fuchsia-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <div className="relative glass-card rounded-2xl p-2 border border-zinc-800 shadow-2xl">
            <div className="w-full aspect-[16/9] md:aspect-[21/9] bg-zinc-950 rounded-xl overflow-hidden relative flex flex-col">
              {/* Mockup Header */}
              <div className="h-10 border-b border-zinc-800/50 flex items-center px-4 gap-2 bg-zinc-900/50">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              {/* Mockup Body */}
              <div className="flex-1 flex p-4 gap-4 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LCAyNTUsIDI1NSwgMC4wNSkiLz48L3N2Zz4=')]">
                <div className="w-1/4 rounded-lg border border-zinc-800/50 bg-zinc-900/30 hidden md:block"></div>
                <div className="flex-1 rounded-lg border border-zinc-800/50 bg-zinc-900/80 p-6 flex flex-col justify-center items-center gap-4 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-primary"></div>
                  <Sparkles className="w-10 h-10 text-indigo-400" />
                  <div className="text-sm font-medium text-zinc-300">Generating script & visuals...</div>
                  <div className="w-64 h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 w-2/3 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      {/* Features Grid */}
      <section id="features" className="py-24 border-t border-zinc-800/50 bg-zinc-950/50 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-white mb-4">Everything you need to scale</h2>
            <p className="text-sm text-zinc-400 max-w-2xl mx-auto">Replace expensive editors, voiceover artists, and SEO experts with one powerful AI engine.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: <Video className="w-5 h-5" />,
                title: "AI Faceless Videos",
                desc: "Generate high-quality b-roll, transitions, and text overlays synced perfectly to human-like AI voiceovers.",
                color: "indigo"
              },
              {
                icon: <ImageIcon className="w-5 h-5" />,
                title: "Auto Thumbnails",
                desc: "Our vision model creates click-worthy, highly engaging thumbnails optimized for YouTube's algorithm.",
                color: "fuchsia"
              },
              {
                icon: <Search className="w-5 h-5" />,
                title: "SEO Title & Tags",
                desc: "Stop guessing. Get keyword-rich titles, descriptions, and tags generated instantly to rank higher.",
                color: "cyan"
              },
              {
                icon: <Calendar className="w-5 h-5" />,
                title: "Schedule & Auto-Publish",
                desc: "Connect your YouTube channel securely and let Vidmatic publish or schedule your content automatically.",
                color: "emerald"
              },
              {
                icon: <BarChart3 className="w-5 h-5" />,
                title: "Analytics Dashboard",
                desc: "Track views, engagement, and subscriber growth directly within your Vidmatic workspace.",
                color: "orange"
              },
              {
                icon: <UserCircle className="w-5 h-5" />,
                title: "Multiple Channels",
                desc: "Manage multiple niches and YouTube channels from a single centralized subscription.",
                color: "blue"
              },
            ].map((feature, idx) => (
              <div key={idx} className="glass-card p-6 rounded-2xl hover:bg-zinc-800/20 transition-colors">
                <div className={`w-10 h-10 rounded-lg bg-${feature.color}-500/10 flex items-center justify-center mb-4 text-${feature.color}-400`}>
                  {feature.icon}
                </div>
                <h3 className="text-base font-medium text-white mb-2">{feature.title}</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Pricing Section */}
      <section id="pricing" className="py-24 relative">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-white mb-4">Simple, transparent pricing</h2>
            <p className="text-sm text-zinc-400">Start free, upgrade when you're ready to scale</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                name: "Free Trial",
                price: "$0",
                period: "2 videos",
                features: ["2 video generations", "Basic features", "720p export", "Community support"],
                cta: "Start Free",
                highlighted: false
              },
              {
                name: "Pro Monthly",
                price: "$11",
                period: "/month",
                originalPrice: "$29",
                features: ["7 videos per month", "All features", "1080p export", "Priority processing", "Priority support"],
                cta: "Get Started",
                highlighted: true,
                badge: "Limited Time"
              },
              {
                name: "Pro Yearly",
                price: "$19",
                period: "/month",
                subtext: "Billed $228/year",
                features: ["15 videos per month", "All features", "4K export", "Priority processing", "Dedicated support"],
                cta: "Best Value",
                highlighted: false,
                badge: "Save 34%"
              },
            ].map((plan, idx) => (
              <div key={idx} className={`glass-card rounded-2xl p-6 relative ${
                plan.highlighted ? 'border-2 border-indigo-500 shadow-lg shadow-indigo-500/20' : ''
              }`}>
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                    {plan.badge}
                  </div>
                )}
                <div className="text-center mb-6">
                  <h3 className="text-lg font-semibold text-white mb-2">{plan.name}</h3>
                  <div className="flex items-baseline justify-center gap-2">
                    {plan.originalPrice && (
                      <span className="text-sm text-zinc-500 line-through">{plan.originalPrice}</span>
                    )}
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    <span className="text-sm text-zinc-400">{plan.period}</span>
                  </div>
                  {plan.subtext && (
                    <p className="text-xs text-zinc-500 mt-1">{plan.subtext}</p>
                  )}
                </div>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="text-sm text-zinc-300 flex items-center gap-2">
                      <span className="text-indigo-400">✓</span> {feature}
                    </li>
                  ))}
                </ul>
                <button 
                  onClick={handleLogin}
                  className={`w-full py-2.5 rounded-lg font-medium text-sm transition-all ${
                    plan.highlighted 
                      ? 'bg-gradient-primary text-white hover:shadow-lg' 
                      : 'glass-card text-white hover:bg-zinc-800'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-zinc-800/50 bg-zinc-950/80 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-zinc-500">
          © 2026 VIDMATIC. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
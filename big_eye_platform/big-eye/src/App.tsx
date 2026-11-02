import { useState, useEffect, useMemo } from 'react';
import { Shield, User, LogOut } from 'lucide-react';
import { useAuth } from './lib/auth-context';
import { useIsAdmin } from './lib/useIsAdmin';
import { isSupabaseConfigured } from './lib/supabase';
import AuthModal from './components/AuthModal';
import SecurityCommandCenter from './components/SecurityCommandCenter';
import MalwareTriage from './components/MalwareTriage';
import SyncAuditCenter from './components/SyncAuditCenter';
import ProviderControlRoom from './components/ProviderControlRoom';
import AllInOneAnalysis from './components/AllInOneAnalysis';
import EmailHeaderAnalyzer from './components/EmailHeaderAnalyzer';
import DomainChecker from './components/DomainChecker';
import EmailLegitimacyChecker from './components/EmailLegitimacyChecker';
import BlacklistScanner from './components/BlacklistScanner';
import IPIntelligence from './components/IPIntelligence';
import PhishingProbability from './components/PhishingProbability';
import TempEmailDetector from './components/TempEmailDetector';
import DomainAgeTracker from './components/DomainAgeTracker';
import LinkChecker from './components/LinkChecker';
import { AdminDashboard } from './components/AdminDashboard';
import DatabaseAnalysis from './components/DatabaseAnalysis';
import './App.css';

type Tool =
  | 'command-center'
  | 'all-in-one'
  | 'email-header'
  | 'domain-checker'
  | 'email-legitimacy'
  | 'blacklist'
  | 'ip-intelligence'
  | 'phishing-ai'
  | 'temp-email'
  | 'domain-age'
  | 'link-checker'
  | 'database-analysis'
  | 'malware-triage'
  | 'sync-audit'
  | 'integrations'
  | 'admin-dashboard';

const baseTools = [
  { id: 'command-center' as Tool, name: 'Command Center' },
  { id: 'all-in-one' as Tool, name: 'All in One Analysis' },
  { id: 'email-header' as Tool, name: 'Email Header Analyzer' },
  { id: 'domain-checker' as Tool, name: 'Domain Checker' },
  { id: 'email-legitimacy' as Tool, name: 'Email Legitimacy' },
  { id: 'blacklist' as Tool, name: 'Blacklist Scanner' },
  { id: 'ip-intelligence' as Tool, name: 'IP Intelligence' },
  { id: 'phishing-ai' as Tool, name: 'AI Phishing Detection' },
  { id: 'temp-email' as Tool, name: 'Temp Email Detector' },
  { id: 'domain-age' as Tool, name: 'Domain Age Tracker' },
  { id: 'link-checker' as Tool, name: 'Link Checker' },
  { id: 'database-analysis' as Tool, name: 'Database Analysis' },
  { id: 'malware-triage' as Tool, name: 'Malware Triage' },
  { id: 'sync-audit' as Tool, name: 'Sync & Audit' },
  { id: 'integrations' as Tool, name: 'API Control Room' },
];

function App() {
  const [activeTool, setActiveTool] = useState<Tool>('command-center');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user, loading, signOut } = useAuth();
  const { isAdmin } = useIsAdmin();

  // Memoize tools array to include admin dashboard if user is admin
  const tools = useMemo(() => {
    if (isAdmin) {
      return [...baseTools, { id: 'admin-dashboard' as Tool, name: 'Admin Dashboard' }];
    }
    return baseTools;
  }, [isAdmin]);

  // Authentication is enforced only when explicitly enabled for a deployed
  // environment. This keeps Vercel previews testable without a Supabase
  // project while preserving enterprise auth as a one-line env switch.
  useEffect(() => {
    const requireAuth = import.meta.env.VITE_REQUIRE_AUTH === 'true';
    if (requireAuth && isSupabaseConfigured && !loading && !user) {
      setShowAuthModal(true);
    }
  }, [loading, user]);

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <div className="min-h-screen bg-bg-near-black text-text-primary">
      {/* Auth Modal - Cannot be closed if user is not authenticated */}
      {showAuthModal && <AuthModal onClose={() => user && setShowAuthModal(false)} />}

      {/* Header */}
      <header className="h-16 bg-bg-near-black border-b border-border-subtle">
        <div className="h-full max-w-7xl mx-auto px-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-accent-primary" />
            <h1 className="text-2xl font-semibold text-text-primary">Big Eye</h1>
            <div className="flex flex-col">
              <span className="text-sm text-text-secondary font-semibold">A Revolution in Email Analysis</span>
              <span className="text-xs text-text-tertiary">We Ensure Authenticity with Accuracy</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <User className="w-4 h-4" />
                  <span>{user.email}</span>
                </div>
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary border border-border-subtle rounded-md hover:bg-bg-hover-surface transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            ) : isSupabaseConfigured ? (
              <button
                onClick={() => setShowAuthModal(true)}
                className="px-4 py-2 text-sm font-semibold bg-accent-primary text-white rounded-md hover:bg-accent-primary/90 transition-colors"
              >
                Sign In
              </button>
            ) : (
              <span className="rounded-full border border-blue-400/30 bg-blue-400/10 px-3 py-1.5 text-xs font-semibold text-blue-300">
                Preview mode · local analysis
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="bg-bg-near-black border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex overflow-x-auto scrollbar-hide">
            {tools.map((tool) => (
              <button
                key={tool.id}
                onClick={() => setActiveTool(tool.id)}
                className={`
                  px-6 py-3 text-sm font-semibold whitespace-nowrap transition-all duration-200
                  border-b-2 hover:bg-bg-hover-surface
                  ${
                    activeTool === tool.id
                      ? 'border-accent-primary text-text-primary bg-bg-hover-surface'
                      : 'border-transparent text-text-secondary'
                  }
                `}
              >
                {tool.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="animate-fade-in">
          {activeTool === 'all-in-one' && <AllInOneAnalysis />}
          {activeTool === 'command-center' && <SecurityCommandCenter />}
          {activeTool === 'email-header' && <EmailHeaderAnalyzer />}
          {activeTool === 'domain-checker' && <DomainChecker />}
          {activeTool === 'email-legitimacy' && <EmailLegitimacyChecker />}
          {activeTool === 'blacklist' && <BlacklistScanner />}
          {activeTool === 'ip-intelligence' && <IPIntelligence />}
          {activeTool === 'phishing-ai' && <PhishingProbability />}
          {activeTool === 'temp-email' && <TempEmailDetector />}
          {activeTool === 'domain-age' && <DomainAgeTracker />}
          {activeTool === 'link-checker' && <LinkChecker />}
          {activeTool === 'database-analysis' && <DatabaseAnalysis />}
          {activeTool === 'malware-triage' && <MalwareTriage />}
          {activeTool === 'sync-audit' && <SyncAuditCenter />}
          {activeTool === 'integrations' && <ProviderControlRoom />}
          {activeTool === 'admin-dashboard' && isAdmin && <AdminDashboard />}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 py-8 border-t border-border-subtle">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-text-tertiary">
          <p className="font-semibold">Big Eye - A Revolution in Email Analysis</p>
          <p className="mt-1">We Ensure Authenticity with Accuracy</p>
          <p className="mt-2 text-xs">Powered by MiniMax Agent</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

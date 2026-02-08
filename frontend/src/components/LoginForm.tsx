/**
 * Login Form Component
 */
import { useState } from 'react';
import { Lock, User, AlertCircle, Shield } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';

const SECURITY_LEVELS = [
  { level: 1, name: 'Top Secret', color: 'text-red-500', icon: '🔴' },
  { level: 2, name: 'Secret', color: 'text-orange-500', icon: '🟠' },
  { level: 3, name: 'Confidential', color: 'text-yellow-500', icon: '🟡' },
  { level: 4, name: 'Public', color: 'text-green-500', icon: '🟢' },
];

const DEMO_ACCOUNTS = [
  { username: 'admin', password: 'admin123', level: 1, access: 'All documents' },
  { username: 'researcher', password: 'research123', level: 2, access: 'Secret & below' },
  { username: 'analyst', password: 'analyst123', level: 3, access: 'Confidential & below' },
  { username: 'guest', password: 'guest123', level: 4, access: 'Public only' },
];

export function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (username && password) {
      await login(username, password);
    }
  };

  const handleDemoLogin = async (demoUsername: string, demoPassword: string) => {
    setUsername(demoUsername);
    setPassword(demoPassword);
    await login(demoUsername, demoPassword);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">On-Premise LLM</h1>
          <p className="text-slate-400">보안 등급 기반 문서 검색 시스템</p>
        </div>

        {/* Login Form */}
        <div className="bg-slate-800 rounded-xl shadow-xl p-8 border border-slate-700">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter password"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-400 text-sm">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          {/* Demo Accounts */}
          <div className="mt-8 pt-6 border-t border-slate-700">
            <p className="text-sm text-slate-400 mb-4 text-center">Demo Accounts</p>
            <div className="space-y-2">
              {DEMO_ACCOUNTS.map((account) => {
                const levelInfo = SECURITY_LEVELS.find((l) => l.level === account.level);
                return (
                  <button
                    key={account.username}
                    onClick={() => handleDemoLogin(account.username, account.password)}
                    className="w-full flex items-center justify-between p-3 bg-slate-900 hover:bg-slate-700 rounded-lg transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      <span>{levelInfo?.icon}</span>
                      <div>
                        <span className="text-white font-medium">{account.username}</span>
                        <span className="text-slate-500 text-sm ml-2">/ {account.password}</span>
                      </div>
                    </div>
                    <span className="text-xs text-slate-400">{account.access}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

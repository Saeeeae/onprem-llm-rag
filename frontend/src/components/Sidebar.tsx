/**
 * Sidebar Component
 */
import { useEffect, useState } from 'react';
import {
  User,
  Shield,
  Activity,
  LogOut,
  MessageSquare,
  Search,
  Settings,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { apiClient, QueueStatus } from '../api/client';

const SECURITY_LEVELS: Record<number, { name: string; icon: string; color: string }> = {
  1: { name: 'Top Secret', icon: '🔴', color: 'text-red-400' },
  2: { name: 'Secret', icon: '🟠', color: 'text-orange-400' },
  3: { name: 'Confidential', icon: '🟡', color: 'text-yellow-400' },
  4: { name: 'Public', icon: '🟢', color: 'text-green-400' },
};

interface SidebarProps {
  activeTab: 'chat' | 'search';
  onTabChange: (tab: 'chat' | 'search') => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const { user, logout } = useAuthStore();
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await apiClient.getQueueStatus();
        setQueueStatus(status);
      } catch {
        // Ignore errors
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const userLevel = user?.security_level || 4;
  const levelInfo = SECURITY_LEVELS[userLevel];

  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white">RAG System</h1>
            <p className="text-xs text-slate-500">On-Premise LLM</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        <button
          onClick={() => onTabChange('chat')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            activeTab === 'chat'
              ? 'bg-blue-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <MessageSquare className="w-5 h-5" />
          <span>Chat</span>
        </button>

        <button
          onClick={() => onTabChange('search')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            activeTab === 'search'
              ? 'bg-blue-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Search className="w-5 h-5" />
          <span>Search</span>
        </button>
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-3">
          <Activity className="w-4 h-4" />
          <span>System Status</span>
        </div>
        {queueStatus && (
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-800 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-white">
                {queueStatus.queue?.queued || 0}
              </div>
              <div className="text-xs text-slate-500">Queued</div>
            </div>
            <div className="bg-slate-800 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-white">
                {queueStatus.active_requests || 0}
              </div>
              <div className="text-xs text-slate-500">Active</div>
            </div>
          </div>
        )}
      </div>

      {/* User Info */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-slate-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-white truncate">{user?.username}</div>
            <div className="text-xs text-slate-500">{user?.department}</div>
          </div>
        </div>

        {/* Security Level */}
        <div className="bg-slate-800 rounded-lg p-3 mb-4">
          <div className="text-xs text-slate-500 mb-1">Security Clearance</div>
          <div className={`flex items-center gap-2 ${levelInfo.color}`}>
            <span>{levelInfo.icon}</span>
            <span className="font-medium">{levelInfo.name}</span>
          </div>
          <div className="text-xs text-slate-500 mt-2">Accessible Levels:</div>
          <div className="flex gap-1 mt-1">
            {user?.accessible_levels?.map((level) => (
              <span key={level} className="text-sm">
                {SECURITY_LEVELS[level]?.icon}
              </span>
            ))}
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}

/**
 * Main Application Component
 */
import { useEffect, useState } from 'react';
import { useAuthStore } from './stores/authStore';
import { LoginForm } from './components/LoginForm';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { SearchInterface } from './components/SearchInterface';
import { Loader2 } from 'lucide-react';

function App() {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'chat' | 'search'>('chat');

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <div className="min-h-screen bg-slate-900 flex">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 flex flex-col">
        {activeTab === 'chat' ? <ChatInterface /> : <SearchInterface />}
      </main>
    </div>
  );
}

export default App;

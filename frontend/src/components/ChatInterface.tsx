/**
 * Chat Interface Component
 */
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useChatStore } from '../stores/chatStore';
import { Source } from '../api/client';

const SECURITY_ICONS: Record<number, string> = {
  1: '🔴',
  2: '🟠',
  3: '🟡',
  4: '🟢',
};

const SECURITY_NAMES: Record<number, string> = {
  1: 'Top Secret',
  2: 'Secret',
  3: 'Confidential',
  4: 'Public',
};

function SourcesList({ sources }: { sources: Source[] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-3 border-t border-slate-700 pt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300 transition-colors"
      >
        <FileText className="w-4 h-4" />
        <span>Sources ({sources.length})</span>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, idx) => (
            <div key={idx} className="bg-slate-800 rounded-lg p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-200">
                  {SECURITY_ICONS[source.security_level]} {source.title}
                </span>
                <span className="text-slate-400 text-xs">
                  Score: {source.score.toFixed(3)}
                </span>
              </div>
              {source.source_path && (
                <div className="text-slate-500 text-xs mt-1 truncate">
                  {source.source_path}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MessageBubble({ role, content, sources }: { role: 'user' | 'assistant'; content: string; sources?: Source[] }) {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-slate-800 text-slate-200 border border-slate-700'
        }`}
      >
        {isUser ? (
          <p>{content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
        {!isUser && sources && <SourcesList sources={sources} />}
      </div>
    </div>
  );
}

export function ChatInterface() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, sendQuery, topK, setTopK, clearChat } = useChatStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');
    await sendQuery(query);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
        <h2 className="text-lg font-semibold text-white">Chat</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-400">Top K:</label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
            >
              {[3, 5, 10, 15, 20].map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={clearChat}
            className="text-sm text-slate-400 hover:text-white transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-slate-500 mt-20">
            <p className="text-lg mb-2">Welcome to On-Premise LLM</p>
            <p className="text-sm">Ask questions about your documents</p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
              sources={message.sources}
            />
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 rounded-2xl px-4 py-3 border border-slate-700">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}

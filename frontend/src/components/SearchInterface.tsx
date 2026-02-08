/**
 * Search Interface Component
 */
import { useState } from 'react';
import { Search, FileText, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';

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

interface SearchResult {
  id: string;
  content: string;
  security_level: number;
  source_path: string;
  document_title: string;
  score: number;
}

export function SearchInterface() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [topK, setTopK] = useState(10);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setSearched(true);

    try {
      const response = await apiClient.search(query.trim(), topK);
      setResults(response.documents);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-700">
        <h2 className="text-lg font-semibold text-white">Document Search</h2>
        <p className="text-sm text-slate-400">Search documents without AI generation</p>
      </div>

      {/* Search Form */}
      <div className="p-6 border-b border-slate-700">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter search terms..."
                className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded-xl px-4 text-white"
            >
              {[5, 10, 20, 30, 50].map((k) => (
                <option key={k} value={k}>
                  Top {k}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
            </button>
          </div>
        </form>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-6">
        {!searched ? (
          <div className="text-center text-slate-500 mt-20">
            <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Enter a search query to find documents</p>
          </div>
        ) : isLoading ? (
          <div className="text-center text-slate-500 mt-20">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin" />
            <p>Searching...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="text-center text-slate-500 mt-20">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No documents found matching your query</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-slate-400">
              Found {results.length} documents
            </p>
            {results.map((doc, idx) => (
              <div
                key={doc.id || idx}
                className="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{SECURITY_ICONS[doc.security_level]}</span>
                    <h3 className="font-medium text-white">{doc.document_title}</h3>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <span>{SECURITY_NAMES[doc.security_level]}</span>
                    <span>Score: {doc.score.toFixed(4)}</span>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mb-3 truncate">
                  {doc.source_path}
                </p>
                <p className="text-sm text-slate-300 line-clamp-3">
                  {doc.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

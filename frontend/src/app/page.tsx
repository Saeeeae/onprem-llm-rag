'use client'

import { FormEvent, useEffect, useState } from 'react'

type User = {
  id: string
  username: string
  department: string
  role: string
  is_superuser: boolean
}

type RetrievedDocument = {
  document_id: string
  filename: string
  score: number
  content: string
  metadata: {
    department?: string
    role?: string
    file_path?: string
  }
}

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  documents?: RetrievedDocument[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function requestJson(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || `Request failed (${response.status})`)
  }
  return data
}

export default function HomePage() {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [authError, setAuthError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'search'>('chat')

  const [chatQuery, setChatQuery] = useState('')
  const [chatTopK, setChatTopK] = useState(5)
  const [chatLoading, setChatLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const [searchQuery, setSearchQuery] = useState('')
  const [searchTopK, setSearchTopK] = useState(10)
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<RetrievedDocument[]>([])

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    if (!storedToken) {
      return
    }
    setToken(storedToken)
    requestJson('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${storedToken}` },
    })
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem('auth_token')
        setToken(null)
        setUser(null)
      })
  }, [])

  const login = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAuthError(null)
    try {
      const data = await requestJson('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      localStorage.setItem('auth_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      setPassword('')
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Login failed')
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
    setMessages([])
    setSearchResults([])
  }

  const sendChat = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!chatQuery.trim() || !token || chatLoading) {
      return
    }

    const query = chatQuery.trim()
    setChatQuery('')
    setChatLoading(true)
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content: query },
    ])

    try {
      const data = await requestJson('/api/v1/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query, top_k: chatTopK }),
      })
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.response,
          documents: data.retrieved_documents,
        },
      ])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: error instanceof Error ? error.message : 'Chat request failed',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  const runSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!searchQuery.trim() || !token || searchLoading) {
      return
    }

    setSearchLoading(true)
    try {
      const data = await requestJson('/api/v1/chat/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query: searchQuery.trim(), top_k: searchTopK }),
      })
      setSearchResults(data.documents || [])
    } catch {
      setSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }

  if (!user) {
    return (
      <main className="page-shell">
        <section className="card login-card">
          <h1>On-Premise LLM</h1>
          <p>Department + Role RBAC</p>
          <form onSubmit={login} className="form-stack">
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              autoComplete="username"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              autoComplete="current-password"
            />
            <button type="submit">Login</button>
            {authError && <div className="error-text">{authError}</div>}
          </form>
        </section>
      </main>
    )
  }

  return (
    <main className="page-shell">
      <section className="card app-card">
        <header className="topbar">
          <div>
            <h1>On-Premise LLM</h1>
            <p>
              {user.username} | {user.department} | {user.role}
            </p>
          </div>
          <button onClick={logout}>Logout</button>
        </header>

        <nav className="tabs">
          <button
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button
            className={activeTab === 'search' ? 'active' : ''}
            onClick={() => setActiveTab('search')}
          >
            Search
          </button>
        </nav>

        {activeTab === 'chat' ? (
          <div className="panel">
            <form className="toolbar" onSubmit={sendChat}>
              <label>
                Top K
                <select value={chatTopK} onChange={(e) => setChatTopK(Number(e.target.value))}>
                  {[3, 5, 10, 20].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <button type="button" onClick={() => setMessages([])}>
                Clear
              </button>
            </form>

            <div className="chat-window">
              {messages.map((message) => (
                <article key={message.id} className={message.role === 'user' ? 'msg user' : 'msg'}>
                  <div>{message.content}</div>
                  {message.documents && message.documents.length > 0 && (
                    <details>
                      <summary>Sources ({message.documents.length})</summary>
                      {message.documents.map((doc, idx) => (
                        <div key={`${message.id}-${doc.document_id}-${idx}`} className="source-item">
                          <strong>{doc.filename}</strong> | score {doc.score.toFixed(3)} |{' '}
                          {doc.metadata.department}/{doc.metadata.role}
                        </div>
                      ))}
                    </details>
                  )}
                </article>
              ))}
              {chatLoading && <div className="status-text">Generating response...</div>}
            </div>

            <form className="query-form" onSubmit={sendChat}>
              <input
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
                placeholder="Ask about your indexed documents..."
              />
              <button type="submit" disabled={chatLoading}>
                Send
              </button>
            </form>
          </div>
        ) : (
          <div className="panel">
            <form className="query-form" onSubmit={runSearch}>
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents (retrieve only)..."
              />
              <select
                value={searchTopK}
                onChange={(e) => setSearchTopK(Number(e.target.value))}
              >
                {[5, 10, 20, 30].map((value) => (
                  <option key={value} value={value}>
                    Top {value}
                  </option>
                ))}
              </select>
              <button type="submit" disabled={searchLoading}>
                Search
              </button>
            </form>

            <div className="search-results">
              {searchLoading && <div className="status-text">Searching...</div>}
              {!searchLoading && searchResults.length === 0 && (
                <div className="status-text">No results yet.</div>
              )}
              {searchResults.map((doc, idx) => (
                <article key={`${doc.document_id}-${idx}`} className="source-item">
                  <h3>{doc.filename}</h3>
                  <p>
                    {doc.metadata.department}/{doc.metadata.role} | score {doc.score.toFixed(3)}
                  </p>
                  <p>{doc.content}</p>
                </article>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

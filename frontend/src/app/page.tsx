'use client'

import { useState } from 'react'

export default function ChatPage() {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([])
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setMessages(prev => [...prev, { role: 'user', content: query }])

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ query }),
      })

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      setQuery('')
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">On-Premise LLM Chat</h1>
      
      <div className="bg-gray-100 rounded-lg p-4 mb-4 h-96 overflow-y-auto">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 p-3 border rounded-lg"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-400"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

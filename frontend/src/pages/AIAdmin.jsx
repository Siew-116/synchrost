import { useState, useRef, useEffect } from 'react'
import { Bot, Send, Wrench } from 'lucide-react'

const API = '/api'

export default function AIAdmin() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'I am your AI Co-Admin. I can answer questions about orders, customers, supplier summaries, and exceptions. I can also draft announcements and summarise activity while you were studying.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const resp = await fetch(`${API}/agent/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input }),
      })
      const data = await resp.json()
      setMessages(prev => [...prev, { role: 'ai', content: data.response, mode: data.mode }])
    } catch {
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I could not process that request.', error: true }])
    }
    setLoading(false)
  }

  const suggestions = [
    'How many orders have been placed?',
    'Which orders are incomplete?',
    'Prepare the final supplier quantity list',
    'Show customers who have not completed payment',
    'Draft an announcement that ordering closes tonight',
    'Summarise what happened while I was studying',
  ]

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">AI Co-Admin</h1>
      <p className="text-sm text-stone-500 mb-6">Ask your AI assistant about business operations</p>

      <div className="card p-0 overflow-hidden flex flex-col" style={{ height: '60vh' }}>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' ? 'bg-blue-100' : msg.role === 'system' ? 'bg-stone-100' : 'bg-brand-100'
              }`}>
                {msg.role === 'user' ? <span className="text-xs font-medium text-blue-600">You</span> : <Bot size={16} className="text-brand-600" />}
              </div>
              <div className={`rounded-lg p-3 max-w-md ${
                msg.role === 'user' ? 'bg-blue-50 text-blue-900' : 'bg-stone-50 text-stone-700'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.mode === 'demo' && (
                  <p className="text-xs text-stone-400 mt-2">Simulated AI (deterministic mode)</p>
                )}
                {msg.error && (
                  <p className="text-xs text-red-400 mt-2">Action failed</p>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center">
                <Bot size={16} className="text-brand-600" />
              </div>
              <div className="bg-stone-50 rounded-lg p-3">
                <span className="text-sm text-stone-400">Processing...</span>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input */}
        <div className="border-t border-stone-200 p-3 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Ask about orders, customers, summaries..."
            className="flex-1 px-3 py-2 rounded-lg border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button onClick={send} disabled={loading || !input.trim()} className="btn btn-primary flex items-center gap-2">
            <Send size={16} /> Send
          </button>
        </div>
      </div>

      {/* Suggestions */}
      <div className="mt-4">
        <p className="text-xs text-stone-500 mb-2">Try asking:</p>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => setInput(s)}
              className="btn btn-secondary text-xs"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

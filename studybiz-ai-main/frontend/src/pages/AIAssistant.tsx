import { useState, useRef, useEffect } from 'react'
import { agentAPI } from '../services/api'
import { Send, Bot, User, Loader2 } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  actions?: any[]
  approvals?: any[]
  mode?: string
}

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm your StudyBiz AI assistant. I can help you manage your academic schedule, business orders, inventory, and more.\n\nTry asking:\n• \"I have an exam tomorrow and 15 orders to pack\"\n• \"Which paid orders need packaging?\"\n• \"Check my schedule for conflicts\"\n• \"Calculate my outstanding payments\"",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setInput('')
    setLoading(true)

    try {
      const res = await agentAPI.chat(userMsg)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.response,
        actions: res.data.actions_taken,
        approvals: res.data.approval_requests,
        mode: res.data.mode || 'deterministic',
      }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  const quickPrompts = [
    "I have an exam tomorrow at 9 AM, 15 paid orders to pack, and a shipping cutoff at 5 PM",
    "Which paid orders need packaging?",
    "Calculate my outstanding customer payments",
    "Check my schedule for conflicts",
  ]

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-120px)] flex flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
        <p className="text-sm text-gray-500">Your academic & business operations agent</p>
      </div>

      <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-gray-100 p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' ? 'bg-primary-100 text-primary-600' : 'bg-gradient-to-br from-primary-500 to-accent-500 text-white'
            }`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'bg-primary-50' : 'bg-gray-50'} rounded-xl p-3`}>
              <pre className="whitespace-pre-wrap text-sm text-gray-800 font-sans">{msg.content}</pre>
              {msg.actions && msg.actions.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-500 mb-1">Actions taken:</p>
                  {msg.actions.map((a: any, j: number) => (
                    <div key={j} className="text-xs text-gray-600 flex items-center gap-1">
                      <span className={`w-1.5 h-1.5 rounded-full ${a.success ? 'bg-success-500' : 'bg-danger-500'}`} />
                      {a.tool} {a.requires_approval ? '(needs approval)' : ''}
                    </div>
                  ))}
                </div>
              )}
              {msg.approvals && msg.approvals.length > 0 && (
                <div className="mt-2 p-2 bg-warning-50 rounded-lg">
                  <p className="text-xs font-medium text-warning-600">Approval needed for {msg.approvals.length} action(s)</p>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 text-white flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-gray-50 rounded-xl p-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
              <span className="text-sm text-gray-500">Analyzing...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Quick prompts */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {quickPrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => setInput(p)}
              className="px-3 py-1.5 text-xs bg-white border border-gray-200 rounded-full text-gray-600 hover:border-primary-300 hover:text-primary-600"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask me anything about your schedule, orders, or business..."
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}

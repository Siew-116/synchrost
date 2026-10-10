import { useState, useEffect } from 'react'
import { Send } from 'lucide-react'

const API = '/api'

export default function SettingsPage() {
  const [settings, setSettings] = useState(null)
  const [telegramStatus, setTelegramStatus] = useState(null)
  const [simulation, setSimulation] = useState({ display_name: '', text: '' })
  const [simResult, setSimResult] = useState(null)
  const [simLoading, setSimLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/settings`).then(r => r.json()).then(setSettings)
    fetch(`${API}/telegram/status`).then(r => r.json()).then(setTelegramStatus)
  }, [])

  const simulate = async () => {
    if (!simulation.display_name || !simulation.text) return
    setSimLoading(true)
    const resp = await fetch(`${API}/agent/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(simulation),
    })
    const data = await resp.json()
    setSimResult(data)
    setSimLoading(false)
  }

  if (!settings) return <div className="p-8 text-stone-500">Loading...</div>

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Settings</h1>
      <p className="text-sm text-stone-500 mb-6">Application configuration and integration status</p>

      {/* Status */}
      <div className="card mb-6">
        <h2 className="text-sm font-semibold text-stone-700 mb-4">Integration Status</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-stone-50 rounded-lg p-3">
            <p className="text-xs text-stone-400">Application Mode</p>
            <p className="font-medium text-stone-700">
              {settings.mode_label}
              {settings.demo_mode && <span className="badge badge-amber ml-2">Demo</span>}
            </p>
          </div>
          <div className="bg-stone-50 rounded-lg p-3">
            <p className="text-xs text-stone-400">Exam Mode</p>
            <p className="font-medium text-stone-700">
              {settings.exam_mode ? 'Active' : 'Inactive'}
            </p>
          </div>
        </div>
      </div>

      {/* Telegram Status */}
      <div className="card mb-6">
        <h2 className="text-sm font-semibold text-stone-700 mb-4">Telegram Integration</h2>
        {telegramStatus && (
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <span className={`inline-block w-2 h-2 rounded-full ${
                telegramStatus.connected ? 'bg-green-500' : 'bg-amber-500'
              }`}></span>
              <span className="text-stone-700">
                {telegramStatus.connected ? 'Connected to Telegram' : 'Demo mode (not connected)'}
              </span>
            </div>
            <div className="bg-stone-50 rounded-lg p-3 space-y-1">
              <p className="text-xs text-stone-400">Bot Token: {telegramStatus.bot_token_configured ? 'Configured' : 'Not configured'}</p>
              <p className="text-xs text-stone-400">Webhook URL: {telegramStatus.webhook_url || 'Not set'}</p>
              <p className="text-xs text-stone-400">Mode: {telegramStatus.mode}</p>
            </div>
            {!telegramStatus.connected && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs text-amber-800">
                  To connect Telegram: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CONNECTED=true in .env,
                  then configure your webhook URL to point to /api/telegram/webhook.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Simulated Message Tester */}
      <div className="card mb-6">
        <h2 className="text-sm font-semibold text-stone-700 mb-4">Simulated Customer Message</h2>
        <p className="text-xs text-stone-500 mb-3">
          Test the AI agent by simulating a customer message. This exercises the same backend and business rules as real Telegram messages.
        </p>
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Customer name (e.g. Aisyah)"
            value={simulation.display_name}
            onChange={e => setSimulation({...simulation, display_name: e.target.value})}
            className="w-full px-3 py-2 rounded-lg border border-stone-200 text-sm"
          />
          <input
            type="text"
            placeholder="Message (e.g. Hi, can I order two black hoodies size M?)"
            value={simulation.text}
            onChange={e => setSimulation({...simulation, text: e.target.value})}
            onKeyDown={e => e.key === 'Enter' && simulate()}
            className="w-full px-3 py-2 rounded-lg border border-stone-200 text-sm"
          />
          <button
            onClick={simulate}
            disabled={simLoading || !simulation.display_name || !simulation.text}
            className="btn btn-primary text-sm flex items-center gap-2"
          >
            <Send size={14} /> {simLoading ? 'Processing...' : 'Send'}
          </button>
        </div>

        {simResult && (
          <div className="mt-4 bg-brand-50 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center flex-shrink-0">
                <Bot size={16} className="text-brand-600" />
              </div>
              <div>
                <p className="text-xs font-medium text-stone-400 mb-1">AI Response</p>
                <p className="text-sm text-stone-700">{simResult.response}</p>
                {simResult.intent && (
                  <p className="text-xs text-stone-400 mt-2">Intent: {simResult.intent.replace(/_/g, ' ')}</p>
                )}
                {simResult.exception && (
                  <p className="text-xs text-amber-600 mt-1">Exception created and forwarded to admin.</p>
                )}
                {simResult.order_id && (
                  <p className="text-xs text-blue-600 mt-1">Order #{simResult.order_id} created/updated.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Environment Configuration */}
      <div className="card">
        <h2 className="text-sm font-semibold text-stone-700 mb-4">Environment Variables</h2>
        <p className="text-xs text-stone-500 mb-3">
          Configure these in the .env file. See .env.example for details.
        </p>
        <div className="bg-stone-900 rounded-lg p-4 text-xs text-stone-300 font-mono overflow-x-auto">
          <pre>{`# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CONNECTED=false

# AI / LLM (optional - demo mode without it)
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini

# Modes
DEMO_MODE=true
EXAM_MODE=false`}</pre>
        </div>
      </div>
    </div>
  )
}

function Bot({ size, className }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="18" height="10" x="3" y="11" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" x2="8" y1="16" y2="16" />
      <line x1="16" x2="16" y1="16" y2="16" />
    </svg>
  )
}

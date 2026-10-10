import { useState, useEffect } from 'react'
import { Send, User } from 'lucide-react'

const API = '/api'

export default function InboxPage() {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    fetch(`${API}/inbox/conversations`)
      .then(r => r.json())
      .then(d => { setConversations(d); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const openConv = (id) => {
    fetch(`${API}/inbox/conversations/${id}`)
      .then(r => r.json())
      .then(setSelected)
  }

  const resolve = (id) => {
    fetch(`${API}/inbox/conversations/${id}/resolve`, { method: 'POST' })
      .then(() => { load(); setSelected(null) })
  }

  const escalate = (id) => {
    fetch(`${API}/inbox/conversations/${id}/escalate`, { method: 'POST' })
      .then(() => { load(); setSelected(null) })
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Customer Inbox</h1>
      <p className="text-sm text-stone-500 mb-6">Incoming customer enquiries</p>

      <div className="flex gap-6">
        {/* Conversation List */}
        <div className="w-1/3">
          <div className="card p-0 overflow-hidden">
            {loading ? (
              <p className="p-4 text-sm text-stone-400">Loading...</p>
            ) : conversations.length === 0 ? (
              <p className="p-4 text-sm text-stone-400">No conversations.</p>
            ) : conversations.map(c => (
              <div
                key={c.id}
                onClick={() => openConv(c.id)}
                className={`p-4 border-b border-stone-100 cursor-pointer hover:bg-stone-50 ${
                  selected?.id === c.id ? 'bg-brand-50' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-stone-700">{c.customer}</span>
                  <span className={`badge ${
                    c.status === 'open' ? 'badge-amber' :
                    c.status === 'resolved' ? 'badge-green' : 'badge-red'
                  }`}>{c.status}</span>
                </div>
                <p className="text-xs text-stone-500 truncate">{c.last_message}</p>
                {c.last_intent && (
                  <p className="text-xs text-stone-400 mt-1">Intent: {c.last_intent.replace(/_/g, ' ')}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Conversation Detail */}
        <div className="flex-1">
          {selected ? (
            <div className="card p-0 overflow-hidden flex flex-col" style={{ height: '70vh' }}>
              <div className="p-4 border-b border-stone-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <User size={16} className="text-stone-400" />
                  <span className="font-medium text-stone-700">{selected.customer}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => resolve(selected.id)} className="btn btn-secondary text-xs">Resolve</button>
                  <button onClick={() => escalate(selected.id)} className="btn btn-secondary text-xs">Escalate</button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {selected.messages.map(m => (
                  <div key={m.id} className={`flex gap-2 ${m.sender_type === 'customer' ? 'flex-row' : 'flex-row-reverse'}`}>
                    <div className={`rounded-lg p-3 max-w-md text-sm ${
                      m.sender_type === 'customer' ? 'bg-amber-50 text-stone-700' :
                      m.sender_type === 'ai' ? 'bg-brand-50 text-stone-700' : 'bg-stone-50 text-stone-700'
                    }`}>
                      <p className="text-xs font-medium text-stone-400 mb-1">{m.sender_type}</p>
                      <p>{m.content}</p>
                      {m.intent && m.intent !== 'response' && (
                        <p className="text-xs text-stone-400 mt-1">Intent: {m.intent.replace(/_/g, ' ')}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Related Orders */}
              {selected.related_orders && selected.related_orders.length > 0 && (
                <div className="border-t border-stone-200 p-3">
                  <p className="text-xs font-medium text-stone-500 mb-2">Related Orders</p>
                  <div className="flex flex-wrap gap-2">
                    {selected.related_orders.map(o => (
                      <span key={o.id} className="badge badge-blue">#{o.id} - {o.status}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <p className="text-stone-400">Select a conversation to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

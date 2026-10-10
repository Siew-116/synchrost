import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, HelpCircle } from 'lucide-react'

const API = '/api'

export default function Approvals() {
  const [exceptions, setExceptions] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    fetch(`${API}/exceptions`)
      .then(r => r.json())
      .then(d => { setExceptions(d); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const resolve = (id, action) => {
    fetch(`${API}/exceptions/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    }).then(() => load())
  }

  if (loading) return <div className="p-8 text-stone-500">Loading...</div>

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Approvals & Exceptions</h1>
      <p className="text-sm text-stone-500 mb-6">Resolve escalated cases and exceptions</p>

      {exceptions.length === 0 ? (
        <div className="card text-center py-12">
          <CheckCircle className="mx-auto text-green-500 mb-2" size={32} />
          <p className="text-stone-500">No open exceptions. All clear.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {exceptions.map(e => (
            <div key={e.id} className="card border-l-4 border-l-amber-500">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="badge badge-amber">{e.type.replace(/_/g, ' ')}</span>
                    {e.order && (
                      <span className="badge badge-blue">Order #{e.order.id}</span>
                    )}
                  </div>
                  <p className="text-sm text-stone-600 mt-2">{e.description}</p>
                </div>
              </div>

              {e.order && (
                <div className="bg-stone-50 rounded-lg p-3 mb-3 text-sm">
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <p className="text-xs text-stone-400">Customer</p>
                      <p className="text-stone-700">{e.order.customer}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-400">Status</p>
                      <p className="text-stone-700">{e.order.status}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-400">Total</p>
                      <p className="text-stone-700">RM{e.order.total_amount.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
              )}

              {e.recommended_action && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-stone-500 mb-1">Recommended Action</p>
                  <p className="text-sm text-stone-600">{e.recommended_action}</p>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => resolve(e.id, 'approved')}
                  className="btn btn-primary text-xs flex items-center gap-1"
                >
                  <CheckCircle size={14} /> Approve
                </button>
                <button
                  onClick={() => resolve(e.id, 'rejected')}
                  className="btn btn-danger text-xs flex items-center gap-1"
                >
                  <XCircle size={14} /> Reject
                </button>
                <button
                  onClick={() => resolve(e.id, 'more_info')}
                  className="btn btn-secondary text-xs flex items-center gap-1"
                >
                  <HelpCircle size={14} /> Request Info
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

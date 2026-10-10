import { useState, useEffect } from 'react'

const API = '/api'

export default function GroupBuys() {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    fetch(`${API}/campaigns`)
      .then(r => r.json())
      .then(d => { setCampaigns(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-stone-500">Loading...</div>

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Group Buys</h1>
      <p className="text-sm text-stone-500 mb-6">Manage your group buy campaigns</p>

      {campaigns.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-stone-500">No campaigns yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns.map(c => (
            <div key={c.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h2 className="text-lg font-semibold text-stone-900">{c.name}</h2>
                  <p className="text-sm text-stone-500 mt-1">{c.description}</p>
                </div>
                <span className={`badge ${
                  c.status === 'open' ? 'badge-green' :
                  c.status === 'closed' ? 'badge-grey' :
                  c.status === 'closing_soon' ? 'badge-amber' : 'badge-blue'
                }`}>
                  {c.status.replace(/_/g, ' ')}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-xs text-stone-400">Total Orders</p>
                  <p className="font-semibold text-stone-700">{c.total_orders}</p>
                </div>
                <div>
                  <p className="text-xs text-stone-400">Opens</p>
                  <p className="font-medium text-stone-600">
                    {c.opens_at ? new Date(c.opens_at).toLocaleDateString() : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-stone-400">Closes</p>
                  <p className="font-medium text-stone-600">
                    {c.closes_at ? new Date(c.closes_at).toLocaleDateString() : 'No deadline'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-stone-400">Late Order Policy</p>
                  <p className="font-medium text-stone-600">{c.late_order_policy.replace(/_/g, ' ')}</p>
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => {
                    fetch(`${API}/campaigns/${c.id}`)
                      .then(r => r.json())
                      .then(setSelected)
                  }}
                  className="btn btn-secondary text-xs"
                >
                  View Details
                </button>
                {c.status === 'open' && (
                  <button
                    onClick={() => {
                      fetch(`${API}/campaigns/${c.id}/close`, { method: 'POST' })
                        .then(() => window.location.reload())
                    }}
                    className="btn btn-secondary text-xs"
                  >
                    Close Ordering
                  </button>
                )}
                <button
                  onClick={() => window.location.href = `/supplier`}
                  className="btn btn-secondary text-xs"
                >
                  Supplier Summary
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">{selected.name}</h2>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-stone-700 mb-2">Products & Variants</h3>
              {selected.products.map(p => (
                <div key={p.id} className="bg-stone-50 rounded-lg p-3 mb-2">
                  <p className="text-sm font-medium text-stone-700">{p.name} - RM{p.price.toFixed(2)}</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {p.variants.map(v => (
                      <span key={v.id} className="badge badge-blue">{v.attributes} ({v.available_quantity} available)</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-stone-700 mb-2">Order Totals by Variant</h3>
              <div className="bg-stone-50 rounded-lg p-3">
                {Object.entries(selected.variant_totals.totals_by_variant || {}).map(([variant, qty]) => (
                  <div key={variant} className="flex justify-between text-sm py-1">
                    <span className="text-stone-600">{variant}</span>
                    <span className="font-medium text-stone-800">{qty}</span>
                  </div>
                ))}
                <div className="border-t border-stone-200 mt-2 pt-2 flex justify-between text-sm font-semibold">
                  <span>Total Units</span>
                  <span>{selected.variant_totals.total_units}</span>
                </div>
              </div>
            </div>

            <div className="text-sm text-stone-600">
              <p><strong>Payment Instructions:</strong> {selected.payment_instructions}</p>
            </div>

            <button onClick={() => setSelected(null)} className="btn btn-secondary mt-4">Close</button>
          </div>
        </div>
      )}
    </div>
  )
}

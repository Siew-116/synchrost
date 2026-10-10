import { useState, useEffect } from 'react'

const API = '/api'

export default function Customers() {
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    fetch(`${API}/customers`)
      .then(r => r.json())
      .then(d => { setCustomers(d); setLoading(false) })
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Customers</h1>
      <p className="text-sm text-stone-500 mb-6">Customer records and order history</p>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 border-b border-stone-200">
            <tr>
              <th className="text-left p-3 font-medium text-stone-600">ID</th>
              <th className="text-left p-3 font-medium text-stone-600">Name</th>
              <th className="text-left p-3 font-medium text-stone-600">Telegram ID</th>
              <th className="text-left p-3 font-medium text-stone-600">Username</th>
              <th className="text-left p-3 font-medium text-stone-600">Orders</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="5" className="p-8 text-center text-stone-400">Loading...</td></tr>
            ) : customers.length === 0 ? (
              <tr><td colSpan="5" className="p-8 text-center text-stone-400">No customers.</td></tr>
            ) : customers.map(c => (
              <tr
                key={c.id}
                onClick={() => {
                  fetch(`${API}/customers/${c.id}`).then(r => r.json()).then(setSelected)
                }}
                className="border-b border-stone-100 hover:bg-stone-50 cursor-pointer"
              >
                <td className="p-3 text-stone-600">#{c.id}</td>
                <td className="p-3 text-stone-700">{c.display_name}</td>
                <td className="p-3 text-stone-600 font-mono text-xs">{c.telegram_user_id || '-'}</td>
                <td className="p-3 text-stone-600">@{c.telegram_username || '-'}</td>
                <td className="p-3 text-stone-700">{c.order_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">{selected.display_name}</h2>
            <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
              <div>
                <p className="text-xs text-stone-400">Telegram User ID</p>
                <p className="font-mono text-stone-700">{selected.telegram_user_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-stone-400">Username</p>
                <p className="text-stone-700">@{selected.telegram_username || 'N/A'}</p>
              </div>
            </div>

            <h3 className="text-sm font-semibold text-stone-700 mb-2">Order History</h3>
            <div className="space-y-2">
              {selected.orders.length === 0 ? (
                <p className="text-sm text-stone-400">No orders.</p>
              ) : selected.orders.map(o => (
                <div key={o.id} className="bg-stone-50 rounded-lg p-3 text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="font-medium text-stone-700">Order #{o.id}</span>
                    <span className="text-stone-600">RM{o.total_amount.toFixed(2)}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="badge badge-grey">{o.status}</span>
                    <span className="badge badge-grey">{o.payment_status}</span>
                  </div>
                  <div className="text-xs text-stone-500 mt-1">
                    {o.items.map(i => `${i.quantity}x ${i.variant}`).join(', ')}
                  </div>
                </div>
              ))}
            </div>

            <button onClick={() => setSelected(null)} className="btn btn-secondary mt-4">Close</button>
          </div>
        </div>
      )}
    </div>
  )
}

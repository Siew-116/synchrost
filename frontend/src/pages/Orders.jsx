import { useState, useEffect } from 'react'

const API = '/api'

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ status: '', payment_status: '', search: '' })
  const [selected, setSelected] = useState(null)

  const load = () => {
    const params = new URLSearchParams()
    if (filters.status) params.set('status', filters.status)
    if (filters.payment_status) params.set('payment_status', filters.payment_status)
    if (filters.search) params.set('search', filters.search)
    fetch(`${API}/orders?${params}`)
      .then(r => r.json())
      .then(d => { setOrders(d); setLoading(false) })
  }

  useEffect(() => { load() }, [filters.status, filters.payment_status])

  const statusBadge = (s) => {
    const map = {
      draft: 'badge-grey', pending_payment: 'badge-amber',
      confirmed: 'badge-green', cancelled: 'badge-red', completed: 'badge-blue',
    }
    return map[s] || 'badge-grey'
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Orders</h1>
      <p className="text-sm text-stone-500 mb-6">All customer orders</p>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          value={filters.status}
          onChange={e => setFilters({...filters, status: e.target.value})}
          className="px-3 py-2 rounded-lg border border-stone-200 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="pending_payment">Pending Payment</option>
          <option value="confirmed">Confirmed</option>
          <option value="cancelled">Cancelled</option>
          <option value="completed">Completed</option>
        </select>
        <select
          value={filters.payment_status}
          onChange={e => setFilters({...filters, payment_status: e.target.value})}
          className="px-3 py-2 rounded-lg border border-stone-200 text-sm"
        >
          <option value="">All Payments</option>
          <option value="unpaid">Unpaid</option>
          <option value="payment_submitted">Submitted</option>
          <option value="verifying">Verifying</option>
          <option value="paid">Paid</option>
          <option value="rejected">Rejected</option>
        </select>
        <input
          type="text"
          placeholder="Search customer..."
          value={filters.search}
          onChange={e => setFilters({...filters, search: e.target.value})}
          onKeyDown={e => e.key === 'Enter' && load()}
          className="px-3 py-2 rounded-lg border border-stone-200 text-sm flex-1 max-w-xs"
        />
        <button onClick={load} className="btn btn-secondary text-sm">Search</button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 border-b border-stone-200">
            <tr>
              <th className="text-left p-3 font-medium text-stone-600">ID</th>
              <th className="text-left p-3 font-medium text-stone-600">Customer</th>
              <th className="text-left p-3 font-medium text-stone-600">Items</th>
              <th className="text-left p-3 font-medium text-stone-600">Total</th>
              <th className="text-left p-3 font-medium text-stone-600">Status</th>
              <th className="text-left p-3 font-medium text-stone-600">Payment</th>
              <th className="text-left p-3 font-medium text-stone-600">Fulfilment</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="7" className="p-8 text-center text-stone-400">Loading...</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan="7" className="p-8 text-center text-stone-400">No orders found.</td></tr>
            ) : orders.map(o => (
              <tr
                key={o.id}
                onClick={() => {
                  fetch(`${API}/orders/${o.id}`).then(r => r.json()).then(setSelected)
                }}
                className="border-b border-stone-100 hover:bg-stone-50 cursor-pointer"
              >
                <td className="p-3 text-stone-600">#{o.id}</td>
                <td className="p-3 text-stone-700">{o.customer}</td>
                <td className="p-3 text-stone-600">
                  {o.items.map((item, i) => (
                    <span key={i}>{item.quantity}x {item.variant}{i < o.items.length - 1 ? ', ' : ''}</span>
                  ))}
                </td>
                <td className="p-3 text-stone-700">RM{o.total_amount.toFixed(2)}</td>
                <td className="p-3"><span className={`badge ${statusBadge(o.status)}`}>{o.status.replace(/_/g, ' ')}</span></td>
                <td className="p-3"><span className={`badge ${statusBadge(o.payment_status)}`}>{o.payment_status.replace(/_/g, ' ')}</span></td>
                <td className="p-3"><span className={`badge ${statusBadge(o.fulfilment_status)}`}>{o.fulfilment_status.replace(/_/g, ' ')}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Order #{selected.id}</h2>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs text-stone-400">Customer</p>
                <p className="text-sm font-medium text-stone-700">{selected.customer}</p>
              </div>
              <div>
                <p className="text-xs text-stone-400">Total Amount</p>
                <p className="text-sm font-medium text-stone-700">RM{selected.total_amount.toFixed(2)}</p>
              </div>
            </div>

            <h3 className="text-sm font-semibold text-stone-700 mb-2">Items</h3>
            <div className="bg-stone-50 rounded-lg p-3 mb-4">
              {selected.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm py-1">
                  <span className="text-stone-600">{item.quantity}x {item.variant}</span>
                  <span className="text-stone-600">RM{(item.unit_price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>

            <h3 className="text-sm font-semibold text-stone-700 mb-2">Messages</h3>
            <div className="bg-stone-50 rounded-lg p-3 mb-4 space-y-2 max-h-40 overflow-y-auto">
              {selected.messages.length === 0 ? (
                <p className="text-sm text-stone-400">No messages.</p>
              ) : selected.messages.map(m => (
                <div key={m.id} className="text-sm">
                  <span className={`badge ${m.sender_type === 'customer' ? 'badge-amber' : m.sender_type === 'ai' ? 'badge-blue' : 'badge-grey'}`}>
                    {m.sender_type}
                  </span>
                  <span className="text-stone-600 ml-2">{m.content}</span>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <p className="text-xs text-stone-400">Order Status</p>
                <span className={`badge ${statusBadge(selected.status)}`}>{selected.status}</span>
              </div>
              <div>
                <p className="text-xs text-stone-400">Payment Status</p>
                <span className={`badge ${statusBadge(selected.payment_status)}`}>{selected.payment_status}</span>
              </div>
              <div>
                <p className="text-xs text-stone-400">Fulfilment</p>
                <span className={`badge ${statusBadge(selected.fulfilment_status)}`}>{selected.fulfilment_status}</span>
              </div>
            </div>

            <button onClick={() => setSelected(null)} className="btn btn-secondary mt-4">Close</button>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { orderAPI, customerAPI, productAPI } from '../services/api'
import { Plus, Filter, ChevronDown } from 'lucide-react'

const statusColors: Record<string, string> = {
  pending: 'badge-pending', confirmed: 'badge-confirmed', paid: 'badge-paid',
  packed: 'badge-packed', dispatched: 'badge-dispatched', delivered: 'badge-delivered',
  cancelled: 'badge-cancelled', exception: 'badge-exception',
}

export default function Orders() {
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders', statusFilter],
    queryFn: () => orderAPI.list(statusFilter).then(r => r.data),
  })

  const { data: customers } = useQuery({ queryKey: ['customers'], queryFn: () => customerAPI.list().then(r => r.data) })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => productAPI.list().then(r => r.data) })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => orderAPI.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
  })

  const [createForm, setCreateForm] = useState({
    customer_id: 0,
    product_id: 0,
    quantity: 1,
    shipping_charged: '0',
  })

  const handleCreate = async () => {
    const product = products?.find(p => p.id === createForm.product_id)
    if (!product || !createForm.customer_id) return
    await orderAPI.create({
      customer_id: createForm.customer_id,
      order_items: [{ product_id: createForm.product_id, quantity: Number(createForm.quantity) }],
      shipping_charged: createForm.shipping_charged,
    })
    setShowCreate(false)
    qc.invalidateQueries({ queryKey: ['orders'] })
    setCreateForm({ customer_id: 0, product_id: 0, quantity: 1, shipping_charged: '0' })
  }

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await updateMutation.mutateAsync({ id, data: { status: newStatus } })
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update order status')
    }
  }

  if (isLoading) return <Loading />

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
          <Plus className="w-4 h-4" /> New Order
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
          <h3 className="font-semibold text-gray-900">Create New Order</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <select value={createForm.customer_id} onChange={e => setCreateForm({ ...createForm, customer_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
              <option value={0}>Select customer...</option>
              {customers?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select value={createForm.product_id} onChange={e => setCreateForm({ ...createForm, product_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
              <option value={0}>Select product...</option>
              {products?.map(p => <option key={p.id} value={p.id}>{p.name} (RM {p.selling_price})</option>)}
            </select>
            <input type="number" min={1} value={createForm.quantity} onChange={e => setCreateForm({ ...createForm, quantity: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" placeholder="Qty" />
            <input type="text" value={createForm.shipping_charged} onChange={e => setCreateForm({ ...createForm, shipping_charged: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" placeholder="Shipping RM" />
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm font-medium">Create Order</button>
        </div>
      )}

      {/* Status filters */}
      <div className="flex flex-wrap gap-2">
        <FilterChip label="All" active={!statusFilter} onClick={() => setStatusFilter('')} />
        {['pending', 'confirmed', 'paid', 'packed', 'dispatched', 'delivered', 'cancelled', 'exception'].map(s => (
          <FilterChip key={s} label={s} active={statusFilter === s} onClick={() => setStatusFilter(s)} />
        ))}
      </div>

      {/* Orders table */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Order #</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Customer</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Total</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Balance</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Dispatch</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orders?.map((o: any) => {
                const customer = customers?.find(c => c.id === o.customer_id)
                return (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{o.order_number}</td>
                    <td className="px-4 py-3 text-gray-600">{customer?.name || `Customer #${o.customer_id}`}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[o.status]}`}>{o.status}</span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">RM {o.total}</td>
                    <td className="px-4 py-3 text-right text-gray-600">RM {o.balance_due}</td>
                    <td className="px-4 py-3 text-gray-600">{o.promised_dispatch_date || '-'}</td>
                    <td className="px-4 py-3">
                      <select
                        value={o.status}
                        onChange={e => handleStatusChange(o.id, e.target.value)}
                        className="text-xs border border-gray-300 rounded px-2 py-1"
                        disabled={o.status === 'delivered'}
                      >
                        {['pending', 'confirmed', 'paid', 'packed', 'dispatched', 'delivered', 'cancelled'].map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {orders?.length === 0 && <p className="text-center py-8 text-gray-400">No orders found</p>}
      </div>
    </div>
  )
}

function FilterChip({ label, active, onClick }: any) {
  return (
    <button onClick={onClick} className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${active ? 'bg-primary-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:border-primary-300'}`}>
      {label}
    </button>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

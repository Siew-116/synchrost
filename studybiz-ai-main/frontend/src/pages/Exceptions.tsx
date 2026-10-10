import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { exceptionAPI, orderAPI } from '../services/api'
import { AlertTriangle, Plus, CheckCircle, XCircle } from 'lucide-react'

const typeLabels: Record<string, string> = {
  supplier_delay: 'Supplier Delay',
  customer_cancellation: 'Customer Cancellation',
  missing_item: 'Missing Item',
  defective_item: 'Defective Item',
  shipping_blackout: 'Shipping Blackout',
  payment_dispute: 'Payment Dispute',
  other: 'Other',
}

export default function Exceptions() {
  const [statusFilter, setStatusFilter] = useState('open')
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()

  const { data: exceptions, isLoading } = useQuery({
    queryKey: ['exceptions', statusFilter],
    queryFn: () => exceptionAPI.list(statusFilter).then(r => r.data),
  })
  const { data: orders } = useQuery({ queryKey: ['orders'], queryFn: () => orderAPI.list().then(r => r.data) })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => exceptionAPI.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exceptions'] }),
  })

  const [createForm, setCreateForm] = useState({
    exception_type: 'supplier_delay',
    title: '',
    description: '',
    order_id: 0,
  })

  const handleCreate = async () => {
    await exceptionAPI.create({
      ...createForm,
      order_id: createForm.order_id || null,
    })
    setShowCreate(false)
    setCreateForm({ exception_type: 'supplier_delay', title: '', description: '', order_id: 0 })
    qc.invalidateQueries({ queryKey: ['exceptions'] })
  }

  const handleResolve = async (id: number, status: string) => {
    await updateMutation.mutateAsync({ id, data: { status } })
  }

  if (isLoading) return <Loading />

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Exceptions</h1>
          <p className="text-gray-500 text-sm">Track and resolve operational disruptions</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
          <Plus className="w-4 h-4" /> New Exception
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
          <h3 className="font-semibold text-gray-900">Create Exception</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <select value={createForm.exception_type} onChange={e => setCreateForm({ ...createForm, exception_type: e.target.value })} className="px-3 py-2 border rounded-lg text-sm">
              {Object.entries(typeLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <input type="text" placeholder="Title..." value={createForm.title} onChange={e => setCreateForm({ ...createForm, title: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
          </div>
          <textarea placeholder="Description..." value={createForm.description} onChange={e => setCreateForm({ ...createForm, description: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" rows={3} />
          <select value={createForm.order_id} onChange={e => setCreateForm({ ...createForm, order_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
            <option value={0}>No linked order</option>
            {orders?.map((o: any) => <option key={o.id} value={o.id}>{o.order_number}</option>)}
          </select>
          <button onClick={handleCreate} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm font-medium">Create</button>
        </div>
      )}

      <div className="flex gap-2">
        {['open', 'resolved', 'closed', ''].map(s => (
          <button key={s || 'all'} onClick={() => setStatusFilter(s)} className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${statusFilter === s ? 'bg-primary-600 text-white' : 'bg-white border border-gray-200 text-gray-600'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {exceptions?.map((e: any) => (
          <div key={e.id} className={`bg-white rounded-xl border p-4 ${e.status === 'open' ? 'border-danger-200' : 'border-gray-100'}`}>
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${e.status === 'open' ? 'bg-danger-50 text-danger-600' : 'bg-gray-50 text-gray-400'}`}>
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{e.title}</p>
                  <p className="text-xs text-gray-500">{typeLabels[e.exception_type] || e.exception_type} - {e.status}</p>
                  {e.description && <p className="text-sm text-gray-600 mt-1">{e.description}</p>}
                  {e.order_id && <p className="text-xs text-primary-600 mt-1">Linked: Order #{e.order_id}</p>}
                </div>
              </div>
              {e.status === 'open' && (
                <div className="flex gap-2">
                  <button onClick={() => handleResolve(e.id, 'resolved')} className="flex items-center gap-1 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-xs font-medium hover:bg-green-100">
                    <CheckCircle className="w-3 h-3" /> Resolve
                  </button>
                  <button onClick={() => handleResolve(e.id, 'closed')} className="flex items-center gap-1 px-3 py-1.5 bg-gray-50 text-gray-600 rounded-lg text-xs font-medium hover:bg-gray-100">
                    <XCircle className="w-3 h-3" /> Close
                  </button>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-2">Created: {e.created_at?.slice(0, 19).replace('T', ' ')}</p>
          </div>
        ))}
        {exceptions?.length === 0 && <p className="text-center py-8 text-gray-400">No exceptions found</p>}
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

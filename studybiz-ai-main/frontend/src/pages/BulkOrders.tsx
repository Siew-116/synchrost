import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bulkOrderAPI, customerAPI, productAPI } from '../services/api'
import { Plus, Group, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'

export default function BulkOrders() {
  const [showCreate, setShowCreate] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const qc = useQueryClient()

  const { data: bulkOrders, isLoading } = useQuery({
    queryKey: ['bulk-orders'],
    queryFn: () => bulkOrderAPI.list().then(r => r.data),
  })
  const { data: customers } = useQuery({ queryKey: ['customers'], queryFn: () => customerAPI.list().then(r => r.data) })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => productAPI.list().then(r => r.data) })

  const { data: allocations } = useQuery({
    queryKey: ['bulk-order-allocations', expandedId],
    queryFn: () => bulkOrderAPI.allocations(expandedId!).then(r => r.data),
    enabled: !!expandedId,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => bulkOrderAPI.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['bulk-orders'] }); setShowCreate(false) },
  })

  const [createForm, setCreateForm] = useState({
    title: '',
    participants: [{ customer_id: 0, product_id: 0, quantity: 1 }],
    shared_shipping_cost: '0',
    shared_discount: '0',
    allocation_method: 'equal',
  })

  const addParticipant = () => {
    setCreateForm({
      ...createForm,
      participants: [...createForm.participants, { customer_id: 0, product_id: 0, quantity: 1 }],
    })
  }

  const updateParticipant = (idx: number, field: string, value: any) => {
    const updated = [...createForm.participants]
    updated[idx] = { ...updated[idx], [field]: value }
    setCreateForm({ ...createForm, participants: updated })
  }

  const removeParticipant = (idx: number) => {
    setCreateForm({ ...createForm, participants: createForm.participants.filter((_, i) => i !== idx) })
  }

  const handleCreate = async () => {
    await createMutation.mutateAsync({
      title: createForm.title,
      participants: createForm.participants.filter(p => p.customer_id && p.product_id),
      shared_shipping_cost: createForm.shared_shipping_cost,
      shared_discount: createForm.shared_discount,
      allocation_method: createForm.allocation_method,
    })
    setCreateForm({ title: '', participants: [{ customer_id: 0, product_id: 0, quantity: 1 }], shared_shipping_cost: '0', shared_discount: '0', allocation_method: 'equal' })
  }

  if (isLoading) return <Loading />

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bulk Orders</h1>
          <p className="text-gray-500 text-sm">Group orders with two-phase cost allocation</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
          <Plus className="w-4 h-4" /> New Bulk Order
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-4">
          <h3 className="font-semibold text-gray-900">Create Bulk Order</h3>
          <input type="text" placeholder="Bulk order title..." value={createForm.title} onChange={e => setCreateForm({ ...createForm, title: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" />

          {createForm.participants.map((p, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <select value={p.customer_id} onChange={e => updateParticipant(idx, 'customer_id', Number(e.target.value))} className="flex-1 px-3 py-2 border rounded-lg text-sm">
                <option value={0}>Customer...</option>
                {customers?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <select value={p.product_id} onChange={e => updateParticipant(idx, 'product_id', Number(e.target.value))} className="flex-1 px-3 py-2 border rounded-lg text-sm">
                <option value={0}>Product...</option>
                {products?.map(pr => <option key={pr.id} value={pr.id}>{pr.name} (RM {pr.selling_price})</option>)}
              </select>
              <input type="number" min={1} value={p.quantity} onChange={e => updateParticipant(idx, 'quantity', e.target.value)} className="w-20 px-3 py-2 border rounded-lg text-sm" />
              <button onClick={() => removeParticipant(idx)} className="px-2 py-2 text-danger-600 hover:bg-danger-50 rounded-lg text-sm">Remove</button>
            </div>
          ))}
          <button onClick={addParticipant} className="text-sm text-primary-600 hover:text-primary-700">+ Add participant</button>

          <div className="grid grid-cols-3 gap-3">
            <input type="text" placeholder="Shared shipping RM" value={createForm.shared_shipping_cost} onChange={e => setCreateForm({ ...createForm, shared_shipping_cost: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="text" placeholder="Shared discount RM" value={createForm.shared_discount} onChange={e => setCreateForm({ ...createForm, shared_discount: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <select value={createForm.allocation_method} onChange={e => setCreateForm({ ...createForm, allocation_method: e.target.value })} className="px-3 py-2 border rounded-lg text-sm">
              <option value="equal">A: Equal split</option>
              <option value="by_value">B: By value</option>
              <option value="manual">D: Manual</option>
            </select>
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm font-medium">Create Bulk Order</button>
        </div>
      )}

      {/* Bulk order cards */}
      <div className="space-y-3">
        {bulkOrders?.map((bo: any) => (
          <div key={bo.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedId(expandedId === bo.id ? null : bo.id)}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Group className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{bo.title}</p>
                  <p className="text-xs text-gray-500">{bo.participant_count} participants - Method {bo.allocation_method?.toUpperCase()}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">RM {bo.total_cost}</p>
                  <p className="text-xs text-gray-400">Total cost</p>
                </div>
                {expandedId === bo.id ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
              </div>
            </div>

            {expandedId === bo.id && allocations && (
              <div className="border-t border-gray-100 p-4 space-y-3">
                <h4 className="text-sm font-semibold text-gray-700">Cost Allocation (Two-Phase)</h4>
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Customer</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Product</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Qty</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Item Subtotal</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Shared Cost</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-600">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {allocations.map((a: any) => (
                      <tr key={a.id || a.customer_id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-900">{customers?.find(c => c.id === a.customer_id)?.name || `#${a.customer_id}`}</td>
                        <td className="px-3 py-2 text-gray-600">{products?.find(p => p.id === a.product_id)?.name || '-'}</td>
                        <td className="px-3 py-2 text-right text-gray-600">{a.quantity}</td>
                        <td className="px-3 py-2 text-right text-gray-600">RM {a.item_subtotal}</td>
                        <td className="px-3 py-2 text-right text-gray-600">RM {a.shared_cost}</td>
                        <td className="px-3 py-2 text-right font-semibold text-gray-900">RM {a.allocated_total}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-50 font-semibold">
                      <td colSpan={3} className="px-3 py-2 text-right text-gray-700">Totals</td>
                      <td className="px-3 py-2 text-right text-gray-700">RM {allocations.reduce((s: number, a: any) => s + Number(a.item_subtotal || 0), 0).toFixed(2)}</td>
                      <td className="px-3 py-2 text-right text-gray-700">RM {allocations.reduce((s: number, a: any) => s + Number(a.shared_cost || 0), 0).toFixed(2)}</td>
                      <td className="px-3 py-2 text-right text-gray-900">RM {allocations.reduce((s: number, a: any) => s + Number(a.allocated_total || 0), 0).toFixed(2)}</td>
                    </tr>
                  </tfoot>
                </table>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <AlertCircle className="w-3 h-3" />
                  Phase 1: item subtotals - Phase 2: shared cost via method {bo.allocation_method?.toUpperCase()} - Last participant absorbs rounding residual
                </div>
              </div>
            )}
          </div>
        ))}
        {bulkOrders?.length === 0 && <p className="text-center py-8 text-gray-400">No bulk orders yet</p>}
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

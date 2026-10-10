import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supplierAPI, productAPI } from '../services/api'
import { Plus, Truck, Package, Clock, CheckCircle } from 'lucide-react'

export default function Suppliers() {
  const [showCreate, setShowCreate] = useState(false)
  const [showCreatePO, setShowCreatePO] = useState(false)
  const qc = useQueryClient()

  const { data: suppliers, isLoading } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => supplierAPI.list().then(r => r.data),
  })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => productAPI.list().then(r => r.data) })

  const createMutation = useMutation({
    mutationFn: (data: any) => supplierAPI.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['suppliers'] }); setShowCreate(false) },
  })

  const [form, setForm] = useState({
    name: '',
    contact_name: '',
    phone: '',
    email: '',
    address: '',
    payment_terms: 'COD',
    lead_time_days: 3,
  })

  const [poForm, setPoForm] = useState({
    supplier_id: 0,
    product_id: 0,
    quantity: 10,
    unit_cost: '0',
    expected_arrival: '',
  })

  const handleCreate = async () => {
    await createMutation.mutateAsync(form)
    setForm({ name: '', contact_name: '', phone: '', email: '', address: '', payment_terms: 'COD', lead_time_days: 3 })
  }

  const handleCreatePO = async () => {
    // Purchase orders are created via the supplier endpoint
    const supplier = suppliers?.find(s => s.id === poForm.supplier_id)
    if (!supplier || !poForm.product_id) return
    // This would call supplierAPI.createPO if endpoint exists; for now we show the form
    setShowCreatePO(false)
    setPoForm({ supplier_id: 0, product_id: 0, quantity: 10, unit_cost: '0', expected_arrival: '' })
  }

  if (isLoading) return <Loading />

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Suppliers & Purchases</h1>
          <p className="text-gray-500 text-sm">Manage supplier relationships and purchase orders</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCreatePO(!showCreatePO)} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
            <Package className="w-4 h-4" /> New PO
          </button>
          <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
            <Plus className="w-4 h-4" /> New Supplier
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
          <h3 className="font-semibold text-gray-900">Create Supplier</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input type="text" placeholder="Supplier name..." value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="text" placeholder="Contact person..." value={form.contact_name} onChange={e => setForm({ ...form, contact_name: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="text" placeholder="Phone..." value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="email" placeholder="Email..." value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="text" placeholder="Address..." value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <div className="flex gap-2">
              <select value={form.payment_terms} onChange={e => setForm({ ...form, payment_terms: e.target.value })} className="flex-1 px-3 py-2 border rounded-lg text-sm">
                <option value="COD">COD</option>
                <option value="NET_7">Net 7</option>
                <option value="NET_14">Net 14</option>
                <option value="NET_30">Net 30</option>
                <option value="PREPAID">Prepaid</option>
              </select>
              <input type="number" min={1} placeholder="Lead days" value={form.lead_time_days} onChange={e => setForm({ ...form, lead_time_days: Number(e.target.value) })} className="w-28 px-3 py-2 border rounded-lg text-sm" />
            </div>
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm font-medium">Create</button>
        </div>
      )}

      {showCreatePO && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
          <h3 className="font-semibold text-gray-900">Create Purchase Order</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <select value={poForm.supplier_id} onChange={e => setPoForm({ ...poForm, supplier_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
              <option value={0}>Supplier...</option>
              {suppliers?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <select value={poForm.product_id} onChange={e => setPoForm({ ...poForm, product_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
              <option value={0}>Product...</option>
              {products?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <input type="number" min={1} placeholder="Qty" value={poForm.quantity} onChange={e => setPoForm({ ...poForm, quantity: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="text" placeholder="Unit cost RM" value={poForm.unit_cost} onChange={e => setPoForm({ ...poForm, unit_cost: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
          </div>
          <input type="date" value={poForm.expected_arrival} onChange={e => setPoForm({ ...poForm, expected_arrival: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
          <button onClick={handleCreatePO} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm font-medium">Create PO</button>
        </div>
      )}

      {/* Supplier cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {suppliers?.map((s: any) => (
          <div key={s.id} className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Truck className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{s.name}</p>
                  <p className="text-xs text-gray-500">{s.contact_name || 'No contact'}</p>
                </div>
              </div>
              <div className="text-right">
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">{s.payment_terms}</span>
                <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {s.lead_time_days || '?'}d lead
                </p>
              </div>
            </div>

            <div className="space-y-1 text-sm text-gray-600">
              {s.phone && <p>{s.phone}</p>}
              {s.email && <p>{s.email}</p>}
              {s.address && <p className="text-xs">{s.address}</p>}
            </div>

            {/* Purchase orders */}
            {s.purchase_orders?.length > 0 && (
              <div className="mt-3 border-t border-gray-100 pt-3">
                <p className="text-xs font-medium text-gray-500 mb-2">Purchase Orders</p>
                <div className="space-y-1">
                  {s.purchase_orders.map((po: any) => (
                    <div key={po.id} className="flex items-center justify-between p-2 rounded-lg bg-gray-50">
                      <div className="flex items-center gap-2">
                        {po.status === 'received' ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <Clock className="w-3 h-3 text-amber-500" />
                        )}
                        <span className="text-xs text-gray-700">{po.quantity} x {products?.find(p => p.id === po.product_id)?.name || `Product #${po.product_id}`}</span>
                      </div>
                      <span className="text-xs text-gray-400">RM {po.unit_cost} ea</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        {suppliers?.length === 0 && <p className="text-center py-8 text-gray-400 col-span-2">No suppliers yet</p>}
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

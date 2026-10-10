import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messageAPI, customerAPI, orderAPI } from '../services/api'
import { Plus, MessageSquare, Check, Send, Trash2, AlertCircle } from 'lucide-react'

const templateTypes: Record<string, { label: string; lang: string }> = {
  order_confirmation: { label: 'Order Confirmation', lang: 'en' },
  payment_reminder: { label: 'Payment Reminder', lang: 'en' },
  purchase_proof: { label: 'Purchase Proof', lang: 'en' },
  ems_sharing: { label: 'EMS Sharing', lang: 'en' },
  group_order_progress: { label: 'Group Order Progress', lang: 'en' },
  parcel_arrival: { label: 'Parcel Arrival', lang: 'en' },
  packaging_notice: { label: 'Packaging Notice', lang: 'en' },
  postage_scheduling: { label: 'Postage Scheduling', lang: 'en' },
  tracking_update: { label: 'Tracking Update', lang: 'en' },
  blackout_announcement: { label: 'Blackout Announcement', lang: 'en' },
  shipping_delay: { label: 'Shipping Delay', lang: 'en' },
  cancellation: { label: 'Cancellation', lang: 'en' },
  missing_item: { label: 'Missing Item', lang: 'en' },
  defective_item: { label: 'Defective Item', lang: 'en' },
  refund: { label: 'Refund', lang: 'en' },
  replacement: { label: 'Replacement', lang: 'en' },
}

const statusColors: Record<string, string> = {
  draft: 'badge-pending',
  awaiting_approval: 'badge-confirmed',
  approved: 'badge-paid',
  sent: 'badge-delivered',
  rejected: 'badge-cancelled',
}

export default function Messages() {
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages'],
    queryFn: () => messageAPI.list().then(r => r.data),
  })
  const { data: customers } = useQuery({ queryKey: ['customers'], queryFn: () => customerAPI.list().then(r => r.data) })
  const { data: orders } = useQuery({ queryKey: ['orders'], queryFn: () => orderAPI.list().then(r => r.data) })

  const approveMutation = useMutation({
    mutationFn: (id: number) => messageAPI.approve(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['messages'] }),
  })
  const sendMutation = useMutation({
    mutationFn: (id: number) => messageAPI.markSent(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['messages'] }),
  })
  const deleteMutation = useMutation({
    mutationFn: (id: number) => messageAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['messages'] }),
  })

  const [createForm, setCreateForm] = useState({
    template_type: 'order_confirmation',
    customer_id: 0,
    order_id: 0,
    context_vars: '',
  })

  const handleCreate = async () => {
    const contextVars: Record<string, string> = {}
    if (createForm.context_vars) {
      createForm.context_vars.split(',').forEach(pair => {
        const [k, v] = pair.split('=')
        if (k && v) contextVars[k.trim()] = v.trim()
      })
    }
    await messageAPI.create({
      template_type: createForm.template_type,
      customer_id: createForm.customer_id || null,
      order_id: createForm.order_id || null,
      context_vars: contextVars,
    })
    setShowCreate(false)
    setCreateForm({ template_type: 'order_confirmation', customer_id: 0, order_id: 0, context_vars: '' })
    qc.invalidateQueries({ queryKey: ['messages'] })
  }

  if (isLoading) return <Loading />

  return (
    <div className="space-y-4 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customer Messages</h1>
          <p className="text-gray-500 text-sm">16 bilingual (EN/MS) templates - DRAFT to AWAITING_APPROVAL to SENT flow</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
          <Plus className="w-4 h-4" /> New Message
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
          <h3 className="font-semibold text-gray-900">Create Message from Template</h3>
          <select value={createForm.template_type} onChange={e => setCreateForm({ ...createForm, template_type: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm">
            {Object.entries(templateTypes).map(([k, v]) => <option key={k} value={k}>{v.label} ({v.lang})</option>)}
          </select>
          <div className="grid grid-cols-2 gap-3">
            <select value={createForm.customer_id} onChange={e => setCreateForm({ ...createForm, customer_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
              <option value={0}>Select customer...</option>
              {customers?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select value={createForm.order_id} onChange={e => setCreateForm({ ...createForm, order_id: Number(e.target.value) })} className="px-3 py-2 border rounded-lg text-sm">
              <option value={0}>Select order (optional)...</option>
              {orders?.map(o => <option key={o.id} value={o.id}>{o.order_number}</option>)}
            </select>
          </div>
          <input type="text" placeholder="context vars: customer_name=Aisyah, order_no=SBZ-001" value={createForm.context_vars} onChange={e => setCreateForm({ ...createForm, context_vars: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" />
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <AlertCircle className="w-3 h-3" />
            Variables are auto-extracted from customer/order if not provided. Missing variables will block approval.
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm font-medium">Create Draft</button>
        </div>
      )}

      {/* Message list */}
      <div className="space-y-3">
        {messages?.map((m: any) => (
          <div key={m.id} className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{templateTypes[m.template_type]?.label || m.template_type}</p>
                  <p className="text-xs text-gray-500">
                    {m.customer_id && `Customer #${m.customer_id}`}
                    {m.order_id && ` - Order #${m.order_id}`}
                  </p>
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[m.status] || 'bg-gray-100 text-gray-600'}`}>
                {m.status}
              </span>
            </div>

            {m.rendered_content && (
              <div className="bg-gray-50 rounded-lg p-3 mb-3">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{m.rendered_content}</p>
              </div>
            )}

            {m.missing_variables?.length > 0 && (
              <div className="flex items-center gap-2 text-xs text-danger-600 mb-2">
                <AlertCircle className="w-3 h-3" />
                Missing variables: {m.missing_variables.join(', ')}
              </div>
            )}

            <div className="flex items-center gap-2">
              {m.status === 'draft' && !m.missing_variables?.length && (
                <button onClick={() => approveMutation.mutate(m.id)} className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium hover:bg-blue-100">
                  <Check className="w-3 h-3" /> Approve
                </button>
              )}
              {m.status === 'approved' && (
                <button onClick={() => sendMutation.mutate(m.id)} className="flex items-center gap-1 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-xs font-medium hover:bg-green-100">
                  <Send className="w-3 h-3" /> Mark Sent
                </button>
              )}
              <button onClick={() => deleteMutation.mutate(m.id)} className="flex items-center gap-1 px-3 py-1.5 bg-gray-50 text-gray-500 rounded-lg text-xs font-medium hover:bg-gray-100">
                <Trash2 className="w-3 h-3" /> Delete
              </button>
              <span className="text-xs text-gray-400 ml-auto">{m.created_at?.slice(0, 19).replace('T', ' ')}</span>
            </div>
          </div>
        ))}
        {messages?.length === 0 && <p className="text-center py-8 text-gray-400">No messages yet</p>}
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

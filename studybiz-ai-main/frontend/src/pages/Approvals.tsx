import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { approvalAPI } from '../services/api'
import { CheckSquare, Check, X, Clock } from 'lucide-react'

export default function Approvals() {
  const [statusFilter, setStatusFilter] = useState('pending')
  const qc = useQueryClient()

  const { data: approvals, isLoading } = useQuery({
    queryKey: ['approvals', statusFilter],
    queryFn: () => approvalAPI.list(statusFilter).then(r => r.data),
  })

  const decideMutation = useMutation({
    mutationFn: ({ id, approved, note }: { id: number; approved: boolean; note?: string }) =>
      approvalAPI.decide(id, approved, note),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approvals'] }),
  })

  const [notes, setNotes] = useState<Record<number, string>>({})

  const handleDecide = async (id: number, approved: boolean) => {
    await decideMutation.mutateAsync({ id, approved, note: notes[id] })
    setNotes({ ...notes, [id]: '' })
  }

  if (isLoading) return <Loading />

  return (
    <div className="space-y-4 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Approval Queue</h1>
        <p className="text-gray-500 text-sm">Agent-proposed consequential actions requiring human approval</p>
      </div>

      <div className="flex gap-2">
        {['pending', 'approved', 'rejected', ''].map(s => (
          <button
            key={s || 'all'}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${statusFilter === s ? 'bg-primary-600 text-white' : 'bg-white border border-gray-200 text-gray-600'}`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {approvals?.map((a: any) => (
          <div key={a.id} className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  a.status === 'pending' ? 'bg-amber-50 text-amber-600' :
                  a.status === 'approved' ? 'bg-green-50 text-green-600' :
                  'bg-red-50 text-red-600'
                }`}>
                  <CheckSquare className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{a.action_type}</p>
                  <p className="text-xs text-gray-500">
                    {a.description || `Action #${a.id}`}
                  </p>
                  {a.proposed_by && (
                    <p className="text-xs text-primary-600 mt-0.5">Proposed by: {a.proposed_by}</p>
                  )}
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                a.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                a.status === 'approved' ? 'bg-green-100 text-green-700' :
                'bg-red-100 text-red-700'
              }`}>
                {a.status}
              </span>
            </div>

            {a.payload && Object.keys(a.payload).length > 0 && (
              <div className="bg-gray-50 rounded-lg p-3 mb-3">
                <pre className="text-xs text-gray-600 overflow-x-auto">
                  {JSON.stringify(a.payload, null, 2)}
                </pre>
              </div>
            )}

            {a.status === 'pending' && (
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Optional note..."
                  value={notes[a.id] || ''}
                  onChange={e => setNotes({ ...notes, [a.id]: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDecide(a.id, true)}
                    className="flex items-center gap-1 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
                  >
                    <Check className="w-4 h-4" /> Approve
                  </button>
                  <button
                    onClick={() => handleDecide(a.id, false)}
                    className="flex items-center gap-1 px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm font-medium hover:bg-red-100"
                  >
                    <X className="w-4 h-4" /> Reject
                  </button>
                </div>
              </div>
            )}

            {a.decided_at && (
              <p className="text-xs text-gray-400 mt-2 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Decided: {a.decided_at?.slice(0, 19).replace('T', ' ')}
                {a.decision_note && ` - "${a.decision_note}"`}
              </p>
            )}
          </div>
        ))}
        {approvals?.length === 0 && <p className="text-center py-8 text-gray-400">No approval requests</p>}
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

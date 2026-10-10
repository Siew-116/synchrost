import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { automationAPI } from '../services/api'
import { Clock, Play, Pause, CheckCircle, XCircle, Calendar } from 'lucide-react'

export default function Automation() {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const qc = useQueryClient()

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['automation-jobs'],
    queryFn: () => automationAPI.list().then(r => r.data),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => automationAPI.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation-jobs'] }),
  })
  const runNowMutation = useMutation({
    mutationFn: (id: number) => automationAPI.runNow(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automation-jobs'] }),
  })

  const { data: runs } = useQuery({
    queryKey: ['automation-runs', expandedId],
    queryFn: () => automationAPI.runs(expandedId!).then(r => r.data),
    enabled: !!expandedId,
  })

  if (isLoading) return <Loading />

  return (
    <div className="space-y-4 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Automation</h1>
        <p className="text-gray-500 text-sm">Recurring jobs for academic briefings, business alerts, and operational checks</p>
      </div>

      <div className="space-y-3">
        {jobs?.map((job: any) => (
          <div key={job.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${job.is_active ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-400'}`}>
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{job.name}</p>
                  <p className="text-xs text-gray-500">
                    {job.schedule_type} - {job.cron_expression || 'interval-based'}
                    {job.last_run_at && ` - Last: ${job.last_run_at.slice(0, 19).replace('T', ' ')}`}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => runNowMutation.mutate(job.id)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-primary-50 text-primary-700 rounded-lg text-xs font-medium hover:bg-primary-100"
                  disabled={runNowMutation.isPending}
                >
                  <Play className="w-3 h-3" /> Run Now
                </button>
                <button
                  onClick={() => toggleMutation.mutate({ id: job.id, data: { is_active: !job.is_active } })}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium ${job.is_active ? 'bg-amber-50 text-amber-700 hover:bg-amber-100' : 'bg-green-50 text-green-700 hover:bg-green-100'}`}
                >
                  {job.is_active ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                  {job.is_active ? 'Pause' : 'Enable'}
                </button>
                <button
                  onClick={() => setExpandedId(expandedId === job.id ? null : job.id)}
                  className="px-3 py-1.5 text-gray-500 hover:bg-gray-50 rounded-lg text-xs"
                >
                  History
                </button>
              </div>
            </div>

            {expandedId === job.id && runs && (
              <div className="border-t border-gray-100 p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Run History</h4>
                {runs?.length > 0 ? (
                  <div className="space-y-2">
                    {runs.map((run: any) => (
                      <div key={run.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
                        {run.status === 'success' ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-danger-500" />
                        )}
                        <div className="flex-1">
                          <p className="text-sm text-gray-700">{run.result_summary || run.status}</p>
                          <p className="text-xs text-gray-400">{run.started_at?.slice(0, 19).replace('T', ' ')}</p>
                        </div>
                        {run.actions_count > 0 && (
                          <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded">{run.actions_count} actions</span>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 text-center py-4">No runs yet</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary card */}
      <div className="bg-white rounded-xl border border-gray-100 p-4">
        <div className="flex items-center gap-2 mb-2">
          <Calendar className="w-4 h-4 text-primary-600" />
          <h2 className="font-semibold text-gray-900">Default Automation Jobs</h2>
        </div>
        <p className="text-sm text-gray-500">
          10 pre-configured jobs: daily academic briefing, daily business briefing, exam warning (3d/1d),
          assignment deadline warning (2d/1d), pending payment review, orders ready to pack, shipping cutoff check,
          inventory shortage warning, supplier arrival follow-up, weekly sales summary.
        </p>
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

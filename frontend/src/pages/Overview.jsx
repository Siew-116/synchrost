import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, Clock, Bot } from 'lucide-react'

const API = '/api'

export default function Overview() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/dashboard/metrics`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <PageSkeleton />
  if (!data) return <div className="p-8 text-stone-500">Failed to load data.</div>

  const cards = [
    { label: 'Active Group Buys', value: data.active_group_buys, color: 'text-brand-600', icon: 'package' },
    { label: 'Total Orders', value: data.total_orders, color: 'text-blue-600', icon: 'bag' },
    { label: 'Awaiting Payment', value: data.orders_awaiting_payment, color: 'text-amber-600', icon: 'clock' },
    { label: 'Payments to Verify', value: data.payments_awaiting_verification, color: 'text-amber-600', icon: 'clock' },
    { label: 'Admin Attention', value: data.orders_requiring_admin_attention, color: 'text-red-600', icon: 'alert' },
    { label: 'Open Enquiries', value: data.unresolved_customer_enquiries, color: 'text-amber-600', icon: 'alert' },
    { label: 'Open Exceptions', value: data.open_exceptions, color: 'text-red-600', icon: 'alert' },
    { label: 'AI Actions', value: data.automated_actions_completed, color: 'text-brand-600', icon: 'bot' },
  ]

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Overview</h1>
      <p className="text-sm text-stone-500 mb-6">Business operations at a glance</p>

      {/* AI Summary */}
      {data.ai_summary && (
        <div className="card mb-6 border-l-4 border-l-brand-500">
          <div className="flex items-start gap-3">
            <Bot className="text-brand-600 mt-0.5" size={20} />
            <div>
              <h3 className="text-sm font-semibold text-stone-700 mb-1">AI Operations Summary</h3>
              <p className="text-sm text-stone-600">{data.ai_summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {cards.map((c, i) => (
          <div key={i} className="card">
            <p className="text-xs text-stone-500 mb-1">{c.label}</p>
            <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div>
          <h2 className="text-sm font-semibold text-stone-700 mb-3 flex items-center gap-2">
            <Activity size={16} /> Recent Activity
          </h2>
          <div className="card">
            {data.recent_activity && data.recent_activity.length > 0 ? (
              <div className="space-y-3">
                {data.recent_activity.slice(0, 8).map((log, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <span className={`badge ${log.actor === 'ai' ? 'badge-blue' : 'badge-green'}`}>
                      {log.actor}
                    </span>
                    <div className="flex-1">
                      <p className="text-stone-700">{log.input_summary}</p>
                      <p className="text-xs text-stone-400">{log.result}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-400">No recent activity.</p>
            )}
          </div>
        </div>

        {/* Priority Exceptions */}
        <div>
          <h2 className="text-sm font-semibold text-stone-700 mb-3 flex items-center gap-2">
            <AlertTriangle size={16} /> Priority Exceptions
          </h2>
          <div className="card">
            {data.priority_exceptions && data.priority_exceptions.length > 0 ? (
              <div className="space-y-3">
                {data.priority_exceptions.map((e, i) => (
                  <div key={i} className="border-l-4 border-l-red-500 pl-3">
                    <p className="text-xs font-medium text-red-600 uppercase">{e.type.replace(/_/g, ' ')}</p>
                    <p className="text-sm text-stone-600 mt-1">{e.description}</p>
                    {e.recommended_action && (
                      <p className="text-xs text-stone-400 mt-1">Action: {e.recommended_action}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-400">No open exceptions.</p>
            )}
          </div>
        </div>
      </div>

      {/* Active Campaigns */}
      {data.active_campaigns && data.active_campaigns.length > 0 && (
        <div className="mt-6">
          <h2 className="text-sm font-semibold text-stone-700 mb-3 flex items-center gap-2">
            <Clock size={16} /> Upcoming Deadlines
          </h2>
          <div className="card">
            {data.active_campaigns.map((c, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-stone-700">{c.name}</span>
                <span className="text-stone-500">
                  {c.closes_at ? new Date(c.closes_at).toLocaleDateString() : 'No deadline'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function PageSkeleton() {
  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="h-8 bg-stone-200 rounded w-48 animate-pulse mb-6"></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="card h-24 animate-pulse"></div>
        ))}
      </div>
    </div>
  )
}

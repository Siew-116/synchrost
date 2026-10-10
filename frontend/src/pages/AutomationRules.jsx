import { useState, useEffect } from 'react'

const API = '/api'

export default function AutomationRules() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    fetch(`${API}/automation/rules`)
      .then(r => r.json())
      .then(d => { setRules(d); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const toggle = (id, enabled) => {
    fetch(`${API}/automation/rules/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: !enabled }),
    }).then(() => load())
  }

  const ruleDescriptions = {
    business_hours: 'Set the hours during which the business is active. Messages outside these hours are queued.',
    late_order_handling: 'Define what happens when a customer tries to order after the campaign deadline. Default: forward to admin for approval.',
    payment_verification: 'Control whether payment screenshots are required and whether payments can be auto-verified. Default: manual verification required.',
    cancellation_rules: 'Define when customers can cancel orders. Default: cancellations allowed before payment is confirmed.',
    auto_reply_eligible: 'Specify which customer intents can receive automatic AI replies without admin review.',
    exam_mode: 'When enabled, routine operations continue but non-urgent notifications are batched and sensitive decisions are queued. Urgent exceptions still alert the admin.',
    escalation_conditions: 'Define which situations must be escalated to the admin for manual review.',
  }

  if (loading) return <div className="p-8 text-stone-500">Loading...</div>

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Automation Rules</h1>
      <p className="text-sm text-stone-500 mb-6">Configure business policies and automation</p>

      <div className="space-y-4">
        {rules.map(r => (
          <div key={r.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-sm font-semibold text-stone-700">
                    {r.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </h3>
                  <span className={`badge ${r.enabled ? 'badge-green' : 'badge-grey'}`}>
                    {r.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  {r.name === 'exam_mode' && r.enabled && (
                    <span className="badge badge-amber">Active</span>
                  )}
                </div>
                <p className="text-sm text-stone-500 mb-3">
                  {ruleDescriptions[r.name] || 'Custom automation rule.'}
                </p>
                {r.configuration && Object.keys(r.configuration).length > 0 && (
                  <div className="bg-stone-50 rounded-lg p-3 text-xs">
                    <pre className="text-stone-600 whitespace-pre-wrap">
                      {JSON.stringify(r.configuration, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
              <button
                onClick={() => toggle(r.id, r.enabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ml-4 flex-shrink-0 ${
                  r.enabled ? 'bg-brand-600' : 'bg-stone-300'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  r.enabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 card bg-blue-50 border-blue-200">
        <h3 className="text-sm font-semibold text-blue-800 mb-2">Safe Defaults</h3>
        <ul className="text-xs text-blue-700 space-y-1">
          <li>- Payments are never auto-verified. Manual confirmation is always required.</li>
          <li>- Late orders are forwarded to admin for approval, not auto-accepted.</li>
          <li>- Complaints are always escalated to the admin.</li>
          <li>- Exam Mode does not override payment controls or cancellation policies.</li>
          <li>- The AI cannot issue refunds or make financial commitments.</li>
        </ul>
      </div>
    </div>
  )
}

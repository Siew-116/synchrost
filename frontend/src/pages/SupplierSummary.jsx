import { useState, useEffect } from 'react'
import { Download } from 'lucide-react'

const API = '/api'

export default function SupplierSummary() {
  const [campaigns, setCampaigns] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/campaigns`)
      .then(r => r.json())
      .then(setCampaigns)
  }, [])

  const loadSummary = (campaignId) => {
    setLoading(true)
    fetch(`${API}/supplier/summary/${campaignId}`)
      .then(r => r.json())
      .then(d => { setSummary(d); setLoading(false) })
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-stone-900 mb-1">Supplier Summary</h1>
      <p className="text-sm text-stone-500 mb-6">Consolidated order quantities for suppliers</p>

      <div className="mb-4">
        <select
          onChange={e => loadSummary(e.target.value)}
          className="px-3 py-2 rounded-lg border border-stone-200 text-sm"
          defaultValue=""
        >
          <option value="" disabled>Select a campaign</option>
          {campaigns.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {loading && <p className="text-sm text-stone-400">Loading summary...</p>}

      {summary && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-stone-900">{summary.campaign_name}</h2>
              <a
                href={`${API}/supplier/summary/${campaigns.find(c => c.name === summary.campaign_name)?.id || 1}/csv`}
                className="btn btn-secondary text-xs flex items-center gap-1"
              >
                <Download size={14} /> Download CSV
              </a>
            </div>

            {!summary.is_final && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-amber-800">
                  This is NOT a final supplier order. The campaign is still open or has unresolved exceptions.
                  Quantities may change before the final summary.
                </p>
              </div>
            )}

            {summary.is_final && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-green-800">
                  This is a FINAL supplier order. Campaign is closed and all exceptions are resolved.
                </p>
              </div>
            )}

            <table className="w-full text-sm">
              <thead className="bg-stone-50 border-b border-stone-200">
                <tr>
                  <th className="text-left p-3 font-medium text-stone-600">Variant</th>
                  <th className="text-right p-3 font-medium text-stone-600">Quantity</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(summary.variants).map(([variant, qty]) => (
                  <tr key={variant} className="border-b border-stone-100">
                    <td className="p-3 text-stone-700">{variant}</td>
                    <td className="p-3 text-right font-medium text-stone-800">{qty}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-stone-50 font-semibold">
                  <td className="p-3 text-stone-700">Total Units</td>
                  <td className="p-3 text-right text-stone-900">{summary.total_units}</td>
                </tr>
              </tfoot>
            </table>

            <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
              <div className="bg-stone-50 rounded-lg p-3">
                <p className="text-xs text-stone-400">Excluded (Cancelled)</p>
                <p className="font-medium text-stone-700">{summary.excluded_cancelled}</p>
              </div>
              <div className="bg-stone-50 rounded-lg p-3">
                <p className="text-xs text-stone-400">Unresolved Exceptions</p>
                <p className={`font-medium ${summary.unresolved_exceptions > 0 ? 'text-amber-600' : 'text-stone-700'}`}>
                  {summary.unresolved_exceptions}
                </p>
              </div>
            </div>

            <p className="text-xs text-stone-400 mt-4">
              Generated at: {new Date(summary.generated_at).toLocaleString()}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

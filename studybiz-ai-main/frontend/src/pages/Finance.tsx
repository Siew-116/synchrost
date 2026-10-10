import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { financeAPI, exportAPI } from '../services/api'
import { TrendingUp, TrendingDown, DollarSign, Download, ArrowDownRight, ArrowUpRight } from 'lucide-react'

export default function Finance() {
  const [showTransactions, setShowTransactions] = useState(false)

  const { data: summary, isLoading } = useQuery({
    queryKey: ['finance-summary'],
    queryFn: () => financeAPI.summary().then(r => r.data),
  })
  const { data: transactions } = useQuery({
    queryKey: ['finance-transactions'],
    queryFn: () => financeAPI.transactions().then(r => r.data),
    enabled: showTransactions,
  })

  const handleExport = async () => {
    const res = await exportAPI.masterlist()
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `studybiz_masterlist.xlsx`
    a.click()
  }

  if (isLoading) return <Loading />

  const s = summary || {}

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Finance</h1>
          <p className="text-gray-500 text-sm">MYR financial overview - banker's rounding (ROUND_HALF_EVEN)</p>
        </div>
        <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
          <Download className="w-4 h-4" /> Export Masterlist
        </button>
      </div>

      {/* Profit summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ProfitCard
          icon={TrendingUp}
          label="Realised Profit"
          value={s.realized_profit}
          subtitle="DELIVERED orders only"
          color="green"
        />
        <ProfitCard
          icon={TrendingDown}
          label="Estimated Profit"
          value={s.estimated_profit}
          subtitle="PAID + PACKED + DISPATCHED"
          color="amber"
        />
        <ProfitCard
          icon={DollarSign}
          label="Gross Sales"
          value={s.gross_sales}
          subtitle="Realised + Estimated"
          color="blue"
        />
      </div>

      {/* Detail breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <h2 className="font-semibold text-gray-900 mb-3">Revenue & Cost Breakdown</h2>
          <div className="space-y-3">
            <Row label="Gross Sales" value={s.gross_sales} />
            <Row label="Discounts" value={s.discounts} />
            <Row label="Refunds" value={s.refunds} />
            <Row label="Net Sales" value={s.net_sales} bold />
            <div className="border-t border-gray-100 pt-3">
              <Row label="Product Cost" value={s.product_cost} />
              <Row label="Shipping Charged" value={s.shipping_charged} />
              <Row label="Shipping Expenses" value={s.shipping_expenses} />
            </div>
            <div className="border-t border-gray-100 pt-3">
              <Row label="Realised Profit" value={s.realized_profit} bold />
              <Row label="Estimated Profit" value={s.estimated_profit} bold />
            </div>
            <div className="border-t border-gray-100 pt-3">
              <Row label="Outstanding Payments" value={s.outstanding_payments} warn />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <h2 className="font-semibold text-gray-900 mb-3">Profit Boundary</h2>
          <div className="space-y-3">
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-sm font-semibold text-green-700">Realised (DELIVERED only)</p>
              <p className="text-2xl font-bold text-green-600">RM {s.realized_profit || '0.00'}</p>
              <p className="text-xs text-green-600 mt-1">Profit is certain - goods delivered and accepted</p>
            </div>
            <div className="p-3 bg-amber-50 rounded-lg">
              <p className="text-sm font-semibold text-amber-700">Estimated (PAID + PACKED + DISPATCHED)</p>
              <p className="text-2xl font-bold text-amber-600">RM {s.estimated_profit || '0.00'}</p>
              <p className="text-xs text-amber-600 mt-1">Payment received but delivery not yet confirmed</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <p className="text-sm font-semibold text-red-700">Outstanding Payments</p>
              <p className="text-2xl font-bold text-red-600">RM {s.outstanding_payments || '0.00'}</p>
              <p className="text-xs text-red-600 mt-1">Balance due from orders not yet fully paid</p>
            </div>
          </div>
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Finance Transactions</h2>
          <button onClick={() => setShowTransactions(!showTransactions)} className="text-sm text-primary-600 hover:text-primary-700">
            {showTransactions ? 'Hide' : 'Show'} transactions
          </button>
        </div>
        {showTransactions && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Date</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Reference</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Debit</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Credit</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {transactions?.map((t: any) => (
                  <tr key={t.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-600">{t.created_at?.slice(0, 10)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${t.transaction_type === 'payment' ? 'bg-green-100 text-green-700' : t.transaction_type === 'refund' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                        {t.transaction_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{t.reference || '-'}</td>
                    <td className="px-4 py-3 text-right text-danger-600">
                      {t.direction === 'debit' ? `RM ${t.amount}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-right text-success-600">
                      {t.direction === 'credit' ? `RM ${t.amount}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{t.note || '-'}</td>
                  </tr>
                ))}
                {transactions?.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-gray-400">No transactions</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Method note */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <div className="text-blue-600 mt-0.5"><DollarSign className="w-4 h-4" /></div>
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">MYR Financial Precision</p>
            <p>All monetary values use <code className="bg-blue-100 px-1 rounded">Numeric(12,2)</code> with banker's rounding (ROUND_HALF_EVEN). Profit is realised only on DELIVERED orders; PAID/PACKED/DISPATCHED contribute estimated profit.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ProfitCard({ icon: Icon, label, value, subtitle, color }: any) {
  const colorMap: any = {
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    blue: 'bg-blue-50 text-blue-600',
  }
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4">
      <div className={`w-10 h-10 rounded-lg ${colorMap[color]} flex items-center justify-center mb-2`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-gray-900">RM {value || '0.00'}</p>
      <p className="text-sm text-gray-700">{label}</p>
      <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
    </div>
  )
}

function Row({ label, value, bold, warn }: any) {
  return (
    <div className="flex items-center justify-between">
      <span className={`text-sm ${bold ? 'font-semibold text-gray-900' : 'text-gray-600'}`}>{label}</span>
      <span className={`text-sm font-semibold ${warn ? 'text-danger-600' : bold ? 'text-gray-900' : 'text-gray-900'}`}>RM {value || '0.00'}</span>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }

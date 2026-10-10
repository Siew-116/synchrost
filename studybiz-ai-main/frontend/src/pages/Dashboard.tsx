import { useQuery } from '@tanstack/react-query'
import { dashboardAPI, orderAPI, exceptionAPI, exportAPI } from '../services/api'
import { Package, DollarSign, AlertTriangle, GraduationCap, Download, ArrowRight, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardAPI.get().then(r => r.data),
  })
  const { data: exceptions } = useQuery({
    queryKey: ['exceptions', 'open'],
    queryFn: () => exceptionAPI.list('open').then(r => r.data),
  })

  const handleExport = async () => {
    const res = await exportAPI.masterlist()
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `studybiz_masterlist.xlsx`
    a.click()
  }

  if (isLoading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>

  const stats = dashboard?.stats || {}

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user?.full_name?.split(' ')[0]}!</h1>
          <p className="text-gray-500 text-sm">Here's your overview for today</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <Download className="w-4 h-4" />
          Export Masterlist
        </button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Package} label="Total Orders" value={stats.total_orders || 0} color="blue" />
        <StatCard icon={DollarSign} label="Paid Orders" value={stats.paid_orders || 0} color="indigo" />
        <StatCard icon={AlertTriangle} label="Open Exceptions" value={stats.open_exceptions || 0} color="red" />
        <StatCard icon={GraduationCap} label="Upcoming Exams" value={stats.upcoming_exams || 0} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's priorities */}
        <Card title="Today's Priorities">
          {dashboard?.today_priorities?.length ? (
            <div className="space-y-2">
              {dashboard.today_priorities.map((p: any) => (
                <div key={p.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
                  <div className={`w-2 h-2 rounded-full ${p.priority === 'critical' ? 'bg-danger-500' : p.priority === 'high' ? 'bg-warning-500' : 'bg-gray-400'}`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{p.title}</p>
                    <p className="text-xs text-gray-500">{p.event_type} • {p.start_time || 'No time'}</p>
                  </div>
                  {p.is_fixed && <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">Fixed</span>}
                </div>
              ))}
            </div>
          ) : <EmptyState text="No events today" />}
        </Card>

        {/* Packing queue */}
        <Card title="Packing Queue" link="/orders" linkText="View orders">
          {dashboard?.packing_queue?.length ? (
            <div className="space-y-2">
              {dashboard.packing_queue.slice(0, 5).map((o: any) => (
                <div key={o.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{o.order_number}</p>
                    <p className="text-xs text-gray-500">{o.estimated_packing_minutes} min to pack</p>
                  </div>
                  {o.promised_dispatch_date && (
                    <span className="text-xs px-2 py-0.5 bg-warning-100 text-warning-600 rounded">
                      Dispatch: {o.promised_dispatch_date}
                    </span>
                  )}
                </div>
              ))}
              <p className="text-xs text-gray-400 text-center pt-2">{dashboard.packing_queue.length} orders total</p>
            </div>
          ) : <EmptyState text="No orders to pack" />}
        </Card>

        {/* Upcoming exams */}
        <Card title="Upcoming Exams" link="/academic" linkText="View academic">
          {dashboard?.upcoming_exams?.length ? (
            <div className="space-y-2">
              {dashboard.upcoming_exams.map((e: any) => (
                <div key={e.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{e.title}</p>
                    <p className="text-xs text-gray-500">{e.course_code || 'No course'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-danger-600">{e.days_until === 0 ? 'TODAY' : `${e.days_until}d`}</p>
                    <p className="text-xs text-gray-400">{e.date}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyState text="No upcoming exams" />}
        </Card>

        {/* Open exceptions */}
        <Card title="Open Exceptions" link="/exceptions" linkText="View all">
          {exceptions?.length ? (
            <div className="space-y-2">
              {exceptions.slice(0, 5).map((e: any) => (
                <div key={e.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
                  <AlertTriangle className="w-4 h-4 text-danger-500 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{e.title}</p>
                    <p className="text-xs text-gray-500">{e.exception_type}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyState text="No open exceptions" />}
        </Card>
      </div>

      {/* Calendar warnings */}
      {dashboard?.calendar_warnings?.length > 0 && (
        <Card title="Calendar Warnings">
          <div className="space-y-2">
            {dashboard.calendar_warnings.map((w: any, i: number) => (
              <div key={i} className="flex items-center gap-2 p-3 bg-danger-50 rounded-lg">
                <Clock className="w-4 h-4 text-danger-500" />
                <p className="text-sm text-danger-700">
                  {w.type === 'assignment_due' ? `Assignment due: ${w.title}` : `Shipping deadline: ${w.order_number}`}
                  {w.days_until === 0 ? ' TODAY!' : ` in ${w.days_until} day(s)`}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }: any) {
  const colorMap: any = { blue: 'bg-blue-50 text-blue-600', indigo: 'bg-indigo-50 text-indigo-600', red: 'bg-red-50 text-red-600', purple: 'bg-purple-50 text-purple-600' }
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4">
      <div className={`w-10 h-10 rounded-lg ${colorMap[color]} flex items-center justify-center mb-2`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  )
}

function Card({ title, children, link, linkText }: any) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-900">{title}</h2>
        {link && <Link to={link} className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">{linkText} <ArrowRight className="w-3 h-3" /></Link>}
      </div>
      {children}
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return <p className="text-sm text-gray-400 text-center py-4">{text}</p>
}

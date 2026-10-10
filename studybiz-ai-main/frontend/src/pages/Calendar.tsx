import { useQuery } from '@tanstack/react-query'
import { academicAPI } from '../services/api'
import { format } from 'date-fns'

export default function Calendar() {
  const { data: events } = useQuery({
    queryKey: ['academic-events'],
    queryFn: () => academicAPI.list().then(r => r.data),
  })

  const typeColors: Record<string, string> = {
    class: 'bg-blue-50 text-blue-700 border-blue-200',
    exam: 'bg-red-50 text-red-700 border-red-200',
    coursework: 'bg-purple-50 text-purple-700 border-purple-200',
    assignment: 'bg-orange-50 text-orange-700 border-orange-200',
    study_session: 'bg-green-50 text-green-700 border-green-200',
    personal: 'bg-gray-50 text-gray-700 border-gray-200',
  }

  const sorted = events?.filter(e => e.start_datetime).sort((a: any, b: any) =>
    new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime()
  ) || []

  // Group by date
  const groups: Record<string, any[]> = {}
  sorted.forEach((e: any) => {
    const day = format(new Date(e.start_datetime), 'EEEE, dd MMMM yyyy')
    if (!groups[day]) groups[day] = []
    groups[day].push(e)
  })

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Unified Calendar</h1>
      <p className="text-sm text-gray-500">Academic events, packing tasks, and shipping deadlines in one view</p>

      <div className="space-y-6">
        {Object.entries(groups).map(([day, dayEvents]) => (
          <div key={day}>
            <h2 className="text-sm font-semibold text-gray-500 mb-2">{day}</h2>
            <div className="space-y-2">
              {dayEvents.map((e: any) => (
                <div key={e.id} className={`flex items-center gap-3 p-3 rounded-lg border ${typeColors[e.event_type] || 'bg-gray-50'}`}>
                  <div className="text-sm font-bold w-16">
                    {format(new Date(e.start_datetime), 'HH:mm')}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{e.title}</p>
                    <p className="text-xs opacity-75">
                      {e.event_type.replace('_', ' ')}
                      {e.location ? ` • ${e.location}` : ''}
                      {e.course_code ? ` • ${e.course_code}` : ''}
                    </p>
                  </div>
                  {e.is_fixed && <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">Fixed</span>}
                  {e.is_completed && <span className="text-xs px-2 py-0.5 bg-green-200 rounded">Done</span>}
                </div>
              ))}
            </div>
          </div>
        ))}
        {sorted.length === 0 && <p className="text-center text-gray-400 py-8">No upcoming events</p>}
      </div>
    </div>
  )
}

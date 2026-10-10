import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { academicAPI } from '../services/api'
import { Plus, Trash2, Check } from 'lucide-react'

export default function Academic() {
  const [showForm, setShowForm] = useState(false)
  const qc = useQueryClient()
  const { data: events } = useQuery({ queryKey: ['academic'], queryFn: () => academicAPI.list().then(r => r.data) })

  const createMutation = useMutation({
    mutationFn: (data: any) => academicAPI.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['academic'] }); setShowForm(false) },
  })

  const toggleComplete = useMutation({
    mutationFn: ({ id, completed }: { id: number; completed: boolean }) => academicAPI.update(id, { is_completed: completed }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['academic'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => academicAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['academic'] }),
  })

  const [form, setForm] = useState({ title: '', event_type: 'class', priority: 'medium', start_datetime: '', is_fixed: false, notes: '', course_code: '' })

  const handleSubmit = () => {
    const data: any = { ...form, is_fixed: form.is_fixed }
    if (form.start_datetime) data.start_datetime = new Date(form.start_datetime).toISOString()
    createMutation.mutate(data)
  }

  const typeIcons: Record<string, string> = { class: '📚', exam: '📝', coursework: '📋', assignment: '✏️', study_session: '📖', personal: '🏠' }

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Academic Manager</h1>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
          <Plus className="w-4 h-4" /> Add Event
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border p-4 space-y-3">
          <input placeholder="Event title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <select value={form.event_type} onChange={e => setForm({ ...form, event_type: e.target.value })} className="px-3 py-2 border rounded-lg text-sm">
              {['class', 'exam', 'coursework', 'assignment', 'study_session', 'personal'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="px-3 py-2 border rounded-lg text-sm">
              {['critical', 'high', 'medium', 'low'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <input type="datetime-local" value={form.start_datetime} onChange={e => setForm({ ...form, start_datetime: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
            <input placeholder="Course code" value={form.course_code} onChange={e => setForm({ ...form, course_code: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_fixed} onChange={e => setForm({ ...form, is_fixed: e.target.checked })} /> Fixed event</label>
            <button onClick={handleSubmit} className="px-4 py-2 bg-success-600 text-white rounded-lg text-sm">Add</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {events?.map((e: any) => (
          <div key={e.id} className={`flex items-center gap-3 p-3 bg-white rounded-lg border ${e.is_completed ? 'opacity-50' : ''}`}>
            <button onClick={() => toggleComplete.mutate({ id: e.id, completed: !e.is_completed })}>
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${e.is_completed ? 'bg-success-500 border-success-500' : 'border-gray-300'}`}>
                {e.is_completed && <Check className="w-3 h-3 text-white" />}
              </div>
            </button>
            <span className="text-lg">{typeIcons[e.event_type] || '📅'}</span>
            <div className="flex-1">
              <p className={`text-sm font-medium ${e.is_completed ? 'line-through' : ''}`}>{e.title}</p>
              <p className="text-xs text-gray-500">
                {e.event_type.replace('_', ' ')} • {e.priority}
                {e.start_datetime ? ` • ${new Date(e.start_datetime).toLocaleString('en-MY', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}` : ''}
                {e.course_code ? ` • ${e.course_code}` : ''}
              </p>
            </div>
            {e.is_fixed && <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">Fixed</span>}
            <button onClick={() => deleteMutation.mutate(e.id)} className="text-gray-400 hover:text-danger-500"><Trash2 className="w-4 h-4" /></button>
          </div>
        ))}
      </div>
    </div>
  )
}

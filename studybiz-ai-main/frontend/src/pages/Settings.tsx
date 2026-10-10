import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { authAPI } from '../services/api'
import { Settings as SettingsIcon, User, Globe, Shield } from 'lucide-react'

export default function Settings() {
  const { user, updateUser } = useAuth()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
    campus: user?.campus || '',
    campus_state: user?.campus_state || '',
    whatsapp_handle: user?.whatsapp_handle || '',
    default_language: user?.default_language || 'en',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await authAPI.updateMe(form)
      updateUser(res.data)
      setSaved(true)
      setEditing(false)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update profile')
    }
    setSaving(false)
  }

  const malaysianStates = [
    'Selangor', 'Kuala Lumpur', 'Pulau Pinang', 'Johor', 'Perak', 'Sabah', 'Sarawak',
    'Negeri Sembilan', 'Kedah', 'Kelantan', 'Terengganu', 'Pahang', 'Melaka',
    'Perlis', 'Labuan', 'Putrajaya',
  ]

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm">Manage your StudyBiz AI profile and preferences</p>
      </div>

      {saved && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
          <span className="text-green-600 text-sm font-medium">Profile updated successfully!</span>
        </div>
      )}

      {/* Profile section */}
      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <div className="flex items-center gap-2 mb-4">
          <User className="w-5 h-5 text-primary-600" />
          <h2 className="font-semibold text-gray-900">Profile</h2>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium">Full Name</label>
              <input
                type="text"
                value={form.full_name}
                disabled={!editing}
                onChange={e => setForm({ ...form, full_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm disabled:bg-gray-50 disabled:text-gray-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Email</label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border rounded-lg text-sm bg-gray-50 text-gray-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium">Phone</label>
              <input
                type="text"
                value={form.phone}
                disabled={!editing}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="+60123456789"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">WhatsApp Handle</label>
              <input
                type="text"
                value={form.whatsapp_handle}
                disabled={!editing}
                onChange={e => setForm({ ...form, whatsapp_handle: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="wa.me/60123456789"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium">Campus / University</label>
              <input
                type="text"
                value={form.campus}
                disabled={!editing}
                onChange={e => setForm({ ...form, campus: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="e.g., Universiti Malaya"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Campus State (for holiday matching)</label>
              <select
                value={form.campus_state}
                disabled={!editing}
                onChange={e => setForm({ ...form, campus_state: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm disabled:bg-gray-50 disabled:text-gray-500"
              >
                <option value="">Select state...</option>
                {malaysianStates.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 font-medium">Default Language</label>
            <select
              value={form.default_language}
              disabled={!editing}
              onChange={e => setForm({ ...form, default_language: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm disabled:bg-gray-50 disabled:text-gray-500"
            >
              <option value="en">English</option>
              <option value="ms">Bahasa Melayu</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          {editing ? (
            <>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
            >
              Edit Profile
            </button>
          )}
        </div>
      </div>

      {/* Localization info */}
      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-primary-600" />
          <h2 className="font-semibold text-gray-900">Localization</h2>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <InfoRow label="Currency" value="MYR (RM)" />
          <InfoRow label="Timezone" value="Asia/Kuala_Lumpur (UTC+8)" />
          <InfoRow label="Date Format" value="DD/MM/YYYY" />
          <InfoRow label="Languages" value="English + Bahasa Melayu" />
          <InfoRow label="Rounding" value="Banker's (ROUND_HALF_EVEN)" />
          <InfoRow label="Monetary Type" value="Numeric(12,2) - no float" />
        </div>
      </div>

      {/* Security info */}
      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-primary-600" />
          <h2 className="font-semibold text-gray-900">Security</h2>
        </div>
        <div className="space-y-2 text-sm text-gray-600">
          <p>JWT-based authentication with bcrypt password hashing</p>
          <p>Approval gate enforced for consequential agent actions</p>
          <p>Token expires in 7 days - re-login required after expiry</p>
          <p>CORS configured for local development (127.0.0.1:5173)</p>
        </div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: any) {
  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  )
}

import { ReactNode, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { notificationAPI } from '../services/api'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutDashboard, Bot, Package, Calendar, GraduationCap, Boxes,
  Users, DollarSign, Group, AlertTriangle, MessageSquare, Clock,
  CheckSquare, ScrollText, Settings, Truck, LogOut, Menu, X, Bell
} from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/assistant', label: 'AI Assistant', icon: Bot },
  { to: '/orders', label: 'Orders', icon: Package },
  { to: '/calendar', label: 'Calendar', icon: Calendar },
  { to: '/academic', label: 'Academic', icon: GraduationCap },
  { to: '/products', label: 'Products & Inventory', icon: Boxes },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/bulk-orders', label: 'Bulk Orders', icon: Group },
  { to: '/suppliers', label: 'Suppliers', icon: Truck },
  { to: '/finance', label: 'Finance', icon: DollarSign },
  { to: '/messages', label: 'Messages', icon: MessageSquare },
  { to: '/exceptions', label: 'Exceptions', icon: AlertTriangle },
  { to: '/automation', label: 'Automation', icon: Clock },
  { to: '/approvals', label: 'Approvals', icon: CheckSquare },
  { to: '/agent-logs', label: 'Agent Logs', icon: ScrollText },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const { data: notifs } = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: () => notificationAPI.list(true).then(r => r.data),
  })

  const unreadCount = notifs?.length || 0

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/30 z-30 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed md:relative z-40 h-full w-64 bg-white border-r border-gray-200 flex flex-col transition-transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-sm">SB</div>
            <div>
              <h1 className="font-bold text-gray-900 text-sm">StudyBiz AI</h1>
              <p className="text-xs text-gray-500">Dormathon 2026</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`
              }
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              <span className="truncate">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 text-xs font-bold">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-danger-600 hover:bg-danger-50 rounded-lg transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="md:hidden p-1">
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/approvals')}
              className="relative p-2 text-gray-600 hover:text-gray-900"
              title="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-0 right-0 w-4 h-4 bg-danger-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  )
}

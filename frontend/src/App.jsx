import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Bot, Package, ShoppingBag, Users, Inbox,
  AlertTriangle, Truck, Settings as SettingsIcon, Cog, MessageSquare
} from 'lucide-react'
import Overview from './pages/Overview.jsx'
import AIAdmin from './pages/AIAdmin.jsx'
import GroupBuys from './pages/GroupBuys.jsx'
import Orders from './pages/Orders.jsx'
import Customers from './pages/Customers.jsx'
import InboxPage from './pages/Inbox.jsx'
import Approvals from './pages/Approvals.jsx'
import SupplierSummary from './pages/SupplierSummary.jsx'
import AutomationRules from './pages/AutomationRules.jsx'
import SettingsPage from './pages/Settings.jsx'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/ai-admin', label: 'AI Co-Admin', icon: Bot },
  { to: '/group-buys', label: 'Group Buys', icon: Package },
  { to: '/orders', label: 'Orders', icon: ShoppingBag },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/inbox', label: 'Customer Inbox', icon: Inbox },
  { to: '/approvals', label: 'Approvals', icon: AlertTriangle },
  { to: '/supplier', label: 'Supplier Summary', icon: Truck },
  { to: '/automation', label: 'Automation Rules', icon: Cog },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-stone-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-stone-200">
        <h1 className="text-lg font-bold text-stone-900">Synchrost AI</h1>
        <p className="text-xs text-stone-500 mt-1">Your AI Co-Admin</p>
      </div>
      <nav className="flex-1 p-3">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium mb-0.5 transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-stone-600 hover:bg-stone-100'
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-stone-200">
        <DemoBadge />
      </div>
    </aside>
  )
}

function DemoBadge() {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="inline-block w-2 h-2 rounded-full bg-amber-500"></span>
      <span className="text-stone-500">Demo Mode Active</span>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/ai-admin" element={<AIAdmin />} />
            <Route path="/group-buys" element={<GroupBuys />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/inbox" element={<InboxPage />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/supplier" element={<SupplierSummary />} />
            <Route path="/automation" element={<AutomationRules />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

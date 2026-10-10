import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AIAssistant from './pages/AIAssistant'
import Orders from './pages/Orders'
import Calendar from './pages/Calendar'
import Academic from './pages/Academic'
import Products from './pages/Products'
import Customers from './pages/Customers'
import Finance from './pages/Finance'
import BulkOrders from './pages/BulkOrders'
import Exceptions from './pages/Exceptions'
import Messages from './pages/Messages'
import Automation from './pages/Automation'
import Approvals from './pages/Approvals'
import AgentLogs from './pages/AgentLogs'
import Settings from './pages/Settings'
import Suppliers from './pages/Suppliers'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div></div>
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Layout>{children}</Layout>
}

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/assistant" element={<ProtectedRoute><AIAssistant /></ProtectedRoute>} />
      <Route path="/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
      <Route path="/calendar" element={<ProtectedRoute><Calendar /></ProtectedRoute>} />
      <Route path="/academic" element={<ProtectedRoute><Academic /></ProtectedRoute>} />
      <Route path="/products" element={<ProtectedRoute><Products /></ProtectedRoute>} />
      <Route path="/customers" element={<ProtectedRoute><Customers /></ProtectedRoute>} />
      <Route path="/finance" element={<ProtectedRoute><Finance /></ProtectedRoute>} />
      <Route path="/bulk-orders" element={<ProtectedRoute><BulkOrders /></ProtectedRoute>} />
      <Route path="/exceptions" element={<ProtectedRoute><Exceptions /></ProtectedRoute>} />
      <Route path="/messages" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
      <Route path="/automation" element={<ProtectedRoute><Automation /></ProtectedRoute>} />
      <Route path="/approvals" element={<ProtectedRoute><Approvals /></ProtectedRoute>} />
      <Route path="/agent-logs" element={<ProtectedRoute><AgentLogs /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="/suppliers" element={<ProtectedRoute><Suppliers /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

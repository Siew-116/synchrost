import { useQuery } from '@tanstack/react-query'
import { customerAPI, orderAPI } from '../services/api'
import { Users, Phone, Instagram } from 'lucide-react'

export default function Customers() {
  const { data: customers } = useQuery({ queryKey: ['customers'], queryFn: () => customerAPI.list().then(r => r.data) })
  const { data: orders } = useQuery({ queryKey: ['orders'], queryFn: () => orderAPI.list().then(r => r.data) })

  const orderCount = (cid: number) => orders?.filter((o: any) => o.customer_id === cid).length || 0

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Contact</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600">Orders</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {customers?.map((c: any) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold">{c.name[0]}</div>
                    <span className="font-medium text-gray-900">{c.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {c.whatsapp_number && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{c.whatsapp_number}</span>}
                  {c.instagram_handle && <span className="flex items-center gap-1 text-gray-400"><Instagram className="w-3 h-3" />{c.instagram_handle}</span>}
                </td>
                <td className="px-4 py-3 text-center"><span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">{orderCount(c.id)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm text-gray-400">{customers?.length || 0} customers total</p>
    </div>
  )
}

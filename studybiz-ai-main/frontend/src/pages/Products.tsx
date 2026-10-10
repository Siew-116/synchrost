import { useQuery } from '@tanstack/react-query'
import { productAPI } from '../services/api'
import { AlertTriangle, Boxes } from 'lucide-react'

export default function Products() {
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => productAPI.list().then(r => r.data) })
  const { data: lowStock } = useQuery({ queryKey: ['low-stock'], queryFn: () => productAPI.lowStock().then(r => r.data) })

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Products & Inventory</h1>

      {lowStock && lowStock.length > 0 && (
        <div className="flex items-center gap-2 p-3 bg-warning-50 rounded-lg border border-warning-200">
          <AlertTriangle className="w-5 h-5 text-warning-600" />
          <p className="text-sm text-warning-700">{lowStock.length} product(s) are low on stock</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products?.map((p: any) => (
          <div key={p.id} className="bg-white rounded-xl border p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-gray-900 text-sm">{p.name}</h3>
                <p className="text-xs text-gray-500">{p.category} • {p.sku}</p>
              </div>
              {p.is_preorder && <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded">Preorder</span>}
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-lg font-bold text-gray-900">RM {p.selling_price}</span>
              {p.cost_price && <span className="text-xs text-gray-400">cost: RM {p.cost_price}</span>}
            </div>
            <div className="mt-3 flex items-center gap-4 text-xs">
              <div className={`flex items-center gap-1 ${p.available_stock <= p.low_stock_threshold ? 'text-danger-600' : 'text-gray-500'}`}>
                <Boxes className="w-3 h-3" />
                {p.available_stock} available
              </div>
              {p.reserved_stock > 0 && <span className="text-warning-600">{p.reserved_stock} reserved</span>}
              {p.incoming_stock > 0 && <span className="text-success-600">{p.incoming_stock} incoming</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { listProducts, createProduct, deleteProduct } from '../api/api'

const inputStyle = {
  width: '100%', padding: '8px 12px', border: '1px solid #d1d5db',
  borderRadius: '6px', fontSize: '14px', outline: 'none', boxSizing: 'border-box',
}
const labelStyle = { display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }
const btnPrimary = { padding: '8px 16px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }
const btnDanger = { padding: '6px 12px', backgroundColor: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }
const btnGhost = { padding: '6px 12px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }

export default function MaterialManagement() {
  const [products, setProducts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', code: '', safety_stock: 0 })

  const load = async () => {
    const data = await listProducts()
    setProducts(data)
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async () => {
    if (!form.name.trim()) return
    await createProduct(form)
    setForm({ name: '', code: '', safety_stock: 0 })
    setShowForm(false)
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除该物料？')) return
    await deleteProduct(id)
    load()
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px 12px', borderBottom: '2px solid #3b82f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>📦 物料管理</h3>
        <button onClick={() => { setShowForm(!showForm); setForm({ name: '', code: '', safety_stock: 0 }) }} style={btnPrimary}>
          + 添加物料
        </button>
      </div>

      {showForm && (
        <div style={{ padding: '16px 20px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
            <div>
              <label style={labelStyle}>物料名称</label>
              <input style={inputStyle} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="输入物料名称" />
            </div>
            <div>
              <label style={labelStyle}>物料代码</label>
              <input style={inputStyle} value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} placeholder="输入物料代码" />
            </div>
            <div>
              <label style={labelStyle}>安全库存</label>
              <input type="number" style={inputStyle} value={form.safety_stock} onChange={e => setForm({ ...form, safety_stock: parseFloat(e.target.value) || 0 })} />
            </div>
          </div>
          <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
            <button onClick={handleSubmit} style={btnPrimary}>确认添加</button>
            <button onClick={() => setShowForm(false)} style={btnGhost}>取消</button>
          </div>
        </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f8fafc' }}>
            <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#475569' }}>物料代码</th>
            <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#475569' }}>名称</th>
            <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#475569' }}>安全库存</th>
            <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#475569' }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {products.length === 0 && (
            <tr><td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: '#9ca3af' }}>暂无物料，请先添加</td></tr>
          )}
          {products.map(p => (
            <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
              <td style={{ padding: '10px 16px', color: '#6b7280', fontFamily: 'monospace' }}>{p.code || '-'}</td>
              <td style={{ padding: '10px 16px', fontWeight: '500' }}>{p.name}</td>
              <td style={{ padding: '10px 16px', textAlign: 'center' }}>{p.safety_stock}</td>
              <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                <button onClick={() => handleDelete(p.id)} style={btnDanger}>删除</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
import { useState, useEffect } from 'react'
import { listProducts, listLines, createLine, deleteLine } from '../api/api'

const inputStyle = {
  width: '100%', padding: '8px 12px', border: '1px solid #d1d5db',
  borderRadius: '6px', fontSize: '14px', outline: 'none', boxSizing: 'border-box',
}
const labelStyle = { display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }
const btnPrimary = { padding: '8px 16px', backgroundColor: '#059669', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }
const btnDanger = { padding: '6px 12px', backgroundColor: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }
const btnGhost = { padding: '6px 12px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }

export default function LineManagement() {
  const [lines, setLines] = useState([])
  const [products, setProducts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', products: [] })

  const load = async () => {
    const [lineData, prodData] = await Promise.all([listLines(), listProducts()])
    setLines(lineData)
    setProducts(prodData)
  }

  useEffect(() => { load() }, [])

  const addProductToForm = () => {
    setForm(prev => ({ ...prev, products: [...prev.products, { product_id: '', rated_output: 0 }] }))
  }

  const removeProductFromForm = (idx) => {
    setForm(prev => ({ ...prev, products: prev.products.filter((_, i) => i !== idx) }))
  }

  const updateFormProduct = (idx, key, value) => {
    setForm(prev => {
      const prods = [...prev.products]
      prods[idx] = { ...prods[idx], [key]: key === 'product_id' ? value : (parseFloat(value) || 0) }
      return { ...prev, products: prods }
    })
  }

  const handleSubmit = async () => {
    if (!form.name.trim()) return
    if (form.products.length < 2) { alert('产线至少需要添加2个物料'); return }
    await createLine(form)
    setForm({ name: '', products: [] })
    setShowForm(false)
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除该产线？关联的交货计划也会被删除。')) return
    await deleteLine(id)
    load()
  }

  const getProductName = (productId) => {
    const p = products.find(x => x.id === parseInt(productId))
    return p ? p.name : ''
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px 12px', borderBottom: '2px solid #059669', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>🏭 产线管理</h3>
        <button onClick={() => { setShowForm(!showForm); setForm({ name: '', products: [] }) }} style={btnPrimary}>
          + 添加产线
        </button>
      </div>

      {showForm && (
        <div style={{ padding: '16px 20px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ marginBottom: '12px' }}>
            <label style={labelStyle}>产线名称</label>
            <input style={inputStyle} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="输入产线名称" />
          </div>
          <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ ...labelStyle, marginBottom: 0 }}>产线可生产物料</label>
            <button onClick={addProductToForm} style={{ ...btnGhost, fontSize: '12px' }}>+ 添加物料</button>
          </div>
          {form.products.map((fp, idx) => (
            <div key={idx} style={{ display: 'grid', gridTemplateColumns: '3fr 1fr auto', gap: '8px', marginBottom: '8px', alignItems: 'end' }}>
              <div>
                <select style={inputStyle} value={fp.product_id} onChange={e => updateFormProduct(idx, 'product_id', e.target.value)}>
                  <option value="">选择物料</option>
                  {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{ ...labelStyle, fontSize: '11px' }}>8H班产量</label>
                <input type="number" style={inputStyle} value={fp.rated_output} onChange={e => updateFormProduct(idx, 'rated_output', e.target.value)} />
              </div>
              <button onClick={() => removeProductFromForm(idx)} style={{ ...btnDanger, height: '36px' }}>✕</button>
            </div>
          ))}
          {form.products.length > 0 && (
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>
              安全库存将从物料信息中自动带入
            </div>
          )}
          <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
            <button onClick={handleSubmit} style={btnPrimary}>确认添加</button>
            <button onClick={() => setShowForm(false)} style={btnGhost}>取消</button>
          </div>
        </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f8fafc' }}>
            <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#475569' }}>产线名称</th>
            <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#475569' }}>可生产物料</th>
            <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#475569' }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {lines.length === 0 && (
            <tr><td colSpan={3} style={{ padding: '24px', textAlign: 'center', color: '#9ca3af' }}>暂无产线，请先添加</td></tr>
          )}
          {lines.map(l => (
            <tr key={l.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
              <td style={{ padding: '10px 16px', fontWeight: '500' }}>{l.name}</td>
              <td style={{ padding: '10px 16px' }}>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {l.products.map(lp => (
                    <span key={lp.id} style={{ padding: '2px 8px', backgroundColor: '#eff6ff', color: '#2563eb', borderRadius: '4px', fontSize: '12px', fontWeight: '500' }}>
                      {lp.product_name}(8H班产量{lp.rated_output})
                    </span>
                  ))}
                </div>
              </td>
              <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                <button onClick={() => handleDelete(l.id)} style={btnDanger}>删除</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

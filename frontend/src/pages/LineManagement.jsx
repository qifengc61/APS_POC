import { useState, useEffect } from 'react'
import { listLines, createLine, deleteLine, listProducts, createProduct, deleteProduct } from '../api/api'

const inputStyle = {
  width: '100%', padding: '8px 12px', border: '1px solid #d1d5db',
  borderRadius: '6px', fontSize: '14px', outline: 'none', boxSizing: 'border-box',
}
const labelStyle = { display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }
const btnPrimary = { padding: '8px 16px', backgroundColor: '#059669', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }
const btnDanger = { padding: '6px 12px', backgroundColor: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }
const btnGhost = { padding: '6px 12px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }

export default function LineManagementPage() {
  const [lines, setLines] = useState([])
  const [products, setProducts] = useState([])
  const [showLineForm, setShowLineForm] = useState(false)
  const [lineForm, setLineForm] = useState({
    name: '',
    products: [{ product_id: '', rated_output: 0 }],
  })

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    const [lineData, productData] = await Promise.all([listLines(), listProducts()])
    setLines(lineData)
    setProducts(productData)
  }

  const addLineProduct = () => {
    if (lineForm.products.length >= 6) return
    setLineForm(prev => ({
      ...prev,
      products: [...prev.products, { product_id: '', rated_output: 0 }],
    }))
  }

  const removeLineProduct = (idx) => {
    setLineForm(prev => ({
      ...prev,
      products: prev.products.filter((_, i) => i !== idx),
    }))
  }

  const updateLineProduct = (idx, field, value) => {
    setLineForm(prev => {
      const prods = [...prev.products]
      prods[idx] = { ...prods[idx], [field]: field === 'product_id' ? (parseInt(value) || '') : (parseFloat(value) || 0) }
      if (field === 'product_id' && value) {
        const prod = products.find(p => p.id === parseInt(value))
        if (prod) {
          prods[idx].safety_stock = prod.safety_stock || 0
        }
      }
      return { ...prev, products: prods }
    })
  }

  const handleCreateLine = async () => {
    if (!lineForm.name.trim()) { alert('请输入产线名称'); return }
    const validProds = lineForm.products.filter(p => p.product_id)
    if (validProds.length < 1) { alert('至少需要添加1个物料'); return }
    const ids = validProds.map(p => p.product_id)
    if (new Set(ids).size !== ids.length) { alert('物料不能重复'); return }
    await createLine({
      name: lineForm.name,
      products: validProds.map(p => ({
        product_id: p.product_id,
        rated_output: p.rated_output,
      })),
    })
    setLineForm({ name: '', products: [{ product_id: '', rated_output: 0 }] })
    setShowLineForm(false)
    loadData()
  }

  const handleDeleteLine = async (id) => {
    if (!confirm('确定删除该产线？关联的交货计划也会被删除')) return
    await deleteLine(id)
    loadData()
  }

  return (
    <div>
      <div style={{ backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px 12px', borderBottom: '2px solid #059669', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>🏭 产线管理</h3>
          <button onClick={() => setShowLineForm(!showLineForm)} style={btnPrimary}>
            + 新建产线
          </button>
        </div>

        {showLineForm && (
          <div style={{ padding: '16px 20px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <div style={{ marginBottom: '12px' }}>
              <label style={labelStyle}>产线名称</label>
              <input style={inputStyle} value={lineForm.name} onChange={e => setLineForm({ ...lineForm, name: e.target.value })} placeholder="输入产线名称" />
            </div>

            <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ ...labelStyle, marginBottom: 0 }}>可生产物料（1~6个）</label>
              <button onClick={addLineProduct} style={{ ...btnGhost, fontSize: '12px' }} disabled={lineForm.products.length >= 6}>
                + 添加物料 {lineForm.products.length >= 6 ? '(已达上限)' : `(${lineForm.products.length}/6)`}
              </button>
            </div>

            {lineForm.products.map((lp, idx) => (
              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '8px', marginBottom: '8px', alignItems: 'end' }}>
                <div>
                  <label style={{ ...labelStyle, fontSize: '11px' }}>物料 {idx + 1}</label>
                  <select style={inputStyle} value={lp.product_id} onChange={e => updateLineProduct(idx, 'product_id', e.target.value)}>
                    <option value="">选择物料</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ ...labelStyle, fontSize: '11px' }}>8H班产量</label>
                  <input type="number" style={inputStyle} value={lp.rated_output || ''} onChange={e => updateLineProduct(idx, 'rated_output', e.target.value)} placeholder="0" />
                </div>
                <button onClick={() => removeLineProduct(idx)} style={{ ...btnDanger, height: '36px' }}>✕</button>
              </div>
            ))}

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button onClick={handleCreateLine} style={btnPrimary}>确认创建</button>
              <button onClick={() => setShowLineForm(false)} style={btnGhost}>取消</button>
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
              <tr><td colSpan={3} style={{ padding: '24px', textAlign: 'center', color: '#9ca3af' }}>暂无产线，请先创建</td></tr>
            )}
            {lines.map(l => (
              <tr key={l.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px 16px', fontWeight: '500' }}>{l.name}</td>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {(l.products || []).map((lp, idx) => (
                      <span key={idx} style={{
                        padding: '2px 8px', borderRadius: '4px', fontSize: '12px',
                        backgroundColor: '#ecfdf5', color: '#059669',
                      }}>
                        {lp.product_name} (产量{lp.rated_output})
                      </span>
                    ))}
                  </div>
                </td>
                <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                  <button onClick={() => handleDeleteLine(l.id)} style={btnDanger}>删除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

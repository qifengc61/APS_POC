import { useState, useEffect } from 'react'
import { listLines, listDeliveryPlans, createDeliveryPlan, deleteDeliveryPlan } from '../api/api'
import dayjs from 'dayjs'

const inputStyle = {
  width: '100%', padding: '8px 12px', border: '1px solid #d1d5db',
  borderRadius: '6px', fontSize: '14px', outline: 'none', boxSizing: 'border-box',
}
const labelStyle = { display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }
const btnPrimary = { padding: '8px 16px', backgroundColor: '#7c3aed', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }
const btnDanger = { padding: '6px 12px', backgroundColor: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }
const btnGhost = { padding: '6px 12px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }

export default function DeliveryPlanPage() {
  const [plans, setPlans] = useState([])
  const [lines, setLines] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '',
    line_id: '',
    materials: [],
    start_date: dayjs().format('YYYY-MM-DD'),
    end_date: dayjs().add(29, 'day').format('YYYY-MM-DD'),
  })
  const [selectedLine, setSelectedLine] = useState(null)

  const load = async () => {
    const [planData, lineData] = await Promise.all([listDeliveryPlans(), listLines()])
    setPlans(planData)
    setLines(lineData)
  }

  useEffect(() => { load() }, [])

  const handleLineChange = (lineId) => {
    const line = lines.find(l => l.id === parseInt(lineId))
    setSelectedLine(line || null)
    setForm(prev => ({ ...prev, line_id: lineId ? parseInt(lineId) : '', materials: [] }))
  }

  const addMaterial = () => {
    setForm(prev => ({ ...prev, materials: [...prev.materials, { line_product_id: '', daily_deliveries_str: '', computed_total: 0 }] }))
  }

  const removeMaterial = (idx) => {
    setForm(prev => ({ ...prev, materials: prev.materials.filter((_, i) => i !== idx) }))
  }

  const getDaysCount = () => {
    if (!form.start_date || !form.end_date) return 0
    const s = dayjs(form.start_date)
    const e = dayjs(form.end_date)
    return e.diff(s, 'day') + 1
  }

  const parseAndValidateDaily = (str, daysCount) => {
    if (!str || !str.trim()) return { values: null, total: 0, error: null }
    const parts = str.trim().split(/\s+/)
    if (parts.length !== daysCount) {
      return { values: null, total: 0, error: `数量不匹配：输入${parts.length}个值，需要${daysCount}天` }
    }
    const nums = []
    for (const p of parts) {
      const n = parseInt(p)
      if (isNaN(n) || n < 0) {
        return { values: null, total: 0, error: `"${p}" 不是有效的非负整数` }
      }
      nums.push(n)
    }
    return { values: nums, total: nums.reduce((a, b) => a + b, 0), error: null }
  }

  const updateMaterialDaily = (idx, str) => {
    const daysCount = getDaysCount()
    setForm(prev => {
      const materials = [...prev.materials]
      const result = parseAndValidateDaily(str, daysCount)
      materials[idx] = { ...materials[idx], daily_deliveries_str: str, computed_total: result.total, daily_error: result.error }
      return { ...prev, materials }
    })
  }

  const handleSubmit = async () => {
    if (!form.name.trim() || !form.line_id) {
      alert('请填写计划名称并选择产线')
      return
    }
    if (form.materials.length < 2) {
      alert('至少需要添加2个物料')
      return
    }
    const daysCount = getDaysCount()
    for (let i = 0; i < form.materials.length; i++) {
      const m = form.materials[i]
      if (!m.line_product_id) {
        alert(`请选择第${i + 1}个物料`)
        return
      }
      if (!m.daily_deliveries_str || !m.daily_deliveries_str.trim()) {
        alert(`请为第${i + 1}个物料填写每日交货量`)
        return
      }
      const result = parseAndValidateDaily(m.daily_deliveries_str, daysCount)
      if (result.error) {
        alert(`第${i + 1}个物料：${result.error}`)
        return
      }
    }
    const ids = form.materials.map(m => m.line_product_id)
    if (new Set(ids).size !== ids.length) {
      alert('物料不能重复')
      return
    }
    await createDeliveryPlan({
      name: form.name,
      line_id: form.line_id,
      materials: form.materials.map(m => ({
        line_product_id: m.line_product_id,
        initial_inventory: m.initial_inventory || 0,
        daily_deliveries: m.daily_deliveries_str.trim(),
        total_delivery: m.computed_total,
      })),
      start_date: form.start_date,
      end_date: form.end_date,
    })
    setForm({
      name: '', line_id: '', materials: [],
      start_date: dayjs().format('YYYY-MM-DD'),
      end_date: dayjs().add(29, 'day').format('YYYY-MM-DD'),
    })
    setSelectedLine(null)
    setShowForm(false)
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除该交货计划？')) return
    await deleteDeliveryPlan(id)
    load()
  }

  const lineProducts = selectedLine ? selectedLine.products : []
  const daysCount = getDaysCount()

  return (
    <div>
      <div style={{ backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px 12px', borderBottom: '2px solid #7c3aed', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>📋 交货计划</h3>
          <button onClick={() => setShowForm(!showForm)} style={btnPrimary}>
            + 新建交货计划
          </button>
        </div>

        {showForm && (
          <div style={{ padding: '16px 20px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <div style={{ marginBottom: '12px' }}>
              <label style={labelStyle}>计划名称</label>
              <input style={inputStyle} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="输入交货计划名称" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={labelStyle}>选择产线</label>
                <select style={inputStyle} value={form.line_id} onChange={e => handleLineChange(e.target.value)}>
                  <option value="">请选择产线</option>
                  {lines.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>排产日期范围</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input type="date" style={inputStyle} value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} />
                  <span style={{ color: '#9ca3af' }}>~</span>
                  <input type="date" style={inputStyle} value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} />
                </div>
                {form.start_date && form.end_date && (
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>共 {daysCount} 天</div>
                )}
              </div>
            </div>

            {selectedLine && (
              <>
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>交货物料</label>
                  <button onClick={addMaterial} style={{ ...btnGhost, fontSize: '12px' }} disabled={form.materials.length >= 2}>
                    + 添加物料
                  </button>
                </div>
                {form.materials.map((fm, idx) => {
                  const lp = lineProducts.find(x => x.id === parseInt(fm.line_product_id))
                  return (
                    <div key={idx} style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr auto', gap: '8px', marginBottom: '8px', alignItems: 'end' }}>
                        <div>
                          <label style={{ ...labelStyle, fontSize: '11px' }}>选择物料</label>
                          <select style={inputStyle} value={fm.line_product_id} onChange={e => setForm(prev => { const m = [...prev.materials]; m[idx] = { line_product_id: parseInt(e.target.value), initial_inventory: 0, daily_deliveries_str: '', computed_total: 0, daily_error: null }; return { ...prev, materials: m } })}>
                            <option value="">选择物料</option>
                            {lineProducts.map(lp => <option key={lp.id} value={lp.id}>{lp.product_name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label style={{ ...labelStyle, fontSize: '11px' }}>初期库存</label>
                          <input type="number" style={inputStyle} value={fm.initial_inventory || 0} onChange={e => setForm(prev => { const m = [...prev.materials]; m[idx] = { ...m[idx], initial_inventory: parseFloat(e.target.value) || 0 }; return { ...prev, materials: m } })} />
                        </div>
                        <button onClick={() => removeMaterial(idx)} style={{ ...btnDanger, height: '36px' }}>✕</button>
                      </div>
                      <div style={{ marginBottom: '4px' }}>
                        <label style={{ ...labelStyle, fontSize: '11px' }}>每日交货量（空格分隔，共 {daysCount} 个值）</label>
                        <textarea
                          style={{ ...inputStyle, minHeight: '60px', resize: 'vertical', fontFamily: 'monospace', fontSize: '12px' }}
                          value={fm.daily_deliveries_str}
                          onChange={e => updateMaterialDaily(idx, e.target.value)}
                          placeholder="例如：125 55 220 179 181 16 268 240 ..."
                        />
                      </div>
                      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '12px' }}>
                        {fm.daily_error ? (
                          <span style={{ color: '#dc2626' }}>⚠ {fm.daily_error}</span>
                        ) : fm.daily_deliveries_str.trim() ? (
                          <>
                            <span style={{ color: '#374151', fontWeight: '600' }}>总交货量：{fm.computed_total}</span>
                            <span style={{ color: '#6b7280' }}>已输入 {fm.daily_deliveries_str.trim().split(/\s+/).length} / {daysCount} 天</span>
                          </>
                        ) : null}
                      </div>
                      {lp && fm.line_product_id && (
                        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px' }}>
                          安全库存{lp.safety_stock} / 8H班产量{lp.rated_output}
                        </div>
                      )}
                    </div>
                  )
                })}
                {lineProducts.length < 2 && (
                  <div style={{ padding: '12px', backgroundColor: '#fef3c7', borderRadius: '8px', color: '#92400e', fontSize: '13px', marginBottom: '12px' }}>
                    ⚠️ 该产线关联的物料不足2个，请先在产线管理中为产线添加至少2个物料
                  </div>
                )}
              </>
            )}

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button onClick={handleSubmit} style={btnPrimary}>确认创建</button>
              <button onClick={() => { setShowForm(false); setSelectedLine(null) }} style={btnGhost}>取消</button>
            </div>
          </div>
        )}

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc' }}>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#475569' }}>计划名称</th>
              <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#475569' }}>产线</th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#475569' }}>交货物料</th>
              <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#475569' }}>排产日期</th>
              <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#475569' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {plans.length === 0 && (
              <tr><td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: '#9ca3af' }}>暂无交货计划，请先创建</td></tr>
            )}
            {plans.map(p => (
              <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px 16px', fontWeight: '500' }}>{p.name}</td>
                <td style={{ padding: '10px 16px', textAlign: 'center' }}>{p.line_name}</td>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {p.materials.map((m, idx) => (
                      <span key={idx} style={{
                        padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '500',
                        backgroundColor: idx === 0 ? '#eff6ff' : '#ecfdf5',
                        color: idx === 0 ? '#2563eb' : '#059669',
                      }}>
                        {m.product_name}(总交货量{m.total_delivery})
                      </span>
                    ))}
                  </div>
                </td>
                <td style={{ padding: '10px 16px', textAlign: 'center', fontSize: '12px' }}>{p.start_date} ~ {p.end_date}</td>
                <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                  <button onClick={() => handleDelete(p.id)} style={btnDanger}>删除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
import { useState } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

const MATERIAL_COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']

export default function ResultCharts({ result, activeProductIdx = 0, materials = [] }) {
  if (!result || !result.daily_results || result.daily_results.length === 0) return null

  const [overviewIdx, setOverviewIdx] = useState(0)

  const color = MATERIAL_COLORS[activeProductIdx % MATERIAL_COLORS.length]
  const productName = materials[activeProductIdx]?.product_name || `物料${activeProductIdx + 1}`
  const safetyStock = materials[activeProductIdx]?.safety_stock || 0
  const numProducts = result.num_products || materials.length || 1
  const productStats = result.product_stats || []

  const outputData = result.daily_results.map(dr => {
    const p = dr.products?.[activeProductIdx]
    const entry = { date: dr.date.slice(5) }
    entry[`${productName}-产量`] = p?.daily_output
    entry[`${productName}-交货`] = p?.daily_delivery
    return entry
  })

  const inventoryData = result.daily_results.map(dr => {
    const p = dr.products?.[activeProductIdx]
    return {
      date: dr.date.slice(5),
      [`${productName}-库存`]: p?.closing_inventory,
    }
  })

  const shiftData = result.daily_results.map(dr => {
    const entry = { date: dr.date.slice(5), is_rest: dr.is_rest }
    for (let i = 0; i < numProducts; i++) {
      const name = materials[i]?.product_name || `物料${i + 1}`
      entry[`${name}-工时`] = dr.products?.[i]?.work_hours
    }
    return entry
  })

  const shiftBarEntries = []
  for (let i = 0; i < numProducts; i++) {
    const name = materials[i]?.product_name || `物料${i + 1}`
    const barColor = MATERIAL_COLORS[i % MATERIAL_COLORS.length]
    shiftBarEntries.push(<Bar key={i} dataKey={`${name}-工时`} stackId="a" fill={barColor} radius={i === numProducts - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]} />)
  }

  const stats = productStats[overviewIdx] || {}

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📈 {productName} 每日产量趋势</h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={outputData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={`${productName}-产量`} stroke={color} strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey={`${productName}-交货`} stroke="#9ca3af" strokeWidth={1.5} dot={false} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📦 {productName} 库存变化趋势</h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={inventoryData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <ReferenceLine y={safetyStock} stroke={color} strokeDasharray="5 5" label={{ value: '安全库存', position: 'right', fontSize: 10, fill: color }} />
            <Line type="monotone" dataKey={`${productName}-库存`} stroke={color} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>⚙️ 每日工时分配 (上限 24h)</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={shiftData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 24]} />
            <Tooltip />
            <Legend />
            <ReferenceLine y={24} stroke="#ef4444" strokeDasharray="5 5" />
            {shiftBarEntries}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h4 style={{ margin: 0, fontSize: '14px', color: '#1f2937' }}>📊 方案统计概览</h4>
          {numProducts > 1 && (
            <select
              value={overviewIdx}
              onChange={e => setOverviewIdx(parseInt(e.target.value))}
              style={{
                padding: '4px 8px', border: '1px solid #d1d5db', borderRadius: '6px',
                fontSize: '12px', outline: 'none', cursor: 'pointer',
              }}
            >
              {materials.map((m, idx) => (
                <option key={idx} value={idx}>{idx + 1} - {m.product_name}</option>
              ))}
            </select>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <StatCard label="产线运行天数" value={result.total_production_days} unit="天" color="#3b82f6" />
          <StatCard label="休息日占用天数" value={result.rest_days_occupied ?? 0} unit="天" color="#ef4444" />
          <div style={{ gridColumn: '1 / -1', borderTop: '1px solid #e5e7eb', margin: '4px 0' }} />
          {(() => {
            const m = materials[overviewIdx]
            const mColor = MATERIAL_COLORS[overviewIdx % MATERIAL_COLORS.length]
            return (
              <div key={overviewIdx} style={{ gridColumn: '1 / -1' }}>
                <div style={{ fontSize: '12px', fontWeight: '600', color: mColor, marginBottom: '6px', paddingLeft: '4px', borderLeft: `3px solid ${mColor}` }}>
                  {m?.product_name || `物料${overviewIdx + 1}`}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <StatCard label="生产天数" value={stats.total_production_days} unit="天" color={mColor} />
                  <StatCard label="休息日生产" value={stats.holiday_production_days} unit="天" color="#ef4444" />
                  <StatCard label="库存最小值" value={stats.min_inventory} unit="" color="#10b981" />
                  <StatCard label="最终结存" value={stats.final_inventory ?? '—'} unit="" color="#8b5cf6" />
                </div>
              </div>
            )
          })()}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, unit, color }) {
  return (
    <div style={{
      padding: '10px',
      backgroundColor: '#f9fafb',
      borderRadius: '8px',
      textAlign: 'center',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '2px' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: '700', color }}>{value}{unit}</div>
    </div>
  )
}

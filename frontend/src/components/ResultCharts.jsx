import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts'

const SHIFT_LEGEND = [
  { label: '班次1（正常）', color: '#2563eb' },
  { label: '班次1（加班）', color: '#ef4444' },
  { label: '班次2（正常）', color: '#10b981' },
  { label: '班次2（加班）', color: '#f59e0b' },
]

function ShiftLegend() {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center', marginTop: '4px' }}>
      {SHIFT_LEGEND.map(item => (
        <span key={item.label} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#374151' }}>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '2px', backgroundColor: item.color }} />
          {item.label}
        </span>
      ))}
    </div>
  )
}

export default function ResultCharts({ result, safetyStock }) {
  if (!result || !result.daily_results || result.daily_results.length === 0) return null

  const outputData = result.daily_results.map(dr => ({
    date: dr.date.slice(5),
    当日产量: dr.daily_output,
    当日交货量: dr.daily_delivery,
  }))

  const inventoryData = result.daily_results.map(dr => ({
    date: dr.date.slice(5),
    结存库存: dr.closing_inventory,
  }))

  const shiftData = result.daily_results.map(dr => ({
    date: dr.date.slice(5),
    班次1: dr.shift1,
    班次2: dr.shift2,
    is_rest: dr.is_rest,
    is_adjusted: dr.is_adjusted_workday,
  }))

  const getBar1Color = (entry) => {
    if (entry.班次1 > 1.0 || (entry.is_rest && entry.班次1 > 0)) return '#ef4444'
    return '#2563eb'
  }

  const getBar2Color = (entry) => {
    if (entry.班次2 > 1.0 || (entry.is_rest && entry.班次2 > 0)) return '#f59e0b'
    return '#10b981'
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📈 每日产量与交货量趋势</h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={outputData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="当日产量" stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="当日交货量" stroke="#f59e0b" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📦 库存变化趋势</h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={inventoryData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <ReferenceLine y={safetyStock} stroke="#ef4444" strokeDasharray="5 5" label={{ value: '安全库存', position: 'right', fontSize: 11 }} />
            <Line type="monotone" dataKey="结存库存" stroke="#10b981" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>⚙️ 每日班次安排</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={shiftData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 3]} />
            <Tooltip />
            <Bar dataKey="班次1" stackId="a" radius={[0, 0, 0, 0]}>
              {shiftData.map((entry, idx) => (
                <Cell key={idx} fill={getBar1Color(entry)} />
              ))}
            </Bar>
            <Bar dataKey="班次2" stackId="a" radius={[4, 4, 0, 0]}>
              {shiftData.map((entry, idx) => (
                <Cell key={idx} fill={getBar2Color(entry)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <ShiftLegend />
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📊 方案统计概览</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <StatCard label="总生产天数" value={result.total_production_days} unit="天" color="#3b82f6" />
          <StatCard label="加班天数" value={result.overtime_days} unit="天" color="#f59e0b" />
          <StatCard label="加班班次" value={result.overtime_shifts ?? '—'} unit="个" color="#ea580c" />
          <StatCard label="休息日生产" value={result.holiday_production_days} unit="天" color="#ef4444" />
          <StatCard label="库存最小值" value={result.min_inventory} unit="" color="#10b981" />
          <StatCard label="最终结存库存" value={result.final_inventory ?? '—'} unit="" color="#8b5cf6" />
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, unit, color }) {
  return (
    <div style={{
      padding: '12px',
      backgroundColor: '#f9fafb',
      borderRadius: '8px',
      textAlign: 'center',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>{label}</div>
      <div style={{ fontSize: '20px', fontWeight: '700', color }}>{value}{unit}</div>
    </div>
  )
}

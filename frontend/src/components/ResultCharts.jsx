import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

export default function ResultCharts({ result, safetyStock1, safetyStock2 }) {
  if (!result || !result.daily_results || result.daily_results.length === 0) return null

  const outputData = result.daily_results.map(dr => ({
    date: dr.date.slice(5),
    '1-产量': dr.daily_output_1,
    '2-产量': dr.daily_output_2,
    '1-交货': dr.daily_delivery_1,
    '2-交货': dr.daily_delivery_2,
  }))

  const inventoryData = result.daily_results.map(dr => ({
    date: dr.date.slice(5),
    '1-库存': dr.closing_inventory_1,
    '2-库存': dr.closing_inventory_2,
  }))

  const shiftData = result.daily_results.map(dr => ({
    date: dr.date.slice(5),
    '1-工时': dr.work_hours_1,
    '2-工时': dr.work_hours_2,
    is_rest: dr.is_rest,
  }))

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📈 每日产量趋势</h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={outputData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="1-产量" stroke="#2563eb" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="2-产量" stroke="#059669" strokeWidth={2} dot={false} />
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
            <ReferenceLine y={safetyStock1} stroke="#2563eb" strokeDasharray="5 5" label={{ value: '1-安全库存', position: 'right', fontSize: 10, fill: '#2563eb' }} />
            <ReferenceLine y={safetyStock2} stroke="#059669" strokeDasharray="5 5" label={{ value: '2-安全库存', position: 'left', fontSize: 10, fill: '#059669' }} />
            <Line type="monotone" dataKey="1-库存" stroke="#2563eb" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="2-库存" stroke="#059669" strokeWidth={2} dot={false} />
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
            <Bar dataKey="1-工时" stackId="a" fill="#2563eb" radius={[0, 0, 0, 0]} />
            <Bar dataKey="2-工时" stackId="a" fill="#059669" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1f2937' }}>📊 方案统计概览</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <StatCard label="产线运行天数" value={result.total_production_days} unit="天" color="#3b82f6" />
          <StatCard label="休息日占用天数" value={result.rest_days_occupied ?? 0} unit="天" color="#ef4444" />
          <div style={{ gridColumn: '1 / -1', borderTop: '1px solid #e5e7eb', margin: '4px 0' }} />
          <StatCard label="1-生产天数" value={result.total_production_days_1} unit="天" color="#2563eb" />
          <StatCard label="1-休息日生产" value={result.holiday_production_days_1} unit="天" color="#ef4444" />
          <StatCard label="1-库存最小值" value={result.min_inventory_1} unit="" color="#10b981" />
          <StatCard label="1-最终结存" value={result.final_inventory_1 ?? '—'} unit="" color="#8b5cf6" />
          <div style={{ gridColumn: '1 / -1', borderTop: '1px solid #e5e7eb', margin: '4px 0' }} />
          <StatCard label="2-生产天数" value={result.total_production_days_2} unit="天" color="#059669" />
          <StatCard label="2-休息日生产" value={result.holiday_production_days_2} unit="天" color="#ef4444" />
          <StatCard label="2-库存最小值" value={result.min_inventory_2} unit="" color="#10b981" />
          <StatCard label="2-最终结存" value={result.final_inventory_2 ?? '—'} unit="" color="#8b5cf6" />
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
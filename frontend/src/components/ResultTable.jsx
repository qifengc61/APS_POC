export default function ResultTable({ result, onExport }) {
  if (!result || !result.daily_results || result.daily_results.length === 0) return null

  const columns = [
    { key: 'date', label: '日期', p: '7%' },
    { key: 'is_rest', label: '休', p: '4%' },
    { key: 'shift_label_1', label: '1-班次', p: '9%' },
    { key: 'work_hours_1', label: '1-工时', p: '5.5%' },
    { key: 'daily_output_1', label: '1-产量', p: '6%' },
    { key: 'daily_delivery_1', label: '1-交货', p: '6%' },
    { key: 'closing_inventory_1', label: '1-库存', p: '7%' },
    { key: 'inventory_violation_1', label: '1-异常', p: '5%' },
    { key: 'shift_label_2', label: '2-班次', p: '9%' },
    { key: 'work_hours_2', label: '2-工时', p: '5.5%' },
    { key: 'daily_output_2', label: '2-产量', p: '6%' },
    { key: 'daily_delivery_2', label: '2-交货', p: '6%' },
    { key: 'closing_inventory_2', label: '2-库存', p: '7%' },
    { key: 'inventory_violation_2', label: '2-异常', p: '5%' },
    { key: 'total_work_hours', label: '总工时', p: '7%' },
  ]

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const parts = dateStr.split('-')
    if (parts.length === 3) return `${parts[1]}-${parts[2]}`
    return dateStr
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px 12px', borderBottom: '2px solid #3b82f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>📋 排产结果明细</h3>
        {onExport && (
          <button onClick={onExport} style={{
            padding: '6px 14px', backgroundColor: '#059669', color: '#fff',
            border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontSize: '13px', fontWeight: '600', whiteSpace: 'nowrap',
          }}>
            📥 导出 Excel
          </button>
        )}
      </div>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        <table style={{ width: '100%', tableLayout: 'fixed', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key} style={{
                  padding: '7px 4px', backgroundColor: '#f8fafc',
                  borderBottom: '2px solid #e2e8f0', textAlign: 'center',
                  fontWeight: '600', color: '#475569',
                  position: 'sticky', top: 0, zIndex: 1,
                  width: col.p, whiteSpace: 'nowrap',
                }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.daily_results.map((row, idx) => {
              const vio1 = row.inventory_violation_1
              const vio2 = row.inventory_violation_2
              const isRest = row.is_rest
              const bgColor = vio1 || vio2 ? '#fef2f2' : isRest ? '#fff1f2' : ''
              return (
                <tr key={idx} style={{ backgroundColor: bgColor, borderBottom: '1px solid #f1f5f9' }}>
                  {columns.map(col => {
                    let val = row[col.key]
                    let color = '#374151'
                    let fontWeight = 'normal'
                    if (col.key === 'date') {
                      val = formatDate(val)
                    } else if (col.key === 'is_rest') {
                      val = isRest ? '🔴' : '\u2014'
                    } else if (col.key === 'inventory_violation_1') {
                      val = vio1 ? '⚠️' : '✅'
                      if (vio1) color = '#dc2626'
                    } else if (col.key === 'inventory_violation_2') {
                      val = vio2 ? '⚠️' : '✅'
                      if (vio2) color = '#dc2626'
                    } else if (col.key === 'shift_label_1' || col.key === 'shift_label_2') {
                      const prefix = col.key === 'shift_label_1' ? '1' : '2'
                      const combo = row['combo_' + prefix]
                      if (isRest && combo > 0) {
                        color = '#dc2626'
                        fontWeight = '600'
                      }
                    }
                    return (
                      <td key={col.key} style={{
                        padding: '5px 4px', textAlign: 'center',
                        color, fontWeight, whiteSpace: 'nowrap',
                        overflow: 'hidden', textOverflow: 'ellipsis',
                      }}>
                        {val}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

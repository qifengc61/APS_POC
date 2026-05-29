const MATERIAL_COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']

export default function ResultTable({ result, onExport, activeProductIdx = 0 }) {
  if (!result || !result.daily_results || result.daily_results.length === 0) return null

  const pidx = activeProductIdx + 1
  const color = MATERIAL_COLORS[activeProductIdx % MATERIAL_COLORS.length]

  const columns = [
    { key: 'date', label: '日期', p: '8%' },
    { key: 'is_rest', label: '休', p: '4%' },
    { key: `shift_label_${pidx}`, label: `${pidx}-班次`, p: '10%', color },
    { key: `work_hours_${pidx}`, label: `${pidx}-工时`, p: '6%', color },
    { key: `daily_output_${pidx}`, label: `${pidx}-产量`, p: '6%', color },
    { key: `daily_delivery_${pidx}`, label: `${pidx}-交货`, p: '6%', color },
    { key: `closing_inventory_${pidx}`, label: `${pidx}-库存`, p: '7%', color },
    { key: `inventory_violation_${pidx}`, label: `${pidx}-异常`, p: '5%', color },
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
      <div style={{ padding: '16px 20px 12px', borderBottom: `2px solid ${color}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
                  fontWeight: '600', color: col.color || '#475569',
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
              const vioKey = `inventory_violation_${pidx}`
              const vio = row[vioKey]
              const isRest = row.is_rest
              const bgColor = vio ? '#fef2f2' : isRest ? '#fff1f2' : ''
              return (
                <tr key={idx} style={{ backgroundColor: bgColor, borderBottom: '1px solid #f1f5f9' }}>
                  {columns.map(col => {
                    let val = row[col.key]
                    let textColor = '#374151'
                    let fontWeight = 'normal'
                    if (col.key === 'date') {
                      val = formatDate(val)
                    } else if (col.key === 'is_rest') {
                      val = isRest ? '🔴' : '\u2014'
                    } else if (col.key === vioKey) {
                      val = vio ? '⚠️' : '✅'
                      if (vio) textColor = '#dc2626'
                    } else if (col.key === `shift_label_${pidx}`) {
                      const comboKey = `combo_${pidx}`
                      const combo = row[comboKey]
                      if (isRest && combo > 0) {
                        textColor = '#dc2626'
                        fontWeight = '600'
                      }
                    }
                    return (
                      <td key={col.key} style={{
                        padding: '5px 4px', textAlign: 'center',
                        color: textColor, fontWeight, whiteSpace: 'nowrap',
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

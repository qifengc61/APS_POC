export default function ResultTable({ result }) {
  if (!result || !result.daily_results || result.daily_results.length === 0) return null

  const columns = [
    { key: 'date', label: '日期', width: '110px' },
    { key: 'is_rest', label: '休息日', width: '70px' },
    { key: 'shift_label', label: '班次安排', width: '120px' },
    { key: 'prod_label', label: '产量构成', width: '100px' },
    { key: 'work_hours', label: '工时(h)', width: '75px' },
    { key: 'daily_output', label: '当日产量', width: '85px' },
    { key: 'daily_delivery', label: '交货量', width: '85px' },
    { key: 'closing_inventory', label: '结存库存', width: '85px' },
    { key: 'inventory_violation', label: '库存异常', width: '75px' },
  ]

  const renderCell = (key, row) => {
    switch (key) {
      case 'is_rest':
        if (row.is_rest) return '🔴'
        return '—'
      case 'shift_label':
        return row[key]
      case 'prod_label':
        return row[key]
      case 'inventory_violation':
        return row[key] ? '⚠️ 异常' : '✅'
      default:
        return row[key]
    }
  }

  const getRowStyle = (row) => {
    if (row.inventory_violation) return { backgroundColor: '#fef2f2' }
    if (row.is_rest) return { backgroundColor: '#fff1f2' }
    return {}
  }

  const getShiftLabelStyle = (row) => {
    if (row.is_holiday && row.combo === 0) return { color: '#1f2937' }
    if (row.is_rest && !row.is_holiday && row.combo === 0) return { color: '#1f2937' }
    if (row.is_rest && row.combo > 0) return { color: '#dc2626', fontWeight: '600' }
    if (row.combo >= 4) return { color: '#dc2626', fontWeight: '600' }
    if (row.shift1 === 0.5 || row.shift2 === 0.5 || row.shift2 === 0) return { color: '#059669' }
    return { color: '#2563eb' }
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb', overflow: 'hidden', marginTop: '16px' }}>
      <h3 style={{ margin: 0, padding: '16px 20px 12px', fontSize: '16px', color: '#1f2937', borderBottom: '2px solid #3b82f6' }}>
        📋 排产结果明细
      </h3>
      <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: '#f8fafc',
                    borderBottom: '2px solid #e2e8f0',
                    textAlign: 'center',
                    fontWeight: '600',
                    color: '#475569',
                    position: 'sticky',
                    top: 0,
                    zIndex: 1,
                    minWidth: col.width,
                  }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.daily_results.map((row, idx) => (
              <tr key={idx} style={{ ...getRowStyle(row), borderBottom: '1px solid #f1f5f9' }}>
                {columns.map(col => (
                  <td
                    key={col.key}
                    style={{
                      padding: '8px 12px',
                      textAlign: 'center',
                      color: col.key === 'inventory_violation' && row[col.key] ? '#dc2626' : '#374151',
                      ...(col.key === 'shift_label' ? getShiftLabelStyle(row) : {}),
                    }}
                  >
                    {renderCell(col.key, row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import { useRef, useEffect, useState } from 'react'
import dayjs from 'dayjs'

const ORDER_COLORS = [
  '#1890ff', '#52c41a', '#fa8c16', '#722ed1', '#eb2f96',
  '#13c2c2', '#f5222d', '#2f54eb', '#a0d911', '#faad14',
]

function isWeekend(day) {
  const dow = day.day()
  return dow === 0 || dow === 6
}

function buildWorkDaySegments(task, minTime, dayWidth) {
  const start = dayjs(task.start_time)
  const end = dayjs(task.end_time)
  const segments = []

  let current = start.startOf('day')
  const lastDay = end.startOf('day')

  while (current.diff(lastDay, 'day') <= 0) {
    if (!isWeekend(current)) {
      const dayStart = current.isSame(start, 'day') ? start : current
      const dayEnd = current.isSame(end, 'day') ? end : current.endOf('day')
      if (dayStart.isBefore(dayEnd)) {
        const left = dayStart.diff(minTime, 'minute') / (24 * 60) * dayWidth
        const width = dayEnd.diff(dayStart, 'minute') / (24 * 60) * dayWidth
        if (width > 1) {
          segments.push({ left: Math.round(left * 100) / 100, width: Math.round(width * 100) / 100, day: current })
        }
      }
    }
    current = current.add(1, 'day')
  }

  return segments
}

export default function SimpleGantt({ data }) {
  const containerRef = useRef(null)
  const [containerWidth, setContainerWidth] = useState(0)

  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth)
      }
    }
    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  if (!data || !data.resources || data.resources.length === 0) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>暂无甘特图数据</div>
  }

  const allTasks = data.resources.flatMap(r => r.tasks || [])
  if (allTasks.length === 0) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>暂无甘特图数据</div>
  }

  const allStartTimes = allTasks.map(t => dayjs(t.start_time))
  const allEndTimes = allTasks.map(t => dayjs(t.end_time))
  const minTime = allStartTimes.reduce((a, b) => a.isBefore(b) ? a : b).startOf('day')
  const maxTime = allEndTimes.reduce((a, b) => a.isAfter(b) ? a : b).endOf('day')
  const totalDays = maxTime.diff(minTime, 'day') + 1

  const leftWidth = 140
  const chartWidth = Math.max(containerWidth - leftWidth, totalDays * 60)
  const dayWidth = chartWidth / totalDays
  const rowHeight = 40

  const days = []
  for (let i = 0; i < totalDays; i++) {
    days.push(minTime.add(i, 'day'))
  }

  const orderColorMap = {}
  let orderColorIndex = 0
  allTasks.forEach(t => {
    const key = t.order_code || t.order_id || 'unknown'
    if (!orderColorMap[key]) {
      orderColorMap[key] = ORDER_COLORS[orderColorIndex % ORDER_COLORS.length]
      orderColorIndex++
    }
  })

  return (
    <div ref={containerRef} style={{ width: '100%', overflowX: 'auto' }}>
      <div style={{ minWidth: leftWidth + chartWidth }}>
        <div style={{ display: 'flex', height: 36, borderBottom: '1px solid #e8e8e8', background: '#fafafa' }}>
          <div style={{ width: leftWidth, minWidth: leftWidth, padding: '0 12px', lineHeight: '36px', fontWeight: 500, borderRight: '1px solid #e8e8e8' }}>
            资源
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            {days.map((day, i) => (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: i * dayWidth,
                  width: dayWidth,
                  height: '100%',
                  textAlign: 'center',
                  lineHeight: '36px',
                  fontSize: 12,
                  color: isWeekend(day) ? '#bfbfbf' : '#666',
                  borderRight: '1px solid #f0f0f0',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap',
                }}
              >
                {day.format('MM/DD')}
              </div>
            ))}
          </div>
        </div>
        {data.resources.map((resource, ri) => (
          <div key={resource.id} style={{ display: 'flex', height: rowHeight, borderBottom: '1px solid #e8e8e8' }}>
            <div style={{
              width: leftWidth,
              minWidth: leftWidth,
              padding: '0 12px',
              lineHeight: `${rowHeight}px`,
              fontWeight: 500,
              borderRight: '1px solid #e8e8e8',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              background: ri % 2 === 0 ? '#fff' : '#fafafa',
            }}>
              {resource.name}
            </div>
            <div style={{ flex: 1, position: 'relative', background: ri % 2 === 0 ? '#fff' : '#fafafa' }}>
              {days.map((day, i) => (
                <div
                  key={i}
                  style={{
                    position: 'absolute',
                    left: i * dayWidth,
                    top: 0,
                    width: dayWidth,
                    height: '100%',
                    borderRight: '1px solid #f5f5f5',
                    background: isWeekend(day) ? 'rgba(0,0,0,0.06)' : 'transparent',
                  }}
                />
              ))}
              {(resource.tasks || []).map((task, ti) => {
                const orderKey = task.order_code || task.order_id || 'unknown'
                const taskColor = orderColorMap[orderKey] || '#1890ff'
                const segments = buildWorkDaySegments(task, minTime, dayWidth)

                return segments.map((seg, si) => {
                    const prevIsWeekend = isWeekend(seg.day.subtract(1, 'day'))
                    const nextIsWeekend = isWeekend(seg.day.add(1, 'day'))
                    const isFirst = si === 0
                    const isLast = si === segments.length - 1
                    const rLeft = isFirst || prevIsWeekend ? '4px' : '0'
                    const rRight = isLast || nextIsWeekend ? '4px' : '0'

                    return (
                      <div
                        key={`${ti}-${si}`}
                        style={{
                          position: 'absolute',
                          left: seg.left,
                          top: 6,
                          width: seg.width,
                          height: rowHeight - 12,
                          background: taskColor,
                          borderRadius: `${rLeft} ${rRight} ${rRight} ${rLeft}`,
                          cursor: 'pointer',
                        }}
                        title={`${task.order_code || '-'} | ${task.process_code} | ${seg.day.format('MM/DD')}: ${task.start_time} ~ ${task.end_time}`}
                      />
                    )
                  })
              })}
            </div>
          </div>
        ))}
        <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: '8px 16px', padding: '0 12px' }}>
          {Object.entries(orderColorMap).map(([orderKey, color]) => (
            <div key={orderKey} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: color }} />
              <span style={{ fontSize: 12, color: '#555' }}>{orderKey}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

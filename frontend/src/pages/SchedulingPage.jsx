import { useState, useEffect, useRef } from 'react'
import { Card, Steps, Progress, Timeline, Table, Tabs, Button, Select, DatePicker, message, Modal } from 'antd'
import { orderApi, smartSchedulingApi } from '../api/api'
import SimpleGantt from '../components/SimpleGantt'
import dayjs from 'dayjs'

const PHASE_TRIGGER = 0
const PHASE_PROGRESS = 1
const PHASE_RESULT = 2

const statusMap = {
  SCHEDULED: '已排产',
  PENDING: '待排产',
  IN_PROGRESS: '进行中',
  COMPLETED: '已完成',
  DELAYED: '已延期',
}

export default function SchedulingPage() {
  const [phase, setPhase] = useState(PHASE_TRIGGER)
  const [orders, setOrders] = useState([])
  const [selectedOrders, setSelectedOrders] = useState([])
  const [startDate, setStartDate] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [taskId, setTaskId] = useState(null)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [logs, setLogs] = useState([])
  const [progressStatus, setProgressStatus] = useState('')
  const [taskData, setTaskData] = useState([])
  const [taskPagination, setTaskPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [taskLoading, setTaskLoading] = useState(false)
  const [ganttData, setGanttData] = useState({ resources: [] })
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [confirmModalOpen, setConfirmModalOpen] = useState(false)
  const [cancelModalOpen, setCancelModalOpen] = useState(false)
  const pollRef = useRef(null)

  const phaseRef = useRef(phase)
  phaseRef.current = phase

  useEffect(() => {
    fetchOrders()
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      if (phaseRef.current === PHASE_RESULT) {
        smartSchedulingApi.cancel().catch(() => {})
      }
    }
  }, [])

  const fetchOrders = async () => {
    try {
      const res = await orderApi.list({ page: 1, page_size: 1000 })
      const items = res.items || res.data || []
      setOrders(items)
    } catch {
      message.error('获取订单列表失败')
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const payload = {}
      if (selectedOrders.length > 0) {
        payload.order_ids = selectedOrders
      }
      if (startDate) {
        payload.start_date = startDate.format('YYYY-MM-DD')
      }
      const res = await smartSchedulingApi.generate(payload)
      const id = res.data?.task_id || res.data?.id || res.task_id || res.id
      setTaskId(id)
      setProgress(0)
      setCurrentStep('排产任务已提交')
      setLogs([{ time: dayjs().format('HH:mm:ss'), text: '排产任务已提交' }])
      setProgressStatus('active')
      setPhase(PHASE_PROGRESS)
      startPolling(id)
    } catch {
      message.error('触发排产失败')
    } finally {
      setGenerating(false)
    }
  }

  const startPolling = (id) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const res = await smartSchedulingApi.getProgress(id)
        const data = res.data || res
        const pct = typeof data.progress === 'number' ? data.progress : 0
        const step = data.current_step || data.step || ''
        const status = data.status || ''
        const newLogs = data.logs || []

        setProgress(pct)
        setCurrentStep(step)
        setProgressStatus(status === 'FAILED' ? 'exception' : 'active')

        if (newLogs.length > 0) {
          setLogs(newLogs.map(l => ({
            time: l.time || l.timestamp || dayjs().format('HH:mm:ss'),
            text: l.message || l.text || l,
          })))
        } else if (step) {
          setLogs(prev => [...prev, { time: dayjs().format('HH:mm:ss'), text: step }])
        }

        if (status === 'SUCCESS') {
          clearInterval(pollRef.current)
          pollRef.current = null
          setProgress(100)
          setProgressStatus('success')
          message.success('排产完成')
          setTimeout(() => {
            setPhase(PHASE_RESULT)
            fetchTaskData(1, 10)
            fetchGanttData()
          }, 500)
        } else if (status === 'FAILED') {
          clearInterval(pollRef.current)
          pollRef.current = null
          setProgressStatus('exception')
          message.error('排产失败: ' + (data.error || data.message || '未知错误'))
        }
      } catch {
        message.error('获取进度失败')
      }
    }, 2000)
  }

  const fetchTaskData = async (page = 1, pageSize = 10) => {
    setTaskLoading(true)
    try {
      const res = await smartSchedulingApi.previewTasks({ page, page_size: pageSize })
      const data = res.data || res
      setTaskData(data.items || data.data || data || [])
      setTaskPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: data.total || (data.items || data.data || []).length,
      }))
    } catch {
      message.error('获取任务列表失败')
    } finally {
      setTaskLoading(false)
    }
  }

  const fetchGanttData = async () => {
    try {
      const res = await smartSchedulingApi.previewGantt()
      const data = res.data || res
      setGanttData(data)
    } catch {
      message.error('获取甘特图数据失败')
    }
  }

  const handleConfirm = () => {
    setConfirmModalOpen(true)
  }

  const handleConfirmOk = async () => {
    setConfirmLoading(true)
    setConfirmModalOpen(false)
    try {
      await smartSchedulingApi.confirm()
      message.success('计划已确认')
      resetState()
    } catch {
      message.error('确认计划失败')
    } finally {
      setConfirmLoading(false)
    }
  }

  const handleCancel = () => {
    setCancelModalOpen(true)
  }

  const handleCancelOk = async () => {
    setConfirmLoading(true)
    setCancelModalOpen(false)
    try {
      await smartSchedulingApi.cancel()
      message.success('计划已放弃')
      resetState()
    } catch {
      message.error('放弃计划失败')
    } finally {
      setConfirmLoading(false)
    }
  }

  const resetState = () => {
    setPhase(PHASE_TRIGGER)
    setTaskId(null)
    setProgress(0)
    setCurrentStep('')
    setLogs([])
    setProgressStatus('')
    setTaskData([])
    setGanttData({ resources: [] })
    setSelectedOrders([])
    setStartDate(null)
  }

  const taskColumns = [
    { title: '任务编码', dataIndex: 'task_code', key: 'task_code', render: (v, r) => v || r.code },
    { title: '工序编码', dataIndex: 'process_code', key: 'process_code' },
    { title: '分配资源', dataIndex: 'resource_name', key: 'resource_name' },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: v => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      render: v => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '持续时长',
      key: 'duration',
      render: (_, r) => {
        if (!r.start_time || !r.end_time) return '-'
        const mins = dayjs(r.end_time).diff(dayjs(r.start_time), 'minute')
        if (mins < 60) return `${mins}分钟`
        const h = Math.floor(mins / 60)
        const m = mins % 60
        return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: v => statusMap[v] || v || '-',
    },
  ]

  const stepsItems = [
    { title: '触发排产' },
    { title: '排产进度' },
    { title: '结果预览' },
  ]

  return (
    <div>
      <Card>
        <Steps current={phase} items={stepsItems} style={{ marginBottom: 32 }} />

        {phase === PHASE_TRIGGER && (
          <div style={{ maxWidth: 600 }}>
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 8, fontWeight: 500 }}>选择订单（可选）</div>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="不选则排产所有可排产订单"
                value={selectedOrders}
                onChange={setSelectedOrders}
                options={orders.map(o => ({ value: o.id, label: o.order_code || o.code || o.name }))}
              />
            </div>
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 8, fontWeight: 500 }}>排产开始日期（可选）</div>
              <DatePicker
                style={{ width: '100%' }}
                placeholder="不选则从下一完整工作日开始"
                value={startDate}
                onChange={setStartDate}
                disabledDate={d => d.day() === 0 || d.day() === 6}
              />
            </div>
            <Button type="primary" size="large" loading={generating} onClick={handleGenerate}>
              开始排产
            </Button>
          </div>
        )}

        {phase === PHASE_PROGRESS && (
          <div style={{ maxWidth: 700 }}>
            <Progress
              percent={progress}
              status={progressStatus}
              style={{ marginBottom: 24 }}
            />
            {currentStep && (
              <div style={{ marginBottom: 24, fontSize: 16 }}>
                当前步骤: {currentStep}
              </div>
            )}
            <div style={{ marginBottom: 8, fontWeight: 500 }}>执行日志</div>
            <Timeline
              items={logs.map((log, i) => ({
                children: (
                  <span>
                    <span style={{ color: '#999', marginRight: 8 }}>{log.time}</span>
                    {log.text}
                  </span>
                ),
              }))}
            />
          </div>
        )}

        {phase === PHASE_RESULT && (
          <div>
            <Tabs
              items={[
                {
                  key: 'tasks',
                  label: '任务列表',
                  children: (
                    <Table
                      rowKey={(r, i) => r.task_code || r.id || i}
                      columns={taskColumns}
                      dataSource={taskData}
                      loading={taskLoading}
                      pagination={{
                        ...taskPagination,
                        showSizeChanger: true,
                        showTotal: total => `共 ${total} 条`,
                        onChange: (page, pageSize) => fetchTaskData(page, pageSize),
                      }}
                    />
                  ),
                },
                {
                  key: 'gantt',
                  label: '甘特图',
                  children: <SimpleGantt data={ganttData} />,
                },
              ]}
            />
            <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
              <Button type="primary" style={{ background: '#52c41a' }} loading={confirmLoading} onClick={handleConfirm}>
                确认计划
              </Button>
              <Button danger loading={confirmLoading} onClick={handleCancel}>
                放弃计划
              </Button>
            </div>
          </div>
        )}

      </Card>
      <Modal
        title="确认计划"
        open={confirmModalOpen}
        onOk={handleConfirmOk}
        onCancel={() => setConfirmModalOpen(false)}
        okText="确认"
        cancelText="取消"
        confirmLoading={confirmLoading}
      >
        确认后将正式生效此排产计划，是否继续？
      </Modal>
      <Modal
        title="放弃计划"
        open={cancelModalOpen}
        onOk={handleCancelOk}
        onCancel={() => setCancelModalOpen(false)}
        okText="放弃"
        cancelText="取消"
        okButtonProps={{ danger: true }}
        confirmLoading={confirmLoading}
      >
        放弃后将丢弃此排产计划，是否继续？
      </Modal>
    </div>
  )
}

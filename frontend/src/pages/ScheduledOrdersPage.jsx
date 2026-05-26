import { useState, useEffect } from 'react'
import { Card, Tabs, Table, Button, Modal, message } from 'antd'
import { orderApi, smartSchedulingApi } from '../api/api'
import SimpleGantt from '../components/SimpleGantt'
import dayjs from 'dayjs'

const statusMap = {
  SCHEDULED: '已排产',
  PENDING: '待排产',
  IN_PROGRESS: '进行中',
  COMPLETED: '已完成',
  DELAYED: '已延期',
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

export default function ScheduledOrdersPage() {
  const [scheduledCount, setScheduledCount] = useState(0)
  const [taskData, setTaskData] = useState([])
  const [taskPagination, setTaskPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [taskLoading, setTaskLoading] = useState(false)
  const [ganttData, setGanttData] = useState({ resources: [] })
  const [clearLoading, setClearLoading] = useState(false)
  const [clearModalOpen, setClearModalOpen] = useState(false)

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    fetchConfirmedTasks(1, 10)
    fetchConfirmedGantt()
    fetchScheduledCount()
  }

  const fetchScheduledCount = async () => {
    try {
      const res = await orderApi.list({ page: 1, page_size: 1000 })
      const items = (res.items || res.data || []).filter(o => o.scheduling_status === 'SCHEDULED')
      setScheduledCount(items.length)
    } catch {
      // silent
    }
  }

  const fetchConfirmedTasks = async (page = 1, pageSize = 10) => {
    setTaskLoading(true)
    try {
      const data = await smartSchedulingApi.getTasks({ page, page_size: pageSize })
      setTaskData(data.items || [])
      setTaskPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: data.total || 0,
      }))
    } catch {
      message.error('获取排产任务列表失败')
    } finally {
      setTaskLoading(false)
    }
  }

  const fetchConfirmedGantt = async () => {
    try {
      const data = await smartSchedulingApi.getGantt()
      setGanttData(data)
    } catch {
      message.error('获取甘特图数据失败')
    }
  }

  const handleClearPlan = async () => {
    setClearLoading(true)
    try {
      await smartSchedulingApi.clearPlan()
      message.success('所有排产结果已清空，订单恢复为未排产状态')
      setTaskData([])
      setGanttData({ resources: [] })
      setScheduledCount(0)
      setTaskPagination({ current: 1, pageSize: 10, total: 0 })
    } catch {
      message.error('清空失败')
    } finally {
      setClearLoading(false)
      setClearModalOpen(false)
    }
  }

  return (
    <div>
      <Card
        title="排产结果"
        extra={
          <Button
            danger
            loading={clearLoading}
            disabled={scheduledCount === 0}
            onClick={() => setClearModalOpen(true)}
          >
            一键清空
          </Button>
        }
      >
        {scheduledCount === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            暂无已排产结果，请先在作业排产中触发排产并确认计划
          </div>
        ) : (
          <Tabs
            items={[
              {
                key: 'tasks',
                label: `任务列表 (${taskPagination.total})`,
                children: (
                  <Table
                    rowKey={(r, i) => r.code || r.id || i}
                    columns={taskColumns}
                    dataSource={taskData}
                    loading={taskLoading}
                    pagination={{
                      ...taskPagination,
                      showSizeChanger: true,
                      showTotal: total => `共 ${total} 条`,
                      onChange: (page, pageSize) => fetchConfirmedTasks(page, pageSize),
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
        )}
      </Card>
      <Modal
        title="清空排产结果"
        open={clearModalOpen}
        onOk={handleClearPlan}
        onCancel={() => setClearModalOpen(false)}
        okText="确认清空"
        cancelText="取消"
        okButtonProps={{ danger: true }}
        confirmLoading={clearLoading}
      >
        将清空所有已确认的排产结果，并将所有订单状态恢复为"未排产"。此操作不可撤销，是否继续？
      </Modal>
    </div>
  )
}

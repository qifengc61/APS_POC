import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm, Tabs, Checkbox, TimePicker } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, MinusCircleOutlined } from '@ant-design/icons'
import { calendarApi, resourceApi } from '../api/api'
import dayjs from 'dayjs'

const dayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function WorkPatternTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await calendarApi.list({ page, page_size: pageSize, type: 'work_pattern' })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取工作模式列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const handleAdd = () => {
    setEditingRecord(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record) => {
    setEditingRecord(record)
    form.setFieldsValue({
      ...record,
      time_periods: (record.time_periods || []).map(tp => ({
        start: tp.start ? dayjs(tp.start, 'HH:mm') : null,
        end: tp.end ? dayjs(tp.end, 'HH:mm') : null,
      })),
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await calendarApi.delete(id, 'work_pattern')
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = { ...values, type: 'work_pattern' }
      if (submitData.time_periods && Array.isArray(submitData.time_periods)) {
        submitData.time_periods = submitData.time_periods.map(tp => ({
          start: tp.start ? tp.start.format('HH:mm') : '',
          end: tp.end ? tp.end.format('HH:mm') : '',
        }))
      }
      if (editingRecord) {
        await calendarApi.update(editingRecord.id, submitData)
        message.success('更新成功')
      } else {
        await calendarApi.create(submitData)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '时间段',
      dataIndex: 'time_periods',
      key: 'time_periods',
      render: v => (v || []).map(tp => `${tp.start}-${tp.end}`).join('、') || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增工作模式</Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
        pagination={{ ...pagination, showSizeChanger: true, showTotal: total => `共 ${total} 条`, onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />
      <Modal title={editingRecord ? '编辑工作模式' : '新增工作模式'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} destroyOnClose width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="时间段">
            <Form.List name="time_periods">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item {...restField} name={[name, 'start']} rules={[{ required: true, message: '请选择' }]} style={{ marginBottom: 0 }}>
                        <TimePicker format="HH:mm" placeholder="开始时间" />
                      </Form.Item>
                      <span>—</span>
                      <Form.Item {...restField} name={[name, 'end']} rules={[{ required: true, message: '请选择' }]} style={{ marginBottom: 0 }}>
                        <TimePicker format="HH:mm" placeholder="结束时间" />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} style={{ color: '#ff4d4f' }} />
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加时间段</Button>
                </>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function WorkCalendarTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [workPatterns, setWorkPatterns] = useState([])
  const [resources, setResources] = useState([])
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await calendarApi.list({ page, page_size: pageSize, type: 'work_calendar' })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取工作日历列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchWorkPatterns = async () => {
    try {
      const res = await calendarApi.list({ page: 1, page_size: 1000, type: 'work_pattern' })
      setWorkPatterns(res.items || res.data || [])
    } catch {}
  }

  const fetchResources = async () => {
    try {
      const res = await resourceApi.list({ page: 1, page_size: 1000 })
      setResources(res.items || res.data || [])
    } catch {}
  }

  useEffect(() => { fetchData(); fetchWorkPatterns(); fetchResources() }, [])

  const handleAdd = () => {
    setEditingRecord(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record) => {
    setEditingRecord(record)
    const workDaysArr = typeof record.work_days === 'string'
      ? record.work_days.split('').reduce((arr, ch, i) => { if (ch === '1') arr.push(i); return arr }, [])
      : (record.work_days || [])
    form.setFieldsValue({
      name: record.name,
      work_mode_id: record.work_mode_id,
      work_days: workDaysArr,
      resource_ids: record.resource_ids || [],
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await calendarApi.delete(id, 'work_calendar')
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const workDaysBitmap = Array.from({ length: 7 }, (_, i) =>
        (values.work_days || []).includes(i) ? '1' : '0'
      ).join('')
      const submitData = {
        ...values,
        type: 'work_calendar',
        work_days: workDaysBitmap,
      }
      if (editingRecord) {
        await calendarApi.update(editingRecord.id, submitData)
        message.success('更新成功')
      } else {
        await calendarApi.create(submitData)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '工作日',
      dataIndex: 'work_days',
      key: 'work_days',
      render: v => {
        if (!v) return '-'
        const arr = Array.isArray(v) ? v : String(v).split('').map((ch, i) => ch === '1' ? i : -1).filter(i => i >= 0)
        return arr.map(d => dayLabels[d]).join('、') || '-'
      },
    },
    {
      title: '关联工作模式',
      dataIndex: 'work_mode_id',
      key: 'work_mode_id',
      render: v => {
        const wp = workPatterns.find(p => p.id === v)
        return wp ? wp.name : v || '-'
      },
    },
    {
      title: '可用资源',
      dataIndex: 'resource_ids',
      key: 'resource_ids',
      render: v => {
        if (!v || !v.length) return '-'
        return v.map(rid => {
          const r = resources.find(item => item.id === rid)
          return r ? r.code : rid
        }).join('、')
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增工作日历</Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
        pagination={{ ...pagination, showSizeChanger: true, showTotal: total => `共 ${total} 条`, onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />
      <Modal title={editingRecord ? '编辑工作日历' : '新增工作日历'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} destroyOnClose width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="work_days" label="工作日">
            <Checkbox.Group>
              {dayLabels.map((label, idx) => (
                <Checkbox key={idx} value={idx}>{label}</Checkbox>
              ))}
            </Checkbox.Group>
          </Form.Item>
          <Form.Item name="work_mode_id" label="关联工作模式">
            <Select allowClear placeholder="请选择工作模式" options={workPatterns.map(wp => ({ value: wp.id, label: wp.name }))} />
          </Form.Item>
          <Form.Item name="resource_ids" label="可用资源">
            <Select
              mode="multiple"
              showSearch
              optionFilterProp="label"
              placeholder="选择可使用此日历的资源"
              options={resources.map(r => ({
                value: r.id,
                label: `${r.code} - ${r.name}`,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default function CalendarPage() {
  const items = [
    { key: 'work_pattern', label: '工作模式', children: <WorkPatternTab /> },
    { key: 'work_calendar', label: '工作日历', children: <WorkCalendarTab /> },
  ]

  return <Tabs items={items} />
}

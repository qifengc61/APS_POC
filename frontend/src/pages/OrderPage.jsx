import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm, Switch, DatePicker } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import { orderApi, materialApi } from '../api/api'
import dayjs from 'dayjs'

const orderStatusOptions = [
  { value: 'PENDING', label: '待处理' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'CANCELLED', label: '已取消' },
]

const schedulingStatusOptions = [
  { value: 'UNSCHEDULED', label: '未排' },
  { value: 'SCHEDULED', label: '已排' },
  { value: 'COMPLETED', label: '完成' },
  { value: 'NO_SCHEDULED', label: '不排' },
]

const orderStatusMap = Object.fromEntries(orderStatusOptions.map(o => [o.value, o.label]))
const schedulingStatusMap = Object.fromEntries(schedulingStatusOptions.map(o => [o.value, o.label]))

export default function OrderPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({ order_status: undefined, scheduling_status: undefined, material_code: undefined })
  const [materials, setMaterials] = useState([])
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (filters.order_status) params.order_status = filters.order_status
      if (filters.scheduling_status) params.scheduling_status = filters.scheduling_status
      if (filters.material_code) params.material_code = filters.material_code
      const res = await orderApi.list(params)
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取订单列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchMaterials = async () => {
    try {
      const res = await materialApi.list({ page: 1, page_size: 1000 })
      setMaterials(res.items || res.data || [])
    } catch {}
  }

  useEffect(() => {
    fetchData()
    fetchMaterials()
  }, [])

  const handleAdd = () => {
    setEditingRecord(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record) => {
    setEditingRecord(record)
    form.setFieldsValue({
      ...record,
      delivery_time: record.delivery_time ? dayjs(record.delivery_time) : undefined,
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await orderApi.delete(id)
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (values.delivery_time) {
        values.delivery_time = values.delivery_time.format('YYYY-MM-DD HH:mm:ss')
      }
      if (editingRecord) {
        await orderApi.update(editingRecord.id, values)
        message.success('更新成功')
      } else {
        await orderApi.create(values)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const handleCanScheduleChange = async (checked, record) => {
    try {
      await orderApi.toggleCanSchedule(record.id, { can_schedule: checked })
      message.success('更新成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('更新失败')
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleSearch = () => {
    fetchData(1, pagination.pageSize)
  }

  const handleReset = () => {
    setFilters({ order_status: undefined, scheduling_status: undefined, material_code: undefined })
    setPagination(prev => ({ ...prev, current: 1 }))
    setTimeout(() => fetchData(1, pagination.pageSize), 0)
  }

  const columns = [
    { title: '编码', dataIndex: 'code', key: 'code' },
    {
      title: '物料',
      dataIndex: 'material_code',
      key: 'material_code',
      render: v => {
        const m = materials.find(item => item.code === v)
        return m ? `${m.code} - ${m.name}` : v
      },
    },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '交付期限', dataIndex: 'delivery_time', key: 'delivery_time' },
    { title: '优先级', dataIndex: 'priority', key: 'priority' },
    { title: '排序', dataIndex: 'sequence', key: 'sequence' },
    { title: '订单状态', dataIndex: 'order_status', key: 'order_status', render: v => orderStatusMap[v] || v },
    { title: '排产状态', dataIndex: 'scheduling_status', key: 'scheduling_status', render: v => schedulingStatusMap[v] || v },
    {
      title: '参与排产',
      dataIndex: 'can_schedule',
      key: 'can_schedule',
      render: (v, record) => (
        <Switch checked={v} onChange={checked => handleCanScheduleChange(checked, record)} />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该订单吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          placeholder="订单状态"
          allowClear
          style={{ width: 140 }}
          value={filters.order_status}
          onChange={v => handleFilterChange('order_status', v)}
          options={orderStatusOptions}
        />
        <Select
          placeholder="排产状态"
          allowClear
          style={{ width: 140 }}
          value={filters.scheduling_status}
          onChange={v => handleFilterChange('scheduling_status', v)}
          options={schedulingStatusOptions}
        />
        <Select
          placeholder="物料"
          allowClear
          showSearch
          optionFilterProp="label"
          style={{ width: 200 }}
          value={filters.material_code}
          onChange={v => handleFilterChange('material_code', v)}
          options={materials.map(m => ({ value: m.code, label: `${m.code} - ${m.name}` }))}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>查询</Button>
        <Button onClick={handleReset}>重置</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增订单</Button>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showTotal: total => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize),
        }}
      />
      <Modal
        title={editingRecord ? '编辑订单' : '新增订单'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="code" label="编码" rules={[{ required: true, message: '请输入编码' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="material_code" label="物料" rules={[{ required: true, message: '请选择物料' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="请选择物料"
              options={materials.map(m => ({ value: m.code, label: `${m.code} - ${m.name}` }))}
            />
          </Form.Item>
          <Form.Item name="quantity" label="数量" rules={[{ required: true, message: '请输入数量' }]}>
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="delivery_time" label="交付期限">
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="sequence" label="排序">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="order_status" label="订单状态" rules={[{ required: true, message: '请选择订单状态' }]}>
            <Select options={orderStatusOptions} />
          </Form.Item>
          <Form.Item name="scheduling_status" label="排产状态">
            <Select options={schedulingStatusOptions} />
          </Form.Item>
          <Form.Item name="can_schedule" label="参与排产" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="supplement" label="补单" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="parent_order_code" label="父订单编码">
            <Input placeholder="补单时填写原订单编码" />
          </Form.Item>
          <Form.Item name="color" label="颜色标记">
            <Input placeholder="如: #ff0000 或 red" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

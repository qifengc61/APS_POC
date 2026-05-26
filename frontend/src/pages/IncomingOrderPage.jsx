import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm, DatePicker } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { incomingOrderApi, materialApi } from '../api/api'
import dayjs from 'dayjs'

const statusOptions = [
  { value: 'PENDING', label: '待到货' },
  { value: 'ARRIVED', label: '已到货' },
  { value: 'CANCELLED', label: '已取消' },
]

const statusMap = Object.fromEntries(statusOptions.map(o => [o.value, o.label]))

export default function IncomingOrderPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [materials, setMaterials] = useState([])
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await incomingOrderApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取来料订单列表失败')
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
      expected_arrival_time: record.expected_arrival_time ? dayjs(record.expected_arrival_time) : null,
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await incomingOrderApi.delete(id)
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = {
        ...values,
        expected_arrival_time: values.expected_arrival_time ? values.expected_arrival_time.format('YYYY-MM-DD HH:mm:ss') : null,
      }
      if (editingRecord) {
        await incomingOrderApi.update(editingRecord.id, submitData)
        message.success('更新成功')
      } else {
        await incomingOrderApi.create(submitData)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    {
      title: '物料',
      dataIndex: 'material_id',
      key: 'material_id',
      render: v => {
        const m = materials.find(item => item.id === v)
        return m ? `${m.code} (${m.name})` : v
      },
    },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '预计到货时间', dataIndex: 'expected_arrival_time', key: 'expected_arrival_time' },
    { title: '订单编码', dataIndex: 'order_code', key: 'order_code' },
    { title: '状态', dataIndex: 'status', key: 'status', render: v => statusMap[v] || v },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该来料订单吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增来料订单</Button>
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
        title={editingRecord ? '编辑来料订单' : '新增来料订单'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="material_id" label="物料" rules={[{ required: true, message: '请选择物料' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={materials.map(m => ({
                value: m.id,
                label: `${m.code} - ${m.name}`,
              }))}
            />
          </Form.Item>
          <Form.Item name="quantity" label="数量" rules={[{ required: true, message: '请输入数量' }]}>
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="expected_arrival_time" label="预计到货时间">
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="order_code" label="订单编码">
            <Input />
          </Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={statusOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

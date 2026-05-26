import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { resourceApi } from '../api/api'

const statusOptions = [
  { value: 'NORMAL', label: '正常' },
  { value: 'MAINTENANCE', label: '维护' },
  { value: 'SCRAPPED', label: '报废' },
]

const statusMap = Object.fromEntries(statusOptions.map(o => [o.value, o.label]))

const parseValueUnit = (str) => {
  if (!str) return null
  const match = String(str).match(/^(\d+(?:\.\d+)?)(.+)$/)
  return match ? { value: parseFloat(match[1]), unit: match[2] } : null
}

const combineValueUnit = (obj) => {
  if (!obj || obj.value == null || !obj.unit) return null
  return `${obj.value}${obj.unit}`
}

export default function ResourcePage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await resourceApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取资源列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
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
      throughput: parseValueUnit(record.throughput),
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await resourceApi.delete(id)
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = { ...values, throughput: combineValueUnit(values.throughput) }
      if (editingRecord) {
        await resourceApi.update(editingRecord.id, submitData)
        message.success('更新成功')
      } else {
        await resourceApi.create(submitData)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    { title: '编码', dataIndex: 'code', key: 'code' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '资源组', dataIndex: 'resource_group', key: 'resource_group' },
    { title: '容量', dataIndex: 'capacity', key: 'capacity' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '默认产能', dataIndex: 'throughput', key: 'throughput' },
    { title: '状态', dataIndex: 'resource_status', key: 'resource_status', render: v => statusMap[v] || v },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该资源吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增资源</Button>
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
        title={editingRecord ? '编辑资源' : '新增资源'}
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
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="resource_group" label="资源组">
            <Input />
          </Form.Item>
          <Form.Item name="capacity" label="容量">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="unit" label="单位">
            <Input />
          </Form.Item>
          <Form.Item label="默认产能">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name={['throughput', 'value']} noStyle>
                <InputNumber min={0} placeholder="数值" style={{ width: '65%' }} />
              </Form.Item>
              <Form.Item name={['throughput', 'unit']} noStyle>
                <Select style={{ width: '35%' }} placeholder="单位" options={[
                  { value: '/H', label: '件/小时 (/H)' },
                  { value: '/M', label: '件/分钟 (/M)' },
                  { value: 'M/P', label: '分钟/件 (M/P)' },
                  { value: '/D', label: '件/天 (/D)' },
                ]} />
              </Form.Item>
            </Space.Compact>
          </Form.Item>
          <Form.Item name="resource_status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={statusOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { materialApi } from '../api/api'

const typeOptions = [
  { value: 'RAW_MATERIAL', label: '原材料' },
  { value: 'SEMI_FINISHED', label: '半成品' },
  { value: 'FINISHED', label: '成品' },
]

const sourceOptions = [
  { value: 'PRODUCED', label: '自制' },
  { value: 'PURCHASED', label: '外购' },
]

const typeMap = Object.fromEntries(typeOptions.map(o => [o.value, o.label]))
const sourceMap = Object.fromEntries(sourceOptions.map(o => [o.value, o.label]))

export default function MaterialPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await materialApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取物料列表失败')
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
    form.setFieldsValue(record)
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await materialApi.delete(id)
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingRecord) {
        await materialApi.update(editingRecord.id, values)
        message.success('更新成功')
      } else {
        await materialApi.create(values)
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
    { title: '类型', dataIndex: 'type', key: 'type', render: v => typeMap[v] || v },
    { title: '来源', dataIndex: 'source', key: 'source', render: v => sourceMap[v] || v },
    { title: '当前库存', dataIndex: 'quantity', key: 'quantity' },
    { title: '安全库存', dataIndex: 'safety_stock', key: 'safety_stock' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '提前期', dataIndex: 'lead_time', key: 'lead_time' },
    { title: '缓冲期', dataIndex: 'buffer_time', key: 'buffer_time' },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该物料吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增物料</Button>
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
        title={editingRecord ? '编辑物料' : '新增物料'}
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
          <Form.Item name="type" label="类型" rules={[{ required: true, message: '请选择类型' }]}>
            <Select options={typeOptions} />
          </Form.Item>
          <Form.Item name="source" label="来源" rules={[{ required: true, message: '请选择来源' }]}>
            <Select options={sourceOptions} />
          </Form.Item>
          <Form.Item name="quantity" label="当前库存">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="safety_stock" label="安全库存">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="unit" label="单位">
            <Input />
          </Form.Item>
          <Form.Item name="lead_time" label="提前期">
            <Input placeholder="如: 3D" />
          </Form.Item>
          <Form.Item name="buffer_time" label="缓冲期">
            <Input placeholder="如: 1D" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

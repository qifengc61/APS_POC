import { useState, useEffect } from 'react'
import { Table, Modal, Form, Select, Switch, Button, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, CheckCircleOutlined, StopOutlined } from '@ant-design/icons'
import { processRouteApi, materialApi } from '../api/api'
import ProcessRouteEditor from '../components/ProcessRouteEditor'

export default function ProcessRoutePage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [materials, setMaterials] = useState([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [form] = Form.useForm()
  const [editorOpen, setEditorOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await processRouteApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取工艺路线列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchMaterials = async () => {
    try {
      const res = await materialApi.list({ page: 1, page_size: 1000 })
      setMaterials(res.items || res.data || [])
    } catch {
      message.error('获取物料列表失败')
    }
  }

  useEffect(() => {
    fetchData()
    fetchMaterials()
  }, [])

  const handleAdd = () => {
    form.resetFields()
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await processRouteApi.create(values)
      message.success('创建成功')
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const handleDelete = async (id) => {
    try {
      await processRouteApi.delete(id)
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleToggleEnabled = async (record) => {
    try {
      await processRouteApi.update(record.id, { ...record, enabled: !record.enabled })
      message.success(record.enabled ? '已禁用' : '已启用')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const handleEditDag = (record) => {
    setEditingRecord(record)
    setEditorOpen(true)
  }

  const handleEditorSave = () => {
    setEditorOpen(false)
    setEditingRecord(null)
    fetchData(pagination.current, pagination.pageSize)
  }

  const getNodeCount = (record) => {
    try {
      const design = typeof record.route_design === 'string' ? JSON.parse(record.route_design) : record.route_design
      return design?.nodes?.length || 0
    } catch {
      return 0
    }
  }

  const getEdgeCount = (record) => {
    try {
      const design = typeof record.route_design === 'string' ? JSON.parse(record.route_design) : record.route_design
      return design?.edges?.length || 0
    } catch {
      return 0
    }
  }

  const columns = [
    { title: '物料ID', dataIndex: 'material_id', key: 'material_id' },
    {
      title: '是否启用',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (v) => v ? '是' : '否',
    },
    {
      title: '节点数量',
      key: 'nodeCount',
      render: (_, record) => getNodeCount(record),
    },
    {
      title: '边数量',
      key: 'edgeCount',
      render: (_, record) => getEdgeCount(record),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEditDag(record)}>编辑DAG</Button>
          <Button
            type="link"
            icon={record.enabled ? <StopOutlined /> : <CheckCircleOutlined />}
            onClick={() => handleToggleEnabled(record)}
          >
            {record.enabled ? '禁用' : '启用'}
          </Button>
          <Popconfirm title="确定删除该工艺路线吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增工艺路线</Button>
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
        title="新增工艺路线"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="material_id" label="物料" rules={[{ required: true, message: '请选择物料' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={materials.map(m => ({ value: m.id, label: `${m.code} - ${m.name}` }))}
              placeholder="请选择物料"
            />
          </Form.Item>
          <Form.Item name="enabled" label="是否启用" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
      <ProcessRouteEditor
        open={editorOpen}
        record={editingRecord}
        onSave={handleEditorSave}
        onCancel={() => {
          setEditorOpen(false)
          setEditingRecord(null)
        }}
      />
    </div>
  )
}

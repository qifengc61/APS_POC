import { useState, useEffect } from 'react'
import { Table, Modal, Form, Select, InputNumber, Button, Space, message, Popconfirm, Tag } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, MinusCircleOutlined } from '@ant-design/icons'
import { bomApi, materialApi } from '../api/api'

export default function BomPage() {
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
      const res = await bomApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取BOM列表失败')
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
      material_id: record.material_id,
      child_materials: (record.child_materials || []).map(cm => ({
        material_id: cm.material_id,
        quantity: cm.quantity,
      })),
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await bomApi.delete(id)
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
        material_id: values.material_id,
        child_materials: (values.child_materials || []).map(cm => ({
          material_id: cm.material_id,
          quantity: cm.quantity,
        })),
      }
      if (editingRecord) {
        await bomApi.update(editingRecord.id, submitData)
        message.success('更新成功')
      } else {
        await bomApi.create(submitData)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 200, ellipsis: true },
    {
      title: '成品物料',
      dataIndex: 'material_id',
      key: 'material_id',
      width: 180,
      render: v => {
        const m = materials.find(item => item.id === v)
        return m ? <span style={{ fontWeight: 500 }}>{m.code}</span> : <Tag>{v}</Tag>
      },
    },
    {
      title: '子件列表',
      dataIndex: 'child_materials',
      key: 'child_materials',
      render: v => (
        <Space wrap size={[4, 4]}>
          {(v || []).map((cm, idx) => {
            const m = materials.find(item => item.id === cm.material_id)
            return (
              <Tag key={idx} color="blue" style={{ margin: 0 }}>
                {m ? m.code : cm.material_id}
                <span style={{ marginLeft: 4, opacity: 0.7 }}>×{cm.quantity}</span>
              </Tag>
            )
          })}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该BOM吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增BOM</Button>
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
        title={editingRecord ? '编辑BOM' : '新增BOM'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="material_id" label="成品物料" rules={[{ required: true, message: '请选择成品物料' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={materials.map(m => ({
                value: m.id,
                label: `${m.code} - ${m.name}`,
              }))}
            />
          </Form.Item>
          <Form.List name="child_materials">
            {(fields, { add, remove }) => (
              <>
                <div style={{ marginBottom: 8, fontWeight: 600 }}>子件列表</div>
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item {...restField} name={[name, 'material_id']} rules={[{ required: true, message: '请选择物料' }]}>
                      <Select
                        showSearch
                        optionFilterProp="label"
                        style={{ width: 250 }}
                        placeholder="选择子件物料"
                        options={materials.map(m => ({
                          value: m.id,
                          label: `${m.code} - ${m.name}`,
                        }))}
                      />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'quantity']} rules={[{ required: true, message: '请输入数量' }]}>
                      <InputNumber min={1} placeholder="数量" style={{ width: 120 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(name)} style={{ color: '#ff4d4f' }} />
                  </Space>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加子件</Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, MinusCircleOutlined } from '@ant-design/icons'
import { processApi, resourceApi, materialApi } from '../api/api'

const relationshipOptions = [
  { value: 'ES', label: '串行' },
  { value: 'EE', label: '并行' },
]

const relationshipMap = Object.fromEntries(relationshipOptions.map(o => [o.value, o.label]))

const durationUnitOptions = [
  { value: 'M', label: '分钟 (M)' },
  { value: 'H', label: '小时 (H)' },
  { value: 'D', label: '天 (D)' },
]

const parseValueUnit = (str) => {
  if (!str) return null
  const match = String(str).match(/^(\d+(?:\.\d+)?)(.+)$/)
  return match ? { value: parseFloat(match[1]), unit: match[2] } : null
}

const combineValueUnit = (obj) => {
  if (!obj || obj.value == null || !obj.unit) return null
  return `${obj.value}${obj.unit}`
}

export default function ProcessPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [resources, setResources] = useState([])
  const [materials, setMaterials] = useState([])
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await processApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取工序列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchResources = async () => {
    try {
      const res = await resourceApi.list({ page: 1, page_size: 1000 })
      setResources(res.items || res.data || [])
    } catch {}
    try {
      const matRes = await materialApi.list({ page: 1, page_size: 1000 })
      setMaterials(matRes.items || matRes.data || [])
    } catch {}
  }

  useEffect(() => {
    fetchData()
    fetchResources()
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
      pre_interval_duration: parseValueUnit(record.pre_interval_duration),
      post_interval_duration: parseValueUnit(record.post_interval_duration),
      buffer_time: parseValueUnit(record.buffer_time),
      use_main_resources: record.use_main_resources || [],
      use_auxiliary_resources: record.use_auxiliary_resources || [],
      use_materials: record.use_materials || [],
      batch_strategy: typeof record.batch_strategy === 'object' ? JSON.stringify(record.batch_strategy, null, 2) : (record.batch_strategy || ''),
    })
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await processApi.delete(id)
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
        pre_interval_duration: combineValueUnit(values.pre_interval_duration),
        post_interval_duration: combineValueUnit(values.post_interval_duration),
        buffer_time: combineValueUnit(values.buffer_time),
        batch_strategy: (() => {
          const bs = values.batch_strategy
          if (!bs || (typeof bs === 'string' && bs.trim() === '')) return null
          try { return JSON.parse(bs) } catch { return bs }
        })(),
      }
      if (editingRecord) {
        await processApi.update(editingRecord.id, submitData)
        message.success('更新成功')
      } else {
        await processApi.create(submitData)
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
    { title: '工序关系', dataIndex: 'process_relationship', key: 'process_relationship', render: v => relationshipMap[v] || v },
    { title: '前间隔', dataIndex: 'pre_interval_duration', key: 'pre_interval_duration' },
    { title: '后间隔', dataIndex: 'post_interval_duration', key: 'post_interval_duration' },
    { title: '缓冲时长', dataIndex: 'buffer_time', key: 'buffer_time' },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该工序吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增工序</Button>
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
        title={editingRecord ? '编辑工序' : '新增工序'}
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
          <Form.Item name="process_relationship" label="工序关系" rules={[{ required: true, message: '请选择工序关系' }]}>
            <Select options={relationshipOptions} />
          </Form.Item>
          <Form.Item label="前间隔">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name={['pre_interval_duration', 'value']} noStyle>
                <InputNumber min={0} placeholder="数值" style={{ width: '65%' }} />
              </Form.Item>
              <Form.Item name={['pre_interval_duration', 'unit']} noStyle>
                <Select style={{ width: '35%' }} placeholder="单位" options={durationUnitOptions} />
              </Form.Item>
            </Space.Compact>
          </Form.Item>
          <Form.Item label="后间隔">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name={['post_interval_duration', 'value']} noStyle>
                <InputNumber min={0} placeholder="数值" style={{ width: '65%' }} />
              </Form.Item>
              <Form.Item name={['post_interval_duration', 'unit']} noStyle>
                <Select style={{ width: '35%' }} placeholder="单位" options={durationUnitOptions} />
              </Form.Item>
            </Space.Compact>
          </Form.Item>
          <Form.Item label="缓冲时长">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name={['buffer_time', 'value']} noStyle>
                <InputNumber min={0} placeholder="数值" style={{ width: '65%' }} />
              </Form.Item>
              <Form.Item name={['buffer_time', 'unit']} noStyle>
                <Select style={{ width: '35%' }} placeholder="单位" options={durationUnitOptions} />
              </Form.Item>
            </Space.Compact>
          </Form.Item>
          <Form.Item name="batch_strategy" label="批次策略">
            <Input.TextArea rows={3} placeholder="JSON格式，如：{&quot;strategy&quot;: &quot;fixed_batch&quot;, &quot;size&quot;: 100}" />
          </Form.Item>
          <Form.Item label="主资源">
            <Form.List name="use_main_resources">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item {...restField} name={[name, 'resource_id']} rules={[{ required: true, message: '请选择资源' }]} style={{ marginBottom: 0 }}>
                        <Select
                          showSearch
                          optionFilterProp="label"
                          style={{ width: 250 }}
                          placeholder="选择资源"
                          options={resources.map(r => ({
                            value: r.id,
                            label: `${r.code} - ${r.name}`,
                          }))}
                        />
                      </Form.Item>
                      <Form.Item {...restField} name={[name, 'quantity']} rules={[{ required: true, message: '请输入数量' }]} style={{ marginBottom: 0 }}>
                        <InputNumber min={1} placeholder="数量" style={{ width: 120 }} />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} style={{ color: '#ff4d4f' }} />
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加主资源</Button>
                </>
              )}
            </Form.List>
          </Form.Item>
          <Form.Item label="辅助资源">
            <Form.List name="use_auxiliary_resources">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item {...restField} name={[name, 'resource_id']} rules={[{ required: true, message: '请选择资源' }]} style={{ marginBottom: 0 }}>
                        <Select
                          showSearch
                          optionFilterProp="label"
                          style={{ width: 250 }}
                          placeholder="选择资源"
                          options={resources.map(r => ({
                            value: r.id,
                            label: `${r.code} - ${r.name}`,
                          }))}
                        />
                      </Form.Item>
                      <Form.Item {...restField} name={[name, 'quantity']} rules={[{ required: true, message: '请输入数量' }]} style={{ marginBottom: 0 }}>
                        <InputNumber min={1} placeholder="数量" style={{ width: 120 }} />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} style={{ color: '#ff4d4f' }} />
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加辅助资源</Button>
                </>
              )}
            </Form.List>
          </Form.Item>
          <Form.Item label="使用物料">
            <Form.List name="use_materials">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item {...restField} name={[name, 'material_id']} rules={[{ required: true, message: '请选择物料' }]} style={{ marginBottom: 0 }}>
                        <Select
                          showSearch
                          optionFilterProp="label"
                          style={{ width: 250 }}
                          placeholder="选择物料"
                          options={materials.map(m => ({
                            value: m.id,
                            label: `${m.code} - ${m.name}`,
                          }))}
                        />
                      </Form.Item>
                      <Form.Item {...restField} name={[name, 'quantity']} rules={[{ required: true, message: '请输入数量' }]} style={{ marginBottom: 0 }}>
                        <InputNumber min={1} placeholder="数量" style={{ width: 120 }} />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} style={{ color: '#ff4d4f' }} />
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加物料</Button>
                </>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

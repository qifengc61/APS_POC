import { useState, useEffect } from 'react'
import { Table, Modal, Form, Input, Select, InputNumber, Button, Space, message, Popconfirm, Switch, Slider, DatePicker } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, MinusCircleOutlined } from '@ant-design/icons'
import { strategyApi } from '../api/api'
import dayjs from 'dayjs'

const directionOptions = [
  { value: 'FORWARD', label: '正向' },
  { value: 'BACKWARD', label: '逆向' },
]

const sortDirectionOptions = [
  { value: 'ASC', label: '升序' },
  { value: 'DESC', label: '降序' },
]

const optimizationRules = [
  { key: 'scheduling_rules', label: '按策略排序规则排列' },
  { key: 'minimize_tardiness', label: '最小化延期总时长' },
  { key: 'minimize_tardiness_task_number', label: '最小化延期任务数量' },
  { key: 'prioritize_delivery_time', label: '优先安排临近交期' },
  { key: 'minimize_gap_between_dependent_tasks', label: '最小化依赖任务间隔' },
  { key: 'finish_early', label: '尽早完成' },
  { key: 'balance_task_count', label: '均衡任务数量' },
  { key: 'balance_workload', label: '均衡工作负载' },
]

export default function StrategyPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [ruleOptions, setRuleOptions] = useState([])
  const [form] = Form.useForm()

  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const res = await strategyApi.list({ page, page_size: pageSize })
      setData(res.items || res.data || [])
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: res.total || (res.items || res.data || []).length,
      }))
    } catch {
      message.error('获取策略列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchRuleOptions = async () => {
    try {
      const res = await strategyApi.getRuleOptions()
      setRuleOptions(res.items || res.data || res || [])
    } catch {
      message.error('获取排序规则选项失败')
    }
  }

  useEffect(() => {
    fetchData()
    fetchRuleOptions()
  }, [])

  const handleAdd = () => {
    setEditingRecord(null)
    form.resetFields()
    const defaultWeights = {}
    optimizationRules.forEach(r => { defaultWeights[r.key] = 0 })
    form.setFieldsValue({ optimization_weights: defaultWeights })
    setModalOpen(true)
  }

  const handleEdit = (record) => {
    setEditingRecord(record)
    const formValues = {
      ...record,
      begin_time: record.begin_time ? dayjs(record.begin_time) : undefined,
    }
    if (record.optimization_weights) {
      const weights = typeof record.optimization_weights === 'string'
        ? JSON.parse(record.optimization_weights)
        : record.optimization_weights
      formValues.optimization_weights = weights
    } else {
      const defaultWeights = {}
      optimizationRules.forEach(r => { defaultWeights[r.key] = 0 })
      formValues.optimization_weights = defaultWeights
    }
    if (record.order_sorting_rules) {
      const rules = typeof record.order_sorting_rules === 'string'
        ? JSON.parse(record.order_sorting_rules)
        : record.order_sorting_rules
      formValues.order_sorting_rules = rules
    }
    form.setFieldsValue(formValues)
    setModalOpen(true)
  }

  const handleDelete = async (id) => {
    try {
      await strategyApi.delete(id)
      message.success('删除成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (values.begin_time) {
        values.begin_time = values.begin_time.format('YYYY-MM-DD HH:mm:ss')
      }
      if (editingRecord) {
        await strategyApi.update(editingRecord.id, values)
        message.success('更新成功')
      } else {
        await strategyApi.create(values)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('操作失败')
    }
  }

  const handleActiveChange = async (checked, record) => {
    try {
      await strategyApi.toggleActive(record.id, { active: checked })
      message.success('更新成功')
      fetchData(pagination.current, pagination.pageSize)
    } catch {
      message.error('更新失败')
    }
  }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '排产开始时间', dataIndex: 'begin_time', key: 'begin_time' },
    {
      title: '是否有效',
      dataIndex: 'active',
      key: 'active',
      render: (v, record) => (
        <Switch checked={v} onChange={checked => handleActiveChange(checked, record)} />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除该策略吗？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增策略</Button>
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
        title={editingRecord ? '编辑策略' : '新增策略'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="begin_time" label="排产开始时间">
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="direction" label="排产方向">
            <Select options={directionOptions} />
          </Form.Item>
          <Form.Item name="materialConstrained" label="物料约束" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="maxNoImprovementTime" label="最大无改进时间（分钟）">
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item label="订单排序规则">
            <Form.List name="order_sorting_rules">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item {...restField} name={[name, 'field']} rules={[{ required: true, message: '请选择字段' }]}>
                        <Select placeholder="选择字段" style={{ width: 200 }} options={ruleOptions.map ? ruleOptions.map(o => ({ value: typeof o === 'string' ? o : o.value, label: typeof o === 'string' ? o : o.label })) : []} />
                      </Form.Item>
                      <Form.Item {...restField} name={[name, 'direction']} rules={[{ required: true, message: '请选择方向' }]}>
                        <Select placeholder="排序方向" style={{ width: 120 }} options={sortDirectionOptions} />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} />
                    </Space>
                  ))}
                  <Button type="dashed" onClick={() => add()} block>
                    添加排序规则
                  </Button>
                </>
              )}
            </Form.List>
          </Form.Item>
          <Form.Item label="优化规则权重">
            {optimizationRules.map(rule => (
              <Form.Item
                key={rule.key}
                name={['optimization_weights', rule.key]}
                label={rule.label}
                style={{ marginBottom: 12 }}
              >
                <Slider
                  min={0}
                  max={100}
                  marks={{ 0: '0', 50: '50', 100: '100' }}
                />
              </Form.Item>
            ))}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

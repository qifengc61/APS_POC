import { useState, useEffect, useRef, useCallback } from 'react'
import { Drawer, Table, Tag, Select, Space, Button, Typography, Switch } from 'antd'
import {
  ClearOutlined,
  PauseCircleOutlined,
  CaretRightOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { subscribe, clearLogs, getLogs } from '../utils/logger'

const { Text } = Typography

const typeColors = {
  request: 'processing',
  response: 'success',
  error: 'error',
}

const methodColors = {
  GET: 'green',
  POST: 'blue',
  PUT: 'orange',
  DELETE: 'red',
  PATCH: 'purple',
}

function formatData(data) {
  if (data === undefined || data === null) return ''
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

function formatTimestamp(ts) {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('zh-CN', { hour12: false })
  } catch {
    return ts
  }
}

export default function LogViewer({ open, onClose }) {
  const [logs, setLogs] = useState(() => getLogs())
  const [paused, setPaused] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [filterType, setFilterType] = useState(undefined)
  const [filterMethod, setFilterMethod] = useState(undefined)
  const [detailOpen, setDetailOpen] = useState(null)
  const tableRef = useRef(null)

  useEffect(() => {
    if (paused) return
    return subscribe((newLogs) => setLogs(newLogs))
  }, [paused])

  const filtered = logs.filter((log) => {
    if (filterType && log.type !== filterType) return false
    if (filterMethod && log.method !== filterMethod) return false
    return true
  })

  const handleClear = useCallback(() => {
    clearLogs()
    setDetailOpen(null)
  }, [])

  const toggleRow = (id) => {
    setDetailOpen((prev) => (prev === id ? null : id))
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 90,
      render: (v) => <Text code style={{ fontSize: 11 }}>{formatTimestamp(v)}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 70,
      render: (v) => <Tag color={typeColors[v]} style={{ margin: 0 }}>{v}</Tag>,
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 70,
      render: (v) => <Tag color={methodColors[v] || 'default'} style={{ margin: 0 }}>{v}</Tag>,
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
      render: (v) => <Text code style={{ fontSize: 12 }}>{v}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 60,
      render: (v, record) => {
        if (record.type === 'request') return null
        const isErr = record.type === 'error' || (typeof v === 'number' && v >= 400)
        return (
          <Text style={{ color: isErr ? '#ff4d4f' : '#52c41a', fontWeight: 600 }}>
            {v ?? '--'}
          </Text>
        )
      },
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      width: 65,
      render: (v) => (v != null ? <Text style={{ fontSize: 12 }}>{v}ms</Text> : null),
    },
  ]

  return (
    <Drawer
      title={
        <Space>
          <span>📋 请求日志</span>
          <Tag>{filtered.length} / {logs.length}</Tag>
        </Space>
      }
      placement="right"
      width={900}
      open={open}
      onClose={onClose}
      extra={
        <Space>
          <Select
            allowClear
            placeholder="类型"
            style={{ width: 90 }}
            value={filterType}
            onChange={setFilterType}
            options={[
              { value: 'request', label: '请求' },
              { value: 'response', label: '响应' },
              { value: 'error', label: '错误' },
            ]}
          />
          <Select
            allowClear
            placeholder="方法"
            style={{ width: 90 }}
            value={filterMethod}
            onChange={setFilterMethod}
            options={['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].map((m) => ({
              value: m,
              label: m,
            }))}
          />
          <Button
            icon={paused ? <CaretRightOutlined /> : <PauseCircleOutlined />}
            onClick={() => setPaused(!paused)}
          >
            {paused ? '继续' : '暂停'}
          </Button>
          <Space>
            <Text style={{ fontSize: 12 }}>自动滚动</Text>
            <Switch size="small" checked={autoScroll} onChange={setAutoScroll} />
          </Space>
          <Button icon={<ClearOutlined />} onClick={handleClear} danger>清空</Button>
        </Space>
      }
      styles={{ body: { padding: 0 } }}
    >
      <Table
        ref={tableRef}
        rowKey="id"
        size="small"
        columns={columns}
        dataSource={filtered}
        pagination={{ pageSize: 50, showSizeChanger: true, pageSizeOptions: ['20', '50', '100', '200'] }}
        expandable={{
          expandedRowKeys: detailOpen ? [detailOpen] : [],
          onExpandedRowsChange: (keys) => setDetailOpen(keys[0] || null),
          expandedRowRender: (record) => (
            <pre style={{
              maxHeight: 300,
              overflow: 'auto',
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 6,
              fontSize: 12,
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}>
              {formatData(record.data)}
            </pre>
          ),
          expandRowByClick: true,
          rowExpandable: () => true,
        }}
      />
    </Drawer>
  )
}

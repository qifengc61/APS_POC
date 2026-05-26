import { useState, useEffect, useCallback, useRef } from 'react'
import { Modal, Button, message, Spin } from 'antd'
import {
  ReactFlow,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { processApi, processRouteApi } from '../api/api'

function ProcessNode({ data }) {
  return (
    <div style={{
      padding: '8px 16px',
      borderRadius: 6,
      border: '2px solid #1a3a6b',
      background: '#fff',
      minWidth: 120,
      textAlign: 'center',
      fontSize: 13,
    }}>
      <Handle type="target" position={Position.Left} />
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{data.processName}</div>
      <div style={{ color: '#888', fontSize: 11 }}>{data.processCode}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

const nodeTypes = { processNode: ProcessNode }

export default function ProcessRouteEditor({ open, record, onSave, onCancel }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [processes, setProcesses] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const reactFlowWrapper = useRef(null)
  const reactFlowInstance = useRef(null)

  useEffect(() => {
    if (open) {
      fetchProcesses()
      loadRouteDesign()
    }
  }, [open, record])

  const fetchProcesses = async () => {
    setLoading(true)
    try {
      const res = await processApi.list({ page: 1, page_size: 1000 })
      setProcesses(res.items || res.data || [])
    } catch {
      message.error('获取工序列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadRouteDesign = () => {
    if (!record?.route_design) {
      setNodes([])
      setEdges([])
      return
    }
    try {
      const design = typeof record.route_design === 'string'
        ? JSON.parse(record.route_design)
        : record.route_design

      const flowNodes = (design.nodes || []).map((n, i) => ({
        id: n.id,
        type: 'processNode',
        position: n.position || { x: 100 + i * 200, y: 100 + i * 80 },
        data: {
          label: n.data?.processName || n.id,
          processCode: n.data?.processCode || n.id,
          processName: n.data?.processName || n.id,
          ...n.data,
        },
      }))

      const flowEdges = (design.edges || []).map(e => ({
        id: `edge-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
      }))

      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch {
      setNodes([])
      setEdges([])
    }
  }

  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge({
      ...params,
      id: `edge-${params.source}-${params.target}`,
    }, eds))
  }, [setEdges])

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((event) => {
    event.preventDefault()
    const processData = event.dataTransfer.getData('application/reactflow')
    if (!processData) return

    const parsed = JSON.parse(processData)
    const bounds = reactFlowWrapper.current?.getBoundingClientRect()
    if (!bounds || !reactFlowInstance.current) return

    const position = reactFlowInstance.current.screenToFlowPosition({
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top,
    })

    const newNode = {
      id: parsed.code,
      type: 'processNode',
      position,
      data: {
        label: parsed.name,
        processCode: parsed.code,
        processName: parsed.name,
        ...parsed,
      },
    }
    setNodes((nds) => [...nds, newNode])
  }, [setNodes])

  const onInit = useCallback((instance) => {
    reactFlowInstance.current = instance
  }, [])

  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Delete' || event.key === 'Backspace') {
      setNodes((nds) => nds.filter((n) => !n.selected))
      setEdges((eds) => eds.filter((e) => !e.selected))
    }
  }, [setNodes, setEdges])

  const onNodeContextMenu = useCallback((event, node) => {
    event.preventDefault()
    setNodes((nds) => nds.filter((n) => n.id !== node.id))
    setEdges((eds) => eds.filter((e) => e.source !== node.id && e.target !== node.id))
  }, [setNodes, setEdges])

  const onEdgeContextMenu = useCallback((event, edge) => {
    event.preventDefault()
    setEdges((eds) => eds.filter((e) => e.id !== edge.id))
  }, [setEdges])

  const handleSave = async () => {
    if (nodes.length === 0) {
      message.warning('请至少添加一个工序节点')
      return
    }

    const routeDesign = {
      nodes: nodes.map(n => ({
        id: n.id,
        data: { ...n.data },
        position: n.position,
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target,
      })),
    }

    setSaving(true)
    try {
      const validateRes = await processRouteApi.validate(routeDesign)
      if (validateRes.valid === false) {
        const errors = validateRes.errors || []
        message.error(errors.join('; ') || 'DAG校验失败')
        setSaving(false)
        return
      }
    } catch (err) {
      const errData = err?.response?.data
      if (errData?.errors) {
        message.error(errData.errors.join('; '))
      } else if (errData?.detail) {
        message.error(errData.detail)
      } else {
        message.error('DAG校验失败')
      }
      setSaving(false)
      return
    }

    try {
      await processRouteApi.update(record.id, {
        ...record,
        route_design: routeDesign,
      })
      message.success('保存成功')
      onSave()
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const onDragStart = (event, process) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(process))
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <Modal
      title={`编辑工艺路线 - 物料ID: ${record?.material_id || ''}`}
      open={open}
      onCancel={onCancel}
      width="100vw"
      style={{ top: 0, maxWidth: '100vw', paddingBottom: 0 }}
      styles={{ body: { height: 'calc(100vh - 110px)', padding: 0 } }}
      footer={[
        <Button key="cancel" onClick={onCancel}>取消</Button>,
        <Button key="save" type="primary" loading={saving} onClick={handleSave}>保存</Button>,
      ]}
      destroyOnClose
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <div style={{
          width: 220,
          borderRight: '1px solid #e8e8e8',
          padding: 12,
          overflowY: 'auto',
          background: '#fafafa',
        }}>
          <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 14 }}>工序列表</div>
          <div style={{ color: '#999', fontSize: 12, marginBottom: 8 }}>拖拽工序到画布</div>
          {loading ? (
            <Spin />
          ) : (
            processes.map((p) => (
              <div
                key={p.id}
                draggable
                onDragStart={(e) => onDragStart(e, p)}
                style={{
                  padding: '8px 12px',
                  marginBottom: 6,
                  background: '#fff',
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                  cursor: 'grab',
                  fontSize: 13,
                }}
              >
                <div style={{ fontWeight: 500 }}>{p.name}</div>
                <div style={{ color: '#888', fontSize: 11 }}>{p.code}</div>
              </div>
            ))
          )}
        </div>
        <div
          ref={reactFlowWrapper}
          style={{ flex: 1, height: '100%' }}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={onInit}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeContextMenu={onNodeContextMenu}
            onEdgeContextMenu={onEdgeContextMenu}
            nodeTypes={nodeTypes}
            fitView
            style={{ background: '#f5f5f5' }}
          >
            <Controls />
            <Background />
          </ReactFlow>
        </div>
      </div>
    </Modal>
  )
}

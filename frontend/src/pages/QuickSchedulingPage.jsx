import { useState, useEffect, useRef } from 'react'
import { Spin, Alert, Typography } from 'antd'
import ParameterForm from '../components/ParameterForm'
import ResultTable from '../components/ResultTable'
import ResultCharts from '../components/ResultCharts'
import { calculateSchedule } from '../api/api'

const { Text } = Typography

export default function QuickSchedulingPage() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [safetyStock, setSafetyStock] = useState(100)
  const [debugMode, setDebugMode] = useState(false)
  const [dots, setDots] = useState('')
  const timerRef = useRef(null)

  useEffect(() => {
    if (loading) {
      timerRef.current = setInterval(() => {
        setDots(prev => prev.length >= 6 ? '' : prev + '.')
      }, 500)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
      setDots('')
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [loading])

  const handleCalculate = async (params, config) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setSafetyStock(params.safety_stock)

    try {
      const data = await calculateSchedule(params, config)
      if (data.success) {
        setResult(data)
      } else {
        setError(data.message || '排产计算失败')
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || '排产计算异常'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20, alignItems: 'start' }}>
      <div>
        <ParameterForm
          onCalculate={handleCalculate}
          loading={loading}
        />
      </div>

      <div>
        {error && (
          <Alert
            type="error"
            message={error}
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {loading && (
          <div style={{
            padding: 40,
            textAlign: 'center',
            backgroundColor: '#fff',
            borderRadius: 10,
            border: '1px solid #e5e7eb',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}>
            <Spin size="large" />
            <div style={{ fontSize: 16, color: '#6b7280', marginTop: 16, display: 'flex', justifyContent: 'center' }}>
              <span>正在计算排产方案{dots}</span>
            </div>
            <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 8 }}>OR-Tools CP-SAT 约束求解器优化中</div>
          </div>
        )}

        {!loading && !result && !error && (
          <div style={{
            padding: '60px 40px',
            textAlign: 'center',
            backgroundColor: '#fff',
            borderRadius: 10,
            border: '1px solid #e5e7eb',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
            <div style={{ fontSize: 18, color: '#6b7280', marginBottom: 8 }}>请配置参数并开始排产</div>
            <div style={{ fontSize: 13, color: '#9ca3af' }}>填写左侧参数后点击"开始排产"按钮</div>
          </div>
        )}

        {result && !loading && (
          <>
            {debugMode && result.solver_status !== undefined && (
              <div style={{
                padding: '10px 16px',
                backgroundColor: '#1e293b',
                borderRadius: 8,
                marginBottom: 16,
                display: 'flex',
                gap: 24,
                alignItems: 'center',
                fontFamily: 'monospace',
                fontSize: 13,
              }}>
                <span style={{ color: '#94a3b8' }}>🔍 求解器状态:</span>
                <span style={{
                  color: result.solver_status === 'OPTIMAL' ? '#4ade80' : '#fbbf24',
                  fontWeight: 600,
                }}>
                  {result.solver_status}
                </span>
                <span style={{ color: '#94a3b8' }}>⏱ 耗时:</span>
                <span style={{ color: '#38bdf8', fontWeight: 600 }}>
                  {result.solve_time}s
                </span>
              </div>
            )}
            <ResultTable result={result} />
            <ResultCharts result={result} safetyStock={safetyStock} />
          </>
        )}
      </div>
    </div>
  )
}

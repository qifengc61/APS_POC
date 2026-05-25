import { useState, useEffect, useRef } from 'react'
import ParameterForm from './components/ParameterForm'
import ResultTable from './components/ResultTable'
import ResultCharts from './components/ResultCharts'
import { calculateSchedule } from './api/api'
import './App.css'

function App() {
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
    <div style={{ minHeight: '100vh', backgroundColor: '#f0f2f5' }}>
      <header style={{
        backgroundColor: '#1e40af',
        color: '#fff',
        padding: '16px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px' }}>🏭</span>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '700' }}>智能排产系统</h1>
            <p style={{ margin: 0, fontSize: '12px', opacity: 0.8 }}>基于 Google OR-Tools CP-SAT 约束优化</p>
          </div>
        </div>
        <span style={{ fontSize: '12px', opacity: 0.6 }}>V1.0</span>
        <span
          onClick={() => setDebugMode(!debugMode)}
          style={{
            fontSize: '12px',
            opacity: debugMode ? 1 : 0.4,
            cursor: 'pointer',
            marginLeft: '12px',
            padding: '2px 8px',
            borderRadius: '4px',
            border: debugMode ? '1px solid rgba(255,255,255,0.6)' : '1px solid transparent',
            backgroundColor: debugMode ? 'rgba(255,255,255,0.15)' : 'transparent',
            transition: 'all 0.2s',
            userSelect: 'none',
          }}
        >
          🛠 {debugMode ? '调试' : '调试'}
        </span>
      </header>

      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px', alignItems: 'start' }}>
          <div>
            <ParameterForm
              onCalculate={handleCalculate}
              loading={loading}
            />
          </div>

          <div>
            {error && (
              <div style={{
                padding: '12px 16px',
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                color: '#dc2626',
                fontSize: '14px',
                marginBottom: '16px',
              }}>
                ❌ {error}
              </div>
            )}

            {loading && (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                backgroundColor: '#fff',
                borderRadius: '10px',
                border: '1px solid #e5e7eb',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}>
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>⏳</div>
                <div style={{ fontSize: '16px', color: '#6b7280', display: 'flex', justifyContent: 'center' }}>
                  <span>正在计算排产方案{dots}</span>
                </div>
                <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '8px' }}>OR-Tools CP-SAT 约束求解器优化中</div>
              </div>
            )}

            {!loading && !result && !error && (
              <div style={{
                padding: '60px 40px',
                textAlign: 'center',
                backgroundColor: '#fff',
                borderRadius: '10px',
                border: '1px solid #e5e7eb',
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                <div style={{ fontSize: '18px', color: '#6b7280', marginBottom: '8px' }}>请配置参数并开始排产</div>
                <div style={{ fontSize: '13px', color: '#9ca3af' }}>填写左侧参数后点击"开始排产"按钮</div>
              </div>
            )}

            {result && !loading && (
              <>
                {debugMode && result.solver_status !== undefined && (
                  <div style={{
                    padding: '10px 16px',
                    backgroundColor: '#1e293b',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    display: 'flex',
                    gap: '24px',
                    alignItems: 'center',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                  }}>
                    <span style={{ color: '#94a3b8' }}>🔍 求解器状态:</span>
                    <span style={{
                      color: result.solver_status === 'OPTIMAL' ? '#4ade80' : '#fbbf24',
                      fontWeight: '600',
                    }}>
                      {result.solver_status}
                    </span>
                    <span style={{ color: '#94a3b8' }}>⏱ 耗时:</span>
                    <span style={{ color: '#38bdf8', fontWeight: '600' }}>
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
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '16px',
        color: '#9ca3af',
        fontSize: '12px',
      }}>
        智能排产系统 © 2026 | Google OR-Tools CP-SAT 约束优化引擎
      </footer>
    </div>
  )
}

export default App

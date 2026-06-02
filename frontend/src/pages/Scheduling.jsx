import { useState, useEffect, useRef } from 'react'
import { listDeliveryPlans, calculateScheduleByPlan, scheduleExport } from '../api/api'
import ResultTable from '../components/ResultTable'
import ResultCharts from '../components/ResultCharts'

const MATERIAL_COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']
const LINE_COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2']

const defaultConfig = {
  avoid_rest_work_weight: 50,
  max_time_seconds: 30,
}

export default function SchedulingPage() {
  const [plans, setPlans] = useState([])
  const [selectedPlanId, setSelectedPlanId] = useState('')
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [config, setConfig] = useState(defaultConfig)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [debugMode, setDebugMode] = useState(false)
  const [activeLineIdx, setActiveLineIdx] = useState(0)
  const [activeProductIdx, setActiveProductIdx] = useState(0)
  const [dots, setDots] = useState('')
  const timerRef = useRef(null)

  useEffect(() => { loadPlans() }, [])

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

  const loadPlans = async () => {
    const data = await listDeliveryPlans()
    setPlans(data)
  }

  const handlePlanSelect = (planId) => {
    setSelectedPlanId(planId)
    const plan = plans.find(p => p.id === parseInt(planId))
    setSelectedPlan(plan || null)
    setResult(null)
    setError(null)
    setActiveLineIdx(0)
    setActiveProductIdx(0)
  }

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: parseFloat(value) }))
  }

  const buildApiConfig = () => ({
    rest_day_weight: config.avoid_rest_work_weight,
    max_time_seconds: config.max_time_seconds,
  })

  const handleCalculate = async () => {
    if (!selectedPlanId) { alert('请先选择交货计划'); return }
    setLoading(true)
    setError(null)
    setResult(null)
    setActiveLineIdx(0)
    setActiveProductIdx(0)

    try {
      const data = await calculateScheduleByPlan(parseInt(selectedPlanId), buildApiConfig())
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

  const handleExport = async (lineResult, linePlan) => {
    if (!lineResult || !linePlan) return
    try {
      const planInfo = (linePlan.materials || []).map((m) => ({
        code: m.product_code || m.product_name || '',
        name: m.product_name || '',
        initial_inventory: m.initial_inventory || 0,
        safety_stock: m.safety_stock || 0,
        rated_output: m.rated_output || 0,
        total_delivery: m.total_delivery || 0,
      }))
      await scheduleExport(lineResult, planInfo)
    } catch (err) {
      alert('导出失败: ' + (err.message || '未知错误'))
    }
  }

  const lineResults = result?.line_results || []
  const activeLineResult = lineResults[activeLineIdx] || null
  const activeLinePlan = selectedPlan?.lines?.[activeLineIdx] || null

  const inputStyle = {
    width: '100%', padding: '8px 12px', border: '1px solid #d1d5db',
    borderRadius: '6px', fontSize: '14px', outline: 'none', boxSizing: 'border-box',
  }
  const labelStyle = { display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '16px' }}>
        <div>
          <div style={{ padding: '20px', backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#1f2937', borderBottom: '2px solid #3b82f6', paddingBottom: '8px' }}>
              🚀 排产计算
            </h3>

            <div style={{ marginBottom: '16px' }}>
              <label style={labelStyle}>选择交货计划</label>
              <select style={inputStyle} value={selectedPlanId} onChange={e => handlePlanSelect(e.target.value)}>
                <option value="">请选择交货计划</option>
                {plans.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({(p.lines || []).map(l => l.line_name).join(' + ')})
                  </option>
                ))}
              </select>
            </div>

            {selectedPlan && (
              <div style={{ padding: '12px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb', marginBottom: '16px' }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>📋 计划详情</div>
                <div style={{ fontSize: '12px', color: '#6b7280', lineHeight: '1.8' }}>
                  <div>日期：<b>{selectedPlan.start_date}</b> ~ <b>{selectedPlan.end_date}</b></div>
                  <div style={{ borderTop: '1px solid #e5e7eb', margin: '6px 0' }} />
                  {(selectedPlan.lines || []).map((line, lIdx) => (
                    <div key={lIdx} style={{ marginBottom: '8px' }}>
                      <div style={{ fontWeight: '600', color: LINE_COLORS[lIdx % LINE_COLORS.length] }}>
                        🏭 {line.line_name}
                      </div>
                      {(line.materials || []).map((m, idx) => (
                        <div key={idx} style={{ paddingLeft: '16px', color: MATERIAL_COLORS[idx % MATERIAL_COLORS.length] }}>
                          <span style={{
                            display: 'inline-block', width: '16px', height: '16px', lineHeight: '16px',
                            textAlign: 'center', borderRadius: '3px', fontSize: '11px', fontWeight: '700',
                            color: '#fff', backgroundColor: MATERIAL_COLORS[idx % MATERIAL_COLORS.length],
                            marginRight: '4px',
                          }}>
                            {idx + 1}
                          </span>
                          {m.product_name}
                          <div style={{ paddingLeft: '20px', color: '#9ca3af' }}>库存{m.initial_inventory} / 安全{m.safety_stock} / 产量{m.rated_output}</div>
                          <div style={{ paddingLeft: '20px' }}>总交货量：<b>{m.total_delivery}</b></div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '10px' }}>⚙️ 算法配置</div>
              <div style={{ padding: '12px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <label style={{ ...labelStyle, fontSize: '12px', marginBottom: 0 }}>规避休息日上班权重</label>
                    <span style={{ fontSize: '13px', fontWeight: '600', color: '#3b82f6' }}>{config.avoid_rest_work_weight}</span>
                  </div>
                  <div style={{ height: '28px', display: 'flex', alignItems: 'center' }}>
                    <input type="range" min={0} max={100} step={10} value={config.avoid_rest_work_weight}
                      onChange={e => handleConfigChange('avoid_rest_work_weight', e.target.value)}
                      style={{ width: '100%', height: '6px', appearance: 'none', WebkitAppearance: 'none',
                        background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(config.avoid_rest_work_weight / 100) * 100}%, #e5e7eb ${(config.avoid_rest_work_weight / 100) * 100}%, #e5e7eb 100%)`,
                        borderRadius: '3px', outline: 'none', cursor: 'pointer' }}
                    />
                  </div>
                </div>
                
                <style>{`
                  input[type=range]::-webkit-slider-thumb {
                    -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%;
                    background: #3b82f6; border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.2); cursor: pointer;
                  }
                  input[type=range]::-moz-range-thumb {
                    width: 18px; height: 18px; border-radius: 50%;
                    background: #3b82f6; border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.2); cursor: pointer;
                  }
                `}</style>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={handleCalculate}
                disabled={loading || !selectedPlanId}
                style={{
                  flex: 1, padding: '10px 20px',
                  backgroundColor: loading || !selectedPlanId ? '#9ca3af' : '#3b82f6',
                  color: '#fff', border: 'none', borderRadius: '8px',
                  cursor: loading || !selectedPlanId ? 'not-allowed' : 'pointer',
                  fontSize: '15px', fontWeight: '600',
                }}
              >
                {loading ? '⏳ 计算中...' : '🚀 开始排产'}
              </button>
            </div>

            <div style={{ marginTop: '12px', textAlign: 'center' }}>
              <span
                onClick={() => setDebugMode(!debugMode)}
                style={{
                  fontSize: '12px', opacity: debugMode ? 1 : 0.4, cursor: 'pointer',
                  padding: '2px 8px', borderRadius: '4px',
                  border: debugMode ? '1px solid #3b82f6' : '1px solid transparent',
                  backgroundColor: debugMode ? '#eff6ff' : 'transparent',
                  transition: 'all 0.2s', userSelect: 'none', color: '#3b82f6',
                }}
              >
                🛠 调试模式
              </span>
            </div>

            {debugMode && (
              <div style={{ padding: '12px', backgroundColor: '#f9fafb', borderRadius: '8px', marginTop: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <label style={{ ...labelStyle, fontSize: '12px', marginBottom: 0 }}>求解限时</label>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#3b82f6' }}>{config.max_time_seconds}s</span>
                </div>
                <div style={{ height: '28px', display: 'flex', alignItems: 'center' }}>
                  <input type="range" min={10} max={60} step={10} value={config.max_time_seconds}
                    onChange={e => handleConfigChange('max_time_seconds', e.target.value)}
                    style={{ width: '100%', height: '6px', appearance: 'none', WebkitAppearance: 'none',
                      background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((config.max_time_seconds - 10) / 50) * 100}%, #e5e7eb ${((config.max_time_seconds - 10) / 50) * 100}%, #e5e7eb 100%)`,
                      borderRadius: '3px', outline: 'none', cursor: 'pointer' }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {error && (
            <div style={{
              padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca',
              borderRadius: '8px', color: '#dc2626', fontSize: '14px', marginBottom: '16px',
            }}>
              ❌ {error}
            </div>
          )}

          {loading && (
            <div style={{
              flex: 1, padding: '40px', textAlign: 'center', backgroundColor: '#fff',
              borderRadius: '10px', border: '1px solid #e5e7eb',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>⏳</div>
              <div style={{ fontSize: '16px', color: '#6b7280', display: 'flex', justifyContent: 'center' }}>
                <span>正在计算排产方案{dots}</span>
              </div>
              <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '8px' }}>OR-Tools CP-SAT 多产线求解器优化中</div>
            </div>
          )}

          {!loading && !result && !error && (
            <div style={{
              flex: 1, padding: '60px 40px', textAlign: 'center', backgroundColor: '#fff',
              borderRadius: '10px', border: '1px solid #e5e7eb',
              display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
              <div style={{ fontSize: '18px', color: '#6b7280', marginBottom: '8px' }}>请选择交货计划并开始排产</div>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>先在"交货计划"页面创建计划，然后在此选择并计算</div>
            </div>
          )}

          {result && !loading && (
            <>
              {debugMode && (
                <div style={{
                  padding: '10px 16px', backgroundColor: '#1e293b', borderRadius: '8px',
                  marginBottom: '16px', display: 'flex', gap: '24px', alignItems: 'center',
                  fontFamily: 'monospace', fontSize: '13px',
                }}>
                  <span style={{ color: '#94a3b8' }}>🔍 产线数:</span>
                  <span style={{ color: '#38bdf8', fontWeight: '600' }}>{lineResults.length}</span>
                  {lineResults.map((lr, idx) => (
                    <span key={idx}>
                      <span style={{ color: '#94a3b8' }}>{lr.line_name}:</span>
                      <span style={{ color: lr.solver_status === 'OPTIMAL' ? '#4ade80' : '#fbbf24', fontWeight: '600' }}>
                        {lr.solver_status}
                      </span>
                      <span style={{ color: '#94a3b8' }}> {lr.solve_time}s</span>
                    </span>
                  ))}
                </div>
              )}

              {lineResults.length > 1 && (
                <div style={{
                  marginBottom: '12px',
                  backgroundColor: '#fff', padding: '10px 16px', borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                }}>
                  <div style={{ fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>🏭 选择产线</div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {lineResults.map((lr, idx) => (
                      <button
                        key={idx}
                        onClick={() => { setActiveLineIdx(idx); setActiveProductIdx(0) }}
                        style={{
                          padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: '600',
                          border: `2px solid ${activeLineIdx === idx ? LINE_COLORS[idx % LINE_COLORS.length] : '#e5e7eb'}`,
                          backgroundColor: activeLineIdx === idx ? LINE_COLORS[idx % LINE_COLORS.length] + '15' : '#fff',
                          color: activeLineIdx === idx ? LINE_COLORS[idx % LINE_COLORS.length] : '#6b7280',
                          cursor: 'pointer', transition: 'all 0.2s',
                        }}
                      >
                        {lr.line_name}
                        {lr.solver_status && (
                          <span style={{ marginLeft: '4px', fontSize: '11px' }}>
                            {lr.solver_status === 'OPTIMAL' ? '✅' : '⚠️'}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeLineResult && (
                <>
                  {activeLineResult.num_products > 1 && activeLinePlan && (
                    <div style={{
                      marginBottom: '12px',
                      backgroundColor: '#fff', padding: '10px 16px', borderRadius: '8px',
                      border: '1px solid #e5e7eb',
                    }}>
                      <select
                        value={activeProductIdx}
                        onChange={e => setActiveProductIdx(parseInt(e.target.value))}
                        style={{
                          padding: '6px 12px', border: '1px solid #d1d5db', borderRadius: '6px',
                          fontSize: '13px', outline: 'none', cursor: 'pointer', width: '100%',
                        }}
                      >
                        {(activeLinePlan.materials || []).map((m, idx) => (
                          <option key={idx} value={idx}>
                            {idx + 1} - {m.product_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <ResultTable
                    result={activeLineResult}
                    onExport={() => handleExport(activeLineResult, activeLinePlan)}
                    activeProductIdx={activeProductIdx}
                    lineName={activeLineResult.line_name}
                  />
                  <ResultCharts
                    result={activeLineResult}
                    activeProductIdx={activeProductIdx}
                    materials={activeLinePlan?.materials || []}
                    lineName={activeLineResult.line_name}
                  />
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

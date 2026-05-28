import { useState } from 'react'
import dayjs from 'dayjs'

const defaultProduct = {
  initial_inventory: 500,
  safety_stock: 100,
  rated_output: 200,
  total_delivery: 5000,
}

const defaultParams = {
  product_1: { ...defaultProduct },
  product_2: {
    initial_inventory: 300,
    safety_stock: 50,
    rated_output: 150,
    total_delivery: 3000,
  },
  start_date: dayjs().format('YYYY-MM-DD'),
  end_date: dayjs().add(29, 'day').format('YYYY-MM-DD'),
  holidays: [],
}

const defaultConfig = {
  avoid_rest_work_weight: 50,
  max_consecutive_work_days: 7,
  max_time_seconds: 10,
}

function ProductFields({ label, color, params, onChange }) {
  const inputStyle = {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
  }
  const labelStyle = {
    display: 'block',
    fontSize: '13px',
    fontWeight: '600',
    color: '#374151',
    marginBottom: '4px',
  }
  const fields = [
    { key: 'initial_inventory', label: '初期库存' },
    { key: 'safety_stock', label: '安全库存' },
    { key: 'rated_output', label: '单班额定产量' },
    { key: 'total_delivery', label: '计划总交货量' },
  ]

  return (
    <div style={{ padding: '12px', backgroundColor: `${color}08`, borderRadius: '8px', border: `1px solid ${color}30` }}>
      <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color, fontWeight: '700' }}>{label}</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        {fields.map(f => (
          <div key={f.key}>
            <label style={{ ...labelStyle, fontSize: '12px' }}>{f.label}</label>
            <input
              type="number"
              style={inputStyle}
              value={params[f.key]}
              onChange={e => onChange(f.key, parseFloat(e.target.value))}
              min="0"
              step="1"
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ParameterForm({ onCalculate, loading }) {
  const [params, setParams] = useState(defaultParams)
  const [config, setConfig] = useState(defaultConfig)
  const [showConfig, setShowConfig] = useState(false)

  const handleProductChange = (product, key, value) => {
    setParams(prev => ({
      ...prev,
      [product]: { ...prev[product], [key]: value },
    }))
  }

  const handleParamChange = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }))
  }

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: parseFloat(value) }))
  }

  const handleReset = () => {
    setParams(defaultParams)
    setConfig(defaultConfig)
  }

  const buildApiConfig = () => ({
    rest_day_weight: config.avoid_rest_work_weight,
    max_consecutive_work_days: config.max_consecutive_work_days,
    max_time_seconds: config.max_time_seconds,
  })

  const handleCalculate = () => {
    onCalculate(params, buildApiConfig())
  }

  const inputStyle = {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
  }

  const labelStyle = {
    display: 'block',
    fontSize: '13px',
    fontWeight: '600',
    color: '#374151',
    marginBottom: '4px',
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#fff', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#1f2937', borderBottom: '2px solid #3b82f6', paddingBottom: '8px' }}>
        📋 双物品排产参数
      </h3>

      <ProductFields
        label="物品 1"
        color="#2563eb"
        params={params.product_1}
        onChange={(k, v) => handleProductChange('product_1', k, v)}
      />

      <div style={{ margin: '16px 0' }} />

      <ProductFields
        label="物品 2"
        color="#059669"
        params={params.product_2}
        onChange={(k, v) => handleProductChange('product_2', k, v)}
      />

      <div style={{ margin: '16px 0', borderTop: '1px solid #e5e7eb' }} />

      <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#374151', fontWeight: '600' }}>📅 共享排产日期</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <label style={labelStyle}>排产开始日期</label>
          <input
            type="date"
            style={inputStyle}
            value={params.start_date}
            onChange={e => handleParamChange('start_date', e.target.value)}
          />
        </div>
        <div>
          <label style={labelStyle}>排产结束日期</label>
          <input
            type="date"
            style={inputStyle}
            value={params.end_date}
            onChange={e => handleParamChange('end_date', e.target.value)}
          />
        </div>
      </div>

      <div style={{ marginTop: '16px' }}>
        <button
          onClick={() => setShowConfig(!showConfig)}
          style={{
            background: 'none',
            border: 'none',
            color: '#3b82f6',
            cursor: 'pointer',
            fontSize: '13px',
            padding: 0,
          }}
        >
          {showConfig ? '▼ 隐藏算法配置' : '▶ 显示算法配置'}
        </button>

        {showConfig && (
          <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <label style={{ ...labelStyle, fontSize: '12px', marginBottom: 0 }}>规避休息日上班权重</label>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#3b82f6' }}>{config.avoid_rest_work_weight}</span>
              </div>
              <div style={{ height: '28px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={10}
                  value={config.avoid_rest_work_weight}
                  onChange={e => handleConfigChange('avoid_rest_work_weight', e.target.value)}
                  style={{
                    width: '100%',
                    height: '6px',
                    appearance: 'none',
                    WebkitAppearance: 'none',
                    background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(config.avoid_rest_work_weight / 100) * 100}%, #e5e7eb ${(config.avoid_rest_work_weight / 100) * 100}%, #e5e7eb 100%)`,
                    borderRadius: '3px',
                    outline: 'none',
                    cursor: 'pointer',
                  }}
                />
              </div>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ ...labelStyle, fontSize: '12px', marginBottom: 0 }}>最大连续工作天数</label>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#3b82f6' }}>{config.max_consecutive_work_days}天</span>
              </div>
              <div style={{ position: 'relative', height: '28px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="range"
                  min={3}
                  max={14}
                  step={1}
                  value={config.max_consecutive_work_days}
                  onChange={e => handleConfigChange('max_consecutive_work_days', e.target.value)}
                  style={{
                    width: '100%',
                    height: '6px',
                    appearance: 'none',
                    WebkitAppearance: 'none',
                    background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((config.max_consecutive_work_days - 3) / 11) * 100}%, #e5e7eb ${((config.max_consecutive_work_days - 3) / 11) * 100}%, #e5e7eb 100%)`,
                    borderRadius: '3px',
                    outline: 'none',
                    cursor: 'pointer',
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#9ca3af', marginTop: '2px', padding: '0 2px' }}>
                {[3, 5, 7, 10, 14].map(v => (
                  <span key={v} style={{ color: v === config.max_consecutive_work_days ? '#3b82f6' : '#9ca3af', fontWeight: v === config.max_consecutive_work_days ? '600' : '400' }}>{v}天</span>
                ))}
              </div>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ ...labelStyle, fontSize: '12px', marginBottom: 0 }}>求解限时</label>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#3b82f6' }}>{config.max_time_seconds}s</span>
              </div>
              <div style={{ position: 'relative', height: '28px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="range"
                  min={10}
                  max={60}
                  step={10}
                  value={config.max_time_seconds}
                  onChange={e => handleConfigChange('max_time_seconds', e.target.value)}
                  style={{
                    width: '100%',
                    height: '6px',
                    appearance: 'none',
                    WebkitAppearance: 'none',
                    background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((config.max_time_seconds - 10) / 50) * 100}%, #e5e7eb ${((config.max_time_seconds - 10) / 50) * 100}%, #e5e7eb 100%)`,
                    borderRadius: '3px',
                    outline: 'none',
                    cursor: 'pointer',
                  }}
                />
                <style>{`
                  input[type=range]::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 18px;
                    height: 18px;
                    border-radius: 50%;
                    background: #3b82f6;
                    border: 2px solid #fff;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
                    cursor: pointer;
                  }
                  input[type=range]::-moz-range-thumb {
                    width: 18px;
                    height: 18px;
                    border-radius: 50%;
                    background: #3b82f6;
                    border: 2px solid #fff;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
                    cursor: pointer;
                  }
                `}</style>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#9ca3af', marginTop: '2px', padding: '0 2px' }}>
                {[10, 20, 30, 40, 50, 60].map(v => (
                  <span key={v} style={{ color: v === config.max_time_seconds ? '#3b82f6' : '#9ca3af', fontWeight: v === config.max_time_seconds ? '600' : '400' }}>{v}s</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button
          onClick={handleCalculate}
          disabled={loading}
          style={{
            flex: 1,
            padding: '10px 20px',
            backgroundColor: loading ? '#9ca3af' : '#3b82f6',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '15px',
            fontWeight: '600',
          }}
        >
          {loading ? '⏳ 计算中...' : '🚀 开始排产'}
        </button>
        <button
          onClick={handleReset}
          style={{
            padding: '10px 20px',
            backgroundColor: '#f3f4f6',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          🔄 重置
        </button>
      </div>
    </div>
  )
}

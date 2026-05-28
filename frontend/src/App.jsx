import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import MaterialManagementPage from './pages/MaterialManagement'
import LineManagementPage from './pages/LineManagement'
import DeliveryPlanPage from './pages/DeliveryPlan'
import SchedulingPage from './pages/Scheduling'
import './App.css'

const navItems = [
  { path: '/materials', label: '物料管理', icon: '📦', color: '#3b82f6' },
  { path: '/lines', label: '产线管理', icon: '🏭', color: '#059669' },
  { path: '/delivery-plans', label: '交货计划', icon: '📋', color: '#7c3aed' },
  { path: '/', label: '排产计算', icon: '🚀', color: '#f59e0b' },
]

function Sidebar() {
  return (
    <div style={{
      width: '200px', minHeight: '100vh', backgroundColor: '#1e293b',
      display: 'flex', flexDirection: 'column', flexShrink: 0,
    }}>
      <div style={{
        padding: '20px 16px 16px', borderBottom: '1px solid #334155',
        display: 'flex', alignItems: 'center', gap: '10px',
      }}>
        <span style={{ fontSize: '24px' }}>🏭</span>
        <div>
          <div style={{ color: '#f1f5f9', fontSize: '15px', fontWeight: '700' }}>智能排产</div>
          <div style={{ color: '#64748b', fontSize: '11px' }}>V2.0</div>
        </div>
      </div>

      <nav style={{ padding: '12px 8px', flex: 1 }}>
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '10px 12px', borderRadius: '8px',
              color: isActive ? '#f1f5f9' : '#94a3b8',
              backgroundColor: isActive ? '#334155' : 'transparent',
              textDecoration: 'none', fontSize: '14px', fontWeight: isActive ? '600' : '400',
              transition: 'all 0.2s', marginBottom: '4px',
              borderLeft: isActive ? `3px solid ${item.color}` : '3px solid transparent',
            })}
          >
            <span style={{ fontSize: '16px' }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div style={{
        padding: '12px 16px', borderTop: '1px solid #334155',
        color: '#475569', fontSize: '11px', textAlign: 'center',
      }}>
        OR-Tools CP-SAT 引擎
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f0f2f5' }}>
        <Sidebar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <main style={{ flex: 1, padding: '20px 24px', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
            <Routes>
              <Route path="/" element={<SchedulingPage />} />
              <Route path="/materials" element={<MaterialManagementPage />} />
              <Route path="/lines" element={<LineManagementPage />} />
              <Route path="/delivery-plans" element={<DeliveryPlanPage />} />
            </Routes>
          </main>
          <footer style={{
            textAlign: 'center', padding: '12px', color: '#9ca3af', fontSize: '12px',
            borderTop: '1px solid #e5e7eb', backgroundColor: '#fff',
          }}>
            智能排产系统 V2.0 © 2026 | OR-Tools CP-SAT 约束优化引擎
          </footer>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App

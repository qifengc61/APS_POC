import { useState } from 'react'
import { Layout, Menu, theme, Button, Badge } from 'antd'
import {
  DatabaseOutlined,
  ThunderboltOutlined,
  InboxOutlined,
  UnorderedListOutlined,
  ToolOutlined,
  ApartmentOutlined,
  HomeOutlined,
  CalendarOutlined,
  FileTextOutlined,
  OrderedListOutlined,
  RocketOutlined,
  BarsOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BugOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import LogViewer from '../components/LogViewer'

const { Sider, Header, Content } = Layout

const menuItems = [
  {
    key: 'base-data',
    icon: <DatabaseOutlined />,
    label: '基础数据',
    children: [
      { key: '/materials', icon: <InboxOutlined />, label: '物料管理' },
      { key: '/bom', icon: <UnorderedListOutlined />, label: 'BOM管理' },
      { key: '/resources', icon: <HomeOutlined />, label: '生产资源' },
      { key: '/processes', icon: <ToolOutlined />, label: '工序管理' },
      { key: '/process-routes', icon: <ApartmentOutlined />, label: '工艺路线' },
      { key: '/calendars', icon: <CalendarOutlined />, label: '工作日历' },
      { key: '/incoming-orders', icon: <FileTextOutlined />, label: '来料订单' },
      { key: '/orders', icon: <OrderedListOutlined />, label: '生产订单' },
    ],
  },
  {
    key: 'scheduling',
    icon: <ThunderboltOutlined />,
    label: '智能排产',
    children: [
      { key: '/quick-scheduling', icon: <RocketOutlined />, label: '快速排产' },
      { key: '/scheduling', icon: <BarsOutlined />, label: '作业排产' },
      { key: '/scheduled-orders', icon: <SearchOutlined />, label: '排产结果' },
    ],
  },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [logOpen, setLogOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  const handleMenuClick = ({ key }) => {
    navigate(key)
  }

  const getOpenKeys = () => {
    for (const group of menuItems) {
      if (group.children?.some(child => child.key === location.pathname)) {
        return [group.key]
      }
    }
    return ['scheduling']
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          background: 'linear-gradient(180deg, #0a1628 0%, #132744 100%)',
        }}
        width={220}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}>
          <span style={{ fontSize: collapsed ? 20 : 24 }}>🏭</span>
          {!collapsed && (
            <span style={{
              color: '#fff',
              fontSize: 16,
              fontWeight: 700,
              marginLeft: 10,
              whiteSpace: 'nowrap',
            }}>
              智能排产
            </span>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            background: 'transparent',
            borderRight: 0,
          }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin-left 0.2s' }}>
        <Header style={{
          padding: '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          position: 'sticky',
          top: 0,
          zIndex: 10,
          height: 64,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: 18, cursor: 'pointer', color: '#333' }}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </span>
            <div>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#1e3a5f' }}>
                智能排产系统
              </span>
              <span style={{ fontSize: 12, color: '#8c8c8c', marginLeft: 12 }}>
                基于 Google OR-Tools CP-SAT
              </span>
            </div>
          </div>
          <div>
            <Button
              icon={<BugOutlined />}
              onClick={() => setLogOpen(true)}
              type="text"
              style={{ fontSize: 16 }}
            >
              日志
            </Button>
          </div>
        </Header>
        <Content style={{
          margin: 16,
          padding: 20,
          background: '#f0f2f5',
          minHeight: 'calc(100vh - 64px - 32px)',
        }}>
          <Outlet />
        </Content>
      </Layout>
      <LogViewer open={logOpen} onClose={() => setLogOpen(false)} />
    </Layout>
  )
}

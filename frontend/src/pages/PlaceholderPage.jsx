import { Result } from 'antd'

export default function PlaceholderPage({ title }) {
  return (
    <div style={{ padding: 24 }}>
      <Result
        status="info"
        title={title}
        subTitle="该功能模块正在开发中，敬请期待"
      />
    </div>
  )
}

import { Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { DbConnections } from '@/pages/DbConnections'
import { Landing } from '@/pages/Landing'
import { MetricSetup } from '@/pages/MetricSetup'

function App() {
  return (
    <Routes>
      {/* 랜딩 페이지 - 레이아웃 없이 */}
      <Route path="/" element={<Landing />} />

      {/* 대시보드 */}
      <Route
        path="/dashboard"
        element={
          <Layout>
            <Dashboard />
          </Layout>
        }
      />

      {/* DB 연결 관리 */}
      <Route
        path="/connections"
        element={
          <Layout>
            <DbConnections />
          </Layout>
        }
      />

      {/* DB 연결 설정 - /connections로 리다이렉트 */}
      <Route path="/db-setup" element={<Navigate to="/connections" replace />} />

      {/* 지표 설정 */}
      <Route
        path="/setup"
        element={
          <Layout>
            <MetricSetup />
          </Layout>
        }
      />

      {/* 기본 리다이렉트 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App

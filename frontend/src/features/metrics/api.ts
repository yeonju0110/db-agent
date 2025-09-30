import { apiClient } from '@/lib/api-client'

import {
  type AnomalyItem,
  type ConnectionTestResult,
  type CreateDbConnectionRequest,
  type DbConnectionItem,
  type DbStatusItem,
  type Metric,
  type MetricDetail,
  type MetricListItem,
  type QueryResponse,
  type RecommendationItem,
  type SetupStartResult,
  type SetupStatus,
  type TableAnomalyDetail,
  type TableAnomalyDetection,
  type TableAnomalySummary,
} from './types'

export const metricsApi = {
  // 지표 목록
  list: async (): Promise<{ total: number; items: MetricListItem[] }> => {
    const { data } = await apiClient.get('/api/metrics')
    return data
  },

  // 지표 상세 (히스토리 포함)
  get: async (id: string): Promise<MetricDetail> => {
    const { data } = await apiClient.get(`/api/metrics/${id}`)
    return data
  },

  // 지표 생성
  create: async (payload: {
    natural_query: string
    name?: string
    db_connection_id: string
    related_tables?: string[]
    threshold_enabled?: boolean
    threshold_operator?: string
    threshold_value?: number
  }): Promise<Metric> => {
    const { data } = await apiClient.post('/api/metrics', payload)
    return data
  },

  // 지표 삭제
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/metrics/${id}`)
  },

  // 즉시 질문
  query: async (question: string): Promise<QueryResponse> => {
    const { data } = await apiClient.post('/api/query', { question })
    return data
  },

  // SQL 직접 실행
  executeSql: async (sql: string): Promise<QueryResponse> => {
    const { data } = await apiClient.post('/api/query/execute', { question: sql })
    return data
  },

  // 추천 테이블 목록
  recommendTables: async (
    question: string
  ): Promise<{
    query: string
    recommended_tables: Array<{
      name: string
      description: string
      score: number
      columns_text: string
      common_queries: string[]
      recommendation_reason: string
    }>
    total_count: number
  }> => {
    const { data } = await apiClient.post('/api/query/recommend-tables', { question })
    return data
  },
}

// DB 연결 관리 API
export const dbConnectionsApi = {
  // DB 연결 목록
  list: async (): Promise<{ total: number; items: DbConnectionItem[] }> => {
    const { data } = await apiClient.get('/api/db-connections')
    return data
  },

  // DB 연결 생성
  create: async (payload: CreateDbConnectionRequest): Promise<DbConnectionItem> => {
    const { data } = await apiClient.post('/api/db-connections', payload)
    return data
  },

  // DB 연결 상세
  get: async (id: string): Promise<DbConnectionItem> => {
    const { data } = await apiClient.get(`/api/db-connections/${id}`)
    return data
  },

  // 연결 테스트
  test: async (id: string): Promise<ConnectionTestResult> => {
    const { data } = await apiClient.post(`/api/db-connections/${id}/test`)
    return data
  },

  // 설정 시작
  startSetup: async (id: string): Promise<SetupStartResult> => {
    const { data } = await apiClient.post(`/api/db-connections/${id}/setup`)
    return data
  },

  // 설정 상태 조회
  getSetupStatus: async (id: string): Promise<SetupStatus> => {
    const { data } = await apiClient.get(`/api/db-connections/${id}/setup-status`)
    return data
  },

  // DB 연결 수정
  update: async (id: string, payload: CreateDbConnectionRequest): Promise<DbConnectionItem> => {
    const { data } = await apiClient.put(`/api/db-connections/${id}`, payload)
    return data
  },

  // DB 연결 삭제
  delete: async (id: string): Promise<{ message: string }> => {
    const { data } = await apiClient.delete(`/api/db-connections/${id}`)
    return data
  },
}

// 대시보드 API
export const dashboardApi = {
  // 이상징후 목록
  getAnomalies: async (
    resolved = false,
    limit = 10
  ): Promise<{ total: number; items: AnomalyItem[] }> => {
    const { data } = await apiClient.get(
      `/api/dashboard/anomalies?resolved=${resolved}&limit=${limit}`
    )
    return data
  },

  // DB 상태
  getDbStatus: async (): Promise<{ items: DbStatusItem[] }> => {
    const { data } = await apiClient.get('/api/dashboard/db-status')
    return data
  },

  // 권장사항
  getRecommendations: async (limit = 10): Promise<{ items: RecommendationItem[] }> => {
    const { data } = await apiClient.get(`/api/dashboard/recommendations?limit=${limit}`)
    return data
  },
}

// 테이블 이상치 감지 API
export const tableAnomaliesApi = {
  // 테이블 이상치 목록
  list: async (
    tableName?: string,
    status?: string
  ): Promise<{ total: number; items: TableAnomalyDetection[] }> => {
    const params = new URLSearchParams()
    if (tableName) params.append('table_name', tableName)
    if (status) params.append('status', status)

    const { data } = await apiClient.get(`/api/table-anomalies?${params.toString()}`, {
      headers: {
        'x-tenant-id': 'default',
      },
    })
    return data
  },

  // 테이블 이상치 수동 검사
  scan: async (
    tableName: string
  ): Promise<{ success: boolean; data: TableAnomalyDetection; message: string }> => {
    const { data } = await apiClient.post('/api/table-anomalies/scan', null, {
      params: { table_name: tableName },
      headers: {
        'x-tenant-id': 'default',
      },
    })
    return data
  },

  // 이상치 상세 정보
  getDetails: async (
    detectionId: string
  ): Promise<{ total: number; items: TableAnomalyDetail[] }> => {
    const { data } = await apiClient.get(`/api/table-anomalies/${detectionId}/details`, {
      headers: {
        'x-tenant-id': 'default',
      },
    })
    return data
  },

  // 이상치 확인 처리
  acknowledge: async (
    detectionId: string
  ): Promise<{ success: boolean; message: string; data: TableAnomalyDetection }> => {
    const { data } = await apiClient.post(`/api/table-anomalies/${detectionId}/acknowledge`, null, {
      headers: {
        'x-tenant-id': 'default',
      },
    })
    return data
  },

  // 이상치 요약 정보
  getSummary: async (): Promise<TableAnomalySummary> => {
    const { data } = await apiClient.get('/api/table-anomalies/summary', {
      headers: {
        'x-tenant-id': 'default',
      },
    })
    return data
  },
}

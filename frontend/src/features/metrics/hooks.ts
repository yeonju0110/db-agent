import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { dashboardApi, dbConnectionsApi, metricsApi, tableAnomaliesApi } from './api'
import { type CreateDbConnectionRequest } from './types'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: metricsApi.list,
    refetchInterval: 10000, // 10초마다 새로고침
    staleTime: 0, // 데이터를 즉시 stale로 처리
  })
}

export function useMetric(id: string | undefined) {
  return useQuery({
    queryKey: ['metrics', id],
    queryFn: () => metricsApi.get(id!),
    enabled: !!id,
    refetchInterval: 10000, // 10초마다 새로고침
    staleTime: 0, // 데이터를 즉시 stale로 처리
  })
}

export function useCreateMetric() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: metricsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
    },
  })
}

export function useDeleteMetric() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: metricsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
    },
  })
}

export function useQueryTest() {
  return useMutation({
    mutationFn: metricsApi.query,
  })
}

export function useExecuteSql() {
  return useMutation({
    mutationFn: metricsApi.executeSql,
  })
}

export function useRecommendTables() {
  return useMutation({
    mutationFn: metricsApi.recommendTables,
  })
}

// 대시보드 hooks
export function useAnomalies(resolved = false, limit = 10) {
  return useQuery({
    queryKey: ['anomalies', resolved, limit],
    queryFn: () => dashboardApi.getAnomalies(resolved, limit),
    refetchInterval: 30000, // 30초마다 새로고침
  })
}

export function useDbStatus() {
  return useQuery({
    queryKey: ['db-status'],
    queryFn: dashboardApi.getDbStatus,
    refetchInterval: 10000, // 10초마다 새로고침
  })
}

export function useRecommendations(limit = 10) {
  return useQuery({
    queryKey: ['recommendations', limit],
    queryFn: () => dashboardApi.getRecommendations(limit),
    refetchInterval: 60000, // 1분마다 새로고침
  })
}

// DB 연결 관리 hooks
export function useDbConnections() {
  return useQuery({
    queryKey: ['db-connections'],
    queryFn: dbConnectionsApi.list,
  })
}

export function useDbConnection(id: string | undefined) {
  return useQuery({
    queryKey: ['db-connections', id],
    queryFn: () => dbConnectionsApi.get(id!),
    enabled: !!id,
  })
}

export function useCreateDbConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: dbConnectionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['db-connections'] })
    },
  })
}

export function useTestConnection() {
  return useMutation({
    mutationFn: dbConnectionsApi.test,
  })
}

export function useStartSetup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: dbConnectionsApi.startSetup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['db-connections'] })
    },
  })
}

export function useSetupStatus(connectionId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['setup-status', connectionId],
    queryFn: () => dbConnectionsApi.getSetupStatus(connectionId!),
    enabled: !!connectionId && enabled,
    refetchInterval: (data) => {
      // 설정 완료 또는 실패 시 폴링 중단
      if (data?.status === 'success' || data?.status === 'error') {
        return false
      }
      return 10000 // 10초마다 폴링
    },
  })
}

export function useUpdateDbConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CreateDbConnectionRequest }) =>
      dbConnectionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['db-connections'] })
    },
  })
}

export function useDeleteDbConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: dbConnectionsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['db-connections'] })
    },
  })
}

// 테이블 이상치 감지 훅들
export function useTableAnomalies(tableName?: string, status?: string) {
  return useQuery({
    queryKey: ['table-anomalies', tableName, status],
    queryFn: () => tableAnomaliesApi.list(tableName, status),
    refetchInterval: 60000, // 1분마다 새로고침
  })
}

export function useScanTableAnomalies() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tableAnomaliesApi.scan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['table-anomalies'] })
    },
  })
}

export function useAnomalyDetails(detectionId: string) {
  return useQuery({
    queryKey: ['anomaly-details', detectionId],
    queryFn: () => tableAnomaliesApi.getDetails(detectionId),
    enabled: !!detectionId,
  })
}

export function useAcknowledgeAnomaly() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: tableAnomaliesApi.acknowledge,
    onSuccess: (_, detectionId) => {
      queryClient.invalidateQueries({ queryKey: ['table-anomalies'] })
      queryClient.invalidateQueries({ queryKey: ['anomalies'] })
      queryClient.invalidateQueries({ queryKey: ['anomaly-summary'] })
      queryClient.invalidateQueries({ queryKey: ['anomaly-details', detectionId] })
    },
  })
}

export function useAnomalySummary() {
  return useQuery({
    queryKey: ['anomaly-summary'],
    queryFn: tableAnomaliesApi.getSummary,
    refetchInterval: 60000, // 1분마다 새로고침
  })
}

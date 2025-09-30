import { Activity, CheckCircle, Clock, Pause, Play, RotateCcw, XCircle } from 'lucide-react'

import React, { useEffect, useState } from 'react'

import { apiClient } from '@/lib/api-client'

interface SchedulerStatusData {
  is_running: boolean
  start_time: string | null
  interval_minutes: number
  active_metrics_count: number
  uptime_seconds: number
}

interface SchedulerStatusProps {
  className?: string
}

export const SchedulerStatus: React.FC<SchedulerStatusProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<SchedulerStatusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchStatus = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/scheduler/status')
      setStatus(response.data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류')
    } finally {
      setLoading(false)
    }
  }

  const executeAction = async (action: string, intervalMinutes?: number) => {
    try {
      setActionLoading(action)

      if (action === 'start' || action === 'restart') {
        await apiClient.post(`/api/scheduler/${action}`, {
          interval_minutes: intervalMinutes || 60,
        })
      } else {
        await apiClient.post(`/api/scheduler/${action}`)
      }

      // 상태 새로고침
      await fetchStatus()
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err as Error)?.message ||
        '알 수 없는 오류'
      setError(errorMessage)
    } finally {
      setActionLoading(null)
    }
  }

  const executeAllMetrics = async () => {
    try {
      setActionLoading('execute-all')

      await apiClient.post('/api/scheduler/execute-all')

      // 상태 새로고침
      await fetchStatus()
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err as Error)?.message ||
        '알 수 없는 오류'
      setError(errorMessage)
    } finally {
      setActionLoading(null)
    }
  }

  useEffect(() => {
    fetchStatus()
    // 30초마다 상태 새로고침
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div
        className={`flex min-h-[180px] items-center justify-center rounded-lg border bg-white p-4 ${className}`}
      >
        <div className="flex w-full items-center justify-center">
          <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <span className="ml-2 text-xs text-gray-600">로딩 중...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div
        className={`flex min-h-[180px] flex-col items-center justify-center rounded-lg border bg-white p-4 ${className}`}
      >
        <div className="mb-2 flex items-center text-red-600">
          <XCircle className="mr-1 h-4 w-4" />
          <span className="text-xs">오류: {error}</span>
        </div>
        <button
          aria-label="상태 새로고침"
          onClick={fetchStatus}
          className="mt-2 rounded bg-red-100 px-2 py-1 text-xs text-red-700 hover:bg-red-200"
        >
          다시 시도
        </button>
      </div>
    )
  }

  if (!status) return null

  return (
    <div className={`rounded-lg border bg-white p-4 ${className}`}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">스케줄러 상태</h3>
        <div className="flex items-center">
          {status.is_running ? (
            <div className="flex items-center text-green-600">
              <div className="mr-2 h-2 w-2 animate-pulse rounded-full bg-green-500"></div>
              <CheckCircle className="mr-1 h-4 w-4" />
              <span className="text-xs font-medium">실행 중</span>
            </div>
          ) : (
            <div className="flex items-center text-red-600">
              <div className="mr-2 h-2 w-2 rounded-full bg-red-500"></div>
              <XCircle className="mr-1 h-4 w-4" />
              <span className="text-xs font-medium">중지됨</span>
            </div>
          )}
        </div>
      </div>

      <div className="mb-4 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center text-gray-600">
            <Clock className="mr-1 h-3 w-3" />
            <span>실행 간격</span>
          </div>
          <span className="font-medium">{status.interval_minutes}분마다</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center text-gray-600">
            <Activity className="mr-1 h-3 w-3" />
            <span>활성 지표</span>
          </div>
          <span className="font-medium">{status.active_metrics_count}개</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {!status.is_running ? (
          <button
            onClick={() => executeAction('start', 60)}
            disabled={actionLoading === 'start'}
            className="flex items-center rounded bg-green-600 px-1 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50"
          >
            <Play className="mr-1 h-3 w-3" />
            {actionLoading === 'start' ? '시작 중...' : '시작'}
          </button>
        ) : (
          <div className="flex flex-row flex-wrap gap-1">
            <button
              onClick={() => executeAction('stop')}
              disabled={actionLoading === 'stop'}
              className="flex min-h-[28px] min-w-[56px] items-center justify-center rounded bg-red-100 px-2 py-1 text-xs text-red-700 hover:bg-red-200 disabled:opacity-50"
              style={{ minWidth: 56, minHeight: 28 }}
            >
              <Pause className="mr-1 h-3 w-3" />
              {actionLoading === 'stop' ? '중지중' : '중지'}
            </button>
            <button
              onClick={() => executeAction('restart', 60)}
              disabled={actionLoading === 'restart'}
              className="flex min-h-[28px] min-w-[56px] items-center justify-center rounded bg-blue-100 px-2 py-1 text-xs text-blue-700 hover:bg-blue-200 disabled:opacity-50"
              style={{ minWidth: 56, minHeight: 28 }}
            >
              <RotateCcw className="mr-1 h-3 w-3" />
              {actionLoading === 'restart' ? '재시작중' : '재시작'}
            </button>
            <button
              onClick={executeAllMetrics}
              disabled={actionLoading === 'execute-all'}
              className="flex min-h-[28px] min-w-[56px] items-center justify-center rounded bg-purple-100 px-2 py-1 text-xs text-purple-700 hover:bg-purple-200 disabled:opacity-50"
              style={{ minWidth: 56, minHeight: 28 }}
            >
              <Activity className="mr-1 h-3 w-3" />
              {actionLoading === 'execute-all' ? '실행중' : '실행'}
            </button>
            <button
              onClick={fetchStatus}
              className="flex min-h-[28px] min-w-[56px] items-center justify-center rounded bg-gray-100 px-2 py-1 text-xs text-gray-700 hover:bg-gray-200"
              style={{ minWidth: 56, minHeight: 28 }}
            >
              <RotateCcw className="mr-1 h-3 w-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

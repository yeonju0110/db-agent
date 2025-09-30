import { useEffect, useMemo, useState } from 'react'

import { useMetrics, useScanTableAnomalies, useTableAnomalies } from '@/features/metrics/hooks'
import { type TableAnomalyDetection } from '@/features/metrics/types'
import { formatUTCToKST } from '@/lib/utils'

interface TableAnomalyDetectionProps {
  className?: string
}

export function TableAnomalyDetection({ className = '' }: TableAnomalyDetectionProps) {
  // 모니터링 지표에서 관련 테이블들을 추출
  const { data: metricsData } = useMetrics()

  // 모니터링 중인 테이블 목록 추출
  const monitoredTables = useMemo(() => {
    if (!metricsData?.items) return []

    const tables = new Set<string>()
    metricsData.items.forEach((metric) => {
      // Step1에서 사용자가 선택한 테이블 정보 사용
      if (metric.related_tables && Array.isArray(metric.related_tables)) {
        metric.related_tables.forEach((table) => {
          // 스키마명 제거 (예: "public.orders" -> "orders")
          const tableName = table.split('.').pop()?.toLowerCase() || table.toLowerCase()
          tables.add(tableName)
        })
      }
    })

    return Array.from(tables).sort()
  }, [metricsData])

  const [selectedTable, setSelectedTable] = useState(() => monitoredTables[0] ?? '')

  useEffect(() => {
    if (monitoredTables.length > 0 && !monitoredTables.includes(selectedTable)) {
      setSelectedTable(monitoredTables[0])
    }
  }, [monitoredTables, selectedTable])

  // 모든 테이블의 이상치 데이터를 가져옴 (테이블 필터 없이)
  const { data: anomaliesData, isLoading } = useTableAnomalies()
  const scanMutation = useScanTableAnomalies()

  const handleScan = async () => {
    try {
      await scanMutation.mutateAsync(selectedTable)
    } catch (error) {
      console.error('테이블 검사 실패:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'error':
        return 'border-red-200 bg-red-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      default:
        return 'border-green-200 bg-green-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'error':
        return 'ri-close-circle-fill text-red-600'
      case 'warning':
        return 'ri-error-warning-fill text-yellow-600'
      default:
        return 'ri-check-circle-fill text-green-600'
    }
  }

  // 선택된 테이블의 최신 이상치 데이터 찾기
  const latestAnomaly = anomaliesData?.items?.find(
    (anomaly) => anomaly.table_name === selectedTable
  )

  return (
    <div className={`rounded-lg border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">테이블 이상치 감지</h3>
        <div className="flex items-center space-x-2">
          <select
            value={selectedTable}
            onChange={(e) => setSelectedTable(e.target.value)}
            className="rounded border border-gray-300 px-3 py-1 pr-8 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            {monitoredTables.length > 0 ? (
              monitoredTables.map((table) => (
                <option key={table} value={table}>
                  {table === 'users' && '사용자 테이블'}
                  {table === 'orders' && '주문 테이블'}
                  {table === 'products' && '상품 테이블'}
                  {table === 'logs' && '로그 테이블'}
                  {!['users', 'orders', 'products', 'logs'].includes(table) && `${table} 테이블`}
                </option>
              ))
            ) : (
              <option value="">모니터링 중인 테이블이 없습니다</option>
            )}
          </select>
          <button
            onClick={handleScan}
            disabled={scanMutation.isPending}
            className="inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap text-gray-700 transition-colors hover:bg-gray-100 disabled:text-gray-400"
          >
            {scanMutation.isPending ? (
              <div className="mr-1 h-4 w-4 animate-spin rounded-full border-b-2 border-blue-600"></div>
            ) : (
              <i className="ri-search-line mr-1"></i>
            )}
            검사
          </button>
        </div>
      </div>

      {monitoredTables.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-gray-500">
          <div className="text-center">
            <i className="ri-database-line mb-2 text-4xl"></i>
            <p>모니터링 중인 테이블이 없습니다</p>
            <p className="text-sm">Step1에서 지표를 설정하면 관련 테이블이 표시됩니다</p>
          </div>
        </div>
      ) : isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
            <p className="text-gray-500">로딩 중...</p>
          </div>
        </div>
      ) : latestAnomaly ? (
        <div className={`mb-4 rounded-lg border-2 p-4 ${getStatusColor(latestAnomaly.status)}`}>
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <i className={getStatusIcon(latestAnomaly.status)}></i>
              <span className="font-medium text-gray-900">
                {selectedTable === 'users' && '사용자 테이블'}
                {selectedTable === 'orders' && '주문 테이블'}
                {selectedTable === 'products' && '상품 테이블'}
                {selectedTable === 'logs' && '로그 테이블'}
              </span>
            </div>
            <span className="text-xs text-gray-500">
              마지막 검사: {formatUTCToKST(latestAnomaly.detected_at)}
            </span>
          </div>

          <div className="mb-4 grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-lg font-bold text-gray-900">
                {latestAnomaly.total_records.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">총 레코드</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">
                {latestAnomaly.duplicate_count}
              </div>
              <div className="text-xs text-gray-500">중복</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-yellow-600">{latestAnomaly.null_count}</div>
              <div className="text-xs text-gray-500">NULL</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-orange-600">{latestAnomaly.anomaly_count}</div>
              <div className="text-xs text-gray-500">이상치</div>
            </div>
          </div>

          {/* 간단한 이상치 유형 표시 */}
          <div className="space-y-2">
            <h5 className="mb-3 text-sm font-medium text-gray-900">이상치 유형별 현황:</h5>
            <div className="grid grid-cols-1 gap-2">
              {latestAnomaly.null_count > 0 && (
                <div className="flex items-center justify-between rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-yellow-600">
                  <div className="flex items-center space-x-3">
                    <i className="ri-information-fill text-sm"></i>
                    <div>
                      <div className="text-sm font-medium">NULL 값</div>
                      <div className="text-xs opacity-75">필수 필드에 NULL 값 존재</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="rounded-full bg-white/50 px-2 py-1 text-sm font-bold">
                      {latestAnomaly.null_count}건
                    </span>
                    <button className="inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap text-gray-700 opacity-75 transition-colors hover:bg-gray-100 hover:opacity-100 disabled:text-gray-400">
                      <i className="ri-eye-line"></i>
                    </button>
                  </div>
                </div>
              )}

              {latestAnomaly.duplicate_count > 0 && (
                <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 p-3 text-red-600">
                  <div className="flex items-center space-x-3">
                    <i className="ri-alert-fill text-sm"></i>
                    <div>
                      <div className="text-sm font-medium">중복 데이터</div>
                      <div className="text-xs opacity-75">동일한 키를 가진 중복 레코드</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="rounded-full bg-white/50 px-2 py-1 text-sm font-bold">
                      {latestAnomaly.duplicate_count}건
                    </span>
                    <button className="inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap text-gray-700 opacity-75 transition-colors hover:bg-gray-100 hover:opacity-100 disabled:text-gray-400">
                      <i className="ri-eye-line"></i>
                    </button>
                  </div>
                </div>
              )}

              {latestAnomaly.anomaly_count === 0 && (
                <div className="flex items-center justify-between rounded-lg border border-green-200 bg-green-50 p-3 text-green-600">
                  <div className="flex items-center space-x-3">
                    <i className="ri-check-fill text-sm"></i>
                    <div>
                      <div className="text-sm font-medium">정상</div>
                      <div className="text-xs opacity-75">이상치가 발견되지 않았습니다</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="rounded-full bg-white/30 px-2 py-1 text-sm font-bold">
                      0건
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 border-t border-gray-200 pt-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">전체 이상치:</span>
                <span
                  className={`text-sm font-bold ${
                    latestAnomaly.status === 'error'
                      ? 'text-red-600'
                      : latestAnomaly.status === 'warning'
                        ? 'text-yellow-600'
                        : 'text-green-600'
                  }`}
                >
                  {latestAnomaly.anomaly_count}건
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <div
                  className={`rounded-full px-2 py-1 text-xs font-medium ${
                    latestAnomaly.status === 'error'
                      ? 'border-red-200 bg-red-50 text-red-600'
                      : latestAnomaly.status === 'warning'
                        ? 'border-yellow-200 bg-yellow-50 text-yellow-600'
                        : 'border-green-200 bg-green-50 text-green-600'
                  }`}
                >
                  {latestAnomaly.status === 'error'
                    ? '높음'
                    : latestAnomaly.status === 'warning'
                      ? '보통'
                      : '낮음'}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex h-32 items-center justify-center text-gray-500">
          <div className="text-center">
            <i className="ri-database-line mb-2 text-4xl"></i>
            <p>데이터가 없습니다</p>
            <p className="text-sm">검사 버튼을 클릭하여 이상치를 확인하세요</p>
          </div>
        </div>
      )}

      {/* 자동 검사 설정 */}
      <div className="rounded-lg bg-blue-50 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <i className="ri-time-line text-blue-600"></i>
            <span className="text-sm font-medium text-blue-900">자동 검사</span>
          </div>
          <button className="inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap text-blue-700 transition-colors hover:bg-blue-100 disabled:text-gray-400">
            <i className="ri-settings-line mr-1"></i>설정
          </button>
        </div>
        <p className="mt-1 text-xs text-blue-700">
          매 시간마다 자동으로 데이터 이상치를 검사합니다.
        </p>
      </div>
    </div>
  )
}

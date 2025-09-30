import { useQueryClient } from '@tanstack/react-query'

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { CategoryChart } from '@/components/ui/CategoryChart'
import { MetricChart } from '@/components/ui/MetricChart'
import { SchedulerStatus } from '@/components/ui/SchedulerStatus'
import { TableAnomalyDetection } from '@/components/ui/TableAnomalyDetection'
import { useDbStatus, useMetric, useMetrics } from '@/features/metrics/hooks'
import { type MetricListItem } from '@/features/metrics/types'
import { formatUTCToKST } from '@/lib/utils'

export function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedMetricId, setSelectedMetricId] = useState<string>()
  const [timeRange, setTimeRange] = useState('24h')

  const { data: metricsData, isLoading: isLoadingMetrics } = useMetrics()
  const { data: metricDetail } = useMetric(selectedMetricId)
  const { data: dbStatusData } = useDbStatus()

  // 첫 번째 지표 자동 선택
  useEffect(() => {
    if (!selectedMetricId && metricsData?.items.length) {
      setSelectedMetricId(metricsData.items[0].id)
    }
  }, [metricsData, selectedMetricId])

  // 새로고침 함수
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['metrics'] })
    queryClient.invalidateQueries({ queryKey: ['db-status'] })
    if (selectedMetricId) {
      queryClient.invalidateQueries({ queryKey: ['metrics', selectedMetricId] })
    }
  }

  if (isLoadingMetrics) {
    return <div className="flex flex-1 items-center justify-center">로딩 중...</div>
  }

  // 지표 상태 계산 함수
  const getMetricStatus = (metric: MetricListItem): 'normal' | 'warning' | 'error' => {
    if (metric.latest_value === '이상') {
      return 'error'
    }
    if (metric.change_rate) {
      const rate = parseFloat(metric.change_rate.replace('%', '').replace('+', ''))
      if (rate < -20) return 'warning'
      if (rate > 50) return 'warning'
    }
    return 'normal'
  }

  const getChangeRate = (metric: MetricListItem): string | null => {
    return metric.change_rate || null
  }

  const getMetricIcon = (metric: MetricListItem): string => {
    if (metric.name?.includes('상태') || metric.name?.includes('카테고리')) {
      return 'ri-pie-chart-line'
    }
    if (metric.name?.includes('시스템') || metric.name?.includes('체크')) {
      return 'ri-checkbox-circle-line'
    }
    return 'ri-line-chart-line'
  }

  const getMetricType = (metric: {
    history?: Array<{ result_type?: string; result_data?: Array<Record<string, unknown>> | null }>
    metric?: { name?: string }
  }): 'single_value' | 'category' | 'status' => {
    if (!metric?.history?.[0]) return 'single_value'
    const latestHistory = metric.history[0]
    if (
      latestHistory.result_type === 'multiple_rows' &&
      latestHistory.result_data &&
      latestHistory.result_data.length > 0
    ) {
      const firstItem = latestHistory.result_data[0]
      if (firstItem && (firstItem.category || firstItem.status || firstItem.name)) {
        return 'category'
      }
    }
    if (metric.metric?.name?.includes('상태')) return 'status'
    if (metric.metric?.name?.includes('카테고리')) return 'category'
    return 'single_value'
  }

  const convertMetricDetailForType = (metricDetail: {
    history?: Array<{
      result_type?: string
      result_data?: Array<Record<string, string | number>> | null
    }>
    metric?: { name?: string }
  }) => ({
    history: metricDetail.history?.map((h) => ({
      result_type: h.result_type,
      result_data: h.result_data,
    })),
    metric: metricDetail.metric,
  })

  return (
    <div className="h-screen-96 flex w-full overflow-hidden bg-gray-50">
      {/* Sidebar - 독립 스크롤 */}
      <div className="flex w-80 flex-shrink-0 flex-col border-r border-gray-200 bg-white">
        {/* 상단 고정 영역 */}
        <div className="flex flex-shrink-0 items-center justify-between p-6 pb-0">
          <h2 className="text-lg font-semibold text-gray-900">모니터링 지표</h2>
          <button
            onClick={() => navigate('/setup')}
            className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium whitespace-nowrap text-white transition-colors hover:bg-blue-700 disabled:bg-blue-300"
          >
            <i className="ri-add-line mr-1"></i>추가
          </button>
        </div>

        {/* 중간 스크롤 영역 - 지표 목록 */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {(metricsData?.items || []).map((metric) => {
              const status = getMetricStatus(metric)
              const changeRate = getChangeRate(metric)
              const isSelected = metric.id === selectedMetricId

              return (
                <div
                  key={metric.id}
                  onClick={() => setSelectedMetricId(metric.id)}
                  className={`cursor-pointer p-3 transition-all ${
                    isSelected ? 'rounded-lg bg-blue-50' : 'rounded-lg hover:bg-gray-50'
                  }`}
                >
                  <div className="mb-2 flex items-center">
                    <i
                      className={`mr-2 text-gray-400 ${
                        getMetricIcon(metric) === 'ri-pie-chart-line'
                          ? 'ri-time-line'
                          : getMetricIcon(metric) === 'ri-checkbox-circle-line'
                            ? 'ri-checkbox-circle-line'
                            : 'ri-line-chart-line'
                      }`}
                    ></i>
                    <span className="text-sm font-medium text-gray-900">{metric.name}</span>
                    {status !== 'normal' && (
                      <div
                        className={`ml-auto flex h-4 w-4 items-center justify-center rounded-full ${
                          status === 'warning' ? 'bg-yellow-100' : 'bg-red-100'
                        }`}
                      >
                        <i
                          className={`text-xs ${
                            status === 'warning'
                              ? 'ri-error-warning-line text-yellow-600'
                              : 'ri-close-line text-red-600'
                          }`}
                        ></i>
                      </div>
                    )}
                  </div>
                  <div className="mb-1">
                    {getMetricIcon(metric) === 'ri-checkbox-circle-line' ? (
                      <span
                        className={`text-sm font-medium ${
                          metric.latest_value === '이상' ? 'text-red-600' : 'text-gray-900'
                        }`}
                      >
                        {metric.latest_value || '정상'}
                      </span>
                    ) : getMetricIcon(metric) === 'ri-pie-chart-line' ? (
                      <div className="flex items-baseline">
                        <span className="text-2xl font-bold text-gray-900">
                          {metric.latest_value || '0'}
                        </span>
                        <span className="ml-1 text-sm text-gray-500">항목</span>
                      </div>
                    ) : (
                      <div className="flex items-baseline justify-between">
                        <span className="text-2xl font-bold text-gray-900">
                          {metric.latest_value || '0'}
                        </span>
                        {changeRate && (
                          <span
                            className={`rounded px-1.5 py-0.5 text-xs ${
                              changeRate.startsWith('+')
                                ? 'bg-green-100 text-green-600'
                                : changeRate.startsWith('-')
                                  ? 'bg-red-100 text-red-600'
                                  : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {changeRate}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {metric.latest_executed_at
                      ? formatUTCToKST(metric.latest_executed_at, {
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : '실행 대기중'}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 하단 고정 영역 */}
        <div className="flex-shrink-0 space-y-2 border-t border-gray-200 p-4">
          {/* DB 연결 상태 */}
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <h3 className="mb-2 flex items-center text-sm font-semibold text-gray-900">
              <i className="ri-database-2-line mr-1 text-blue-600"></i>
              DB 연결 상태
            </h3>
            <div className="space-y-2">
              {(dbStatusData?.items || []).map((db, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between rounded-lg p-2 ${
                    db.status === 'normal' ? 'bg-green-50' : 'bg-red-50'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        db.status === 'normal' ? 'bg-green-500' : 'animate-pulse bg-red-500'
                      }`}
                    ></div>
                    <div>
                      <span className="text-xs font-medium text-gray-900">{db.name}</span>
                      <div className="text-xs text-gray-500">{db.type}</div>
                    </div>
                  </div>
                  <span
                    className={`text-xs font-medium ${
                      db.status === 'normal' ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {db.status === 'normal' ? `정상` : '오류'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 스케줄러 상태 */}
          <SchedulerStatus className="border border-gray-200 bg-transparent p-0 shadow-none" />

          {/* 요금제 정보 */}
          <div className="rounded-lg bg-blue-50 p-4">
            <div className="mb-2 flex items-center space-x-2">
              <i className="ri-information-line text-blue-600"></i>
              <span className="text-sm font-medium text-blue-900">요금제 정보</span>
            </div>
            <p className="text-xs text-blue-700">
              현재 {metricsData?.items.length || 0}개 / 최대 10개 지표 사용 중
            </p>
            <div className="mt-2 h-2 rounded-full bg-blue-200">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all"
                style={{
                  width: `${Math.min(((metricsData?.items.length || 0) / 10) * 100, 100)}%`,
                }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - 독립 스크롤 */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* 헤더 */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {metricDetail?.metric.name || '지표를 선택하세요'}
              </h1>
              {metricDetail && (
                <div
                  className={`rounded-full px-3 py-1 text-sm font-medium ${
                    getMetricType(convertMetricDetailForType(metricDetail)) === 'category'
                      ? 'bg-yellow-100 text-yellow-600'
                      : getMetricType(convertMetricDetailForType(metricDetail)) === 'status'
                        ? 'bg-red-100 text-red-600'
                        : 'bg-green-100 text-green-600'
                  }`}
                >
                  <i
                    className={`mr-1 ${
                      getMetricType(convertMetricDetailForType(metricDetail)) === 'category'
                        ? 'ri-pie-chart-line'
                        : getMetricType(convertMetricDetailForType(metricDetail)) === 'status'
                          ? 'ri-checkbox-circle-line'
                          : 'ri-line-chart-line'
                    }`}
                  ></i>
                  {getMetricType(convertMetricDetailForType(metricDetail)) === 'category'
                    ? '카테고리형'
                    : getMetricType(convertMetricDetailForType(metricDetail)) === 'status'
                      ? '상태형'
                      : '수치형'}
                </div>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 pr-8 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="1h">최근 1시간</option>
                <option value="24h">최근 24시간</option>
                <option value="7d">최근 7일</option>
                <option value="30d">최근 30일</option>
              </select>
              <button
                onClick={handleRefresh}
                className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium whitespace-nowrap text-gray-700 transition-colors hover:bg-gray-50 disabled:bg-gray-100"
              >
                <i className="ri-refresh-line mr-1"></i>새로고침
              </button>
            </div>
          </div>

          {/* SQL 쿼리 표시 */}
          {metricDetail && (
            <div className="mb-4 rounded-lg border border-gray-200 bg-white px-1 shadow-sm">
              <div className="flex flex-col px-3 py-3">
                {/* 자연어 쿼리 */}
                <div className="mb-3 flex items-center">
                  <span className="mr-2 text-xs font-medium text-gray-700">자연어 쿼리</span>
                  <span className="max-w-xs truncate text-xs text-gray-500">
                    "{metricDetail.metric.natural_query}"
                  </span>
                </div>
                {/* SQL 영역 */}
                <div className="flex flex-col gap-1">
                  <div className="relative mb-1 flex">
                    <span className="mt-1 mr-2 text-center text-xs font-medium text-gray-700">
                      변환된 SQL
                    </span>
                    <div className="relative flex-1">
                      <pre
                        className="mb-0 flex-1 rounded bg-gray-700 px-2 py-2 font-mono text-xs break-all whitespace-pre-wrap text-green-300"
                        style={{ minWidth: 0, marginBottom: 0 }}
                      >
                        {metricDetail.metric.sql_query ||
                          `SELECT COUNT(*) as count FROM users WHERE created_at >= CURRENT_DATE`}
                      </pre>
                    </div>
                    <button
                      className="absolute top-0 right-0 rounded px-2 py-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                      onClick={() => {
                        const query =
                          metricDetail.metric.sql_query ||
                          'SELECT COUNT(*) as count FROM users WHERE created_at >= CURRENT_DATE'
                        navigator.clipboard.writeText(query)
                      }}
                      title="쿼리 복사"
                    >
                      <i className="ri-file-copy-line"></i>
                    </button>
                  </div>
                  {/* 복사 버튼과 생성시간을 아래로 내림 */}
                  <div className="m-0 flex justify-end">
                    <span className="text-[10px] text-gray-400">
                      {metricDetail.metric.sql_generated_at
                        ? `생성: ${formatUTCToKST(metricDetail.metric.sql_generated_at)}`
                        : '자동 생성됨'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 차트 영역 */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="lg:col-span-1">
              {metricDetail ? (
                (() => {
                  const metricType = getMetricType(convertMetricDetailForType(metricDetail))

                  switch (metricType) {
                    case 'category':
                      return (
                        <CategoryChart
                          data={metricDetail.history}
                          title={metricDetail.metric.name}
                          isLoading={false}
                        />
                      )

                    case 'status':
                      return (
                        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                          <div className="mb-6 flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-gray-900">
                              {metricDetail.metric.name}
                            </h3>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-500">
                                업데이트:{' '}
                                {metricDetail?.latest_executed_at
                                  ? formatUTCToKST(metricDetail.latest_executed_at)
                                  : '실행 대기중'}
                              </span>
                            </div>
                          </div>
                          <div className="space-y-6">
                            <div className="flex items-center justify-center">
                              <div
                                className={`flex h-32 w-32 items-center justify-center rounded-full ${
                                  metricDetail?.latest_value === '이상'
                                    ? 'border-4 border-red-200 bg-red-100'
                                    : 'border-4 border-green-200 bg-green-100'
                                }`}
                              >
                                <div className="text-center">
                                  <i
                                    className={`mb-2 text-4xl ${
                                      metricDetail?.latest_value === '이상'
                                        ? 'ri-close-circle-fill text-red-600'
                                        : 'ri-check-circle-fill text-green-600'
                                    }`}
                                  ></i>
                                  <div
                                    className={`text-lg font-bold ${
                                      metricDetail?.latest_value === '이상'
                                        ? 'text-red-600'
                                        : 'text-green-600'
                                    }`}
                                  >
                                    {metricDetail?.latest_value === '이상' ? '이상' : '정상'}
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div className="text-center">
                              <p className="text-sm text-gray-600">
                                {metricDetail?.latest_executed_at
                                  ? `마지막 확인: ${formatUTCToKST(metricDetail.latest_executed_at)}`
                                  : '실행 대기중'}
                              </p>
                            </div>
                          </div>
                        </div>
                      )

                    case 'single_value':
                    default:
                      return (
                        <MetricChart
                          history={metricDetail.history}
                          title={metricDetail.metric.name}
                          isLoading={false}
                          timeRange={timeRange as '1h' | '24h' | '7d' | '30d'}
                        />
                      )
                  }
                })()
              ) : (
                <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
                  <div className="flex h-64 items-center justify-center text-gray-500">
                    <div className="text-center">
                      <i className="ri-dashboard-line mb-2 text-4xl"></i>
                      <p>지표를 선택하세요</p>
                      <p className="text-sm">좌측에서 모니터링할 지표를 선택해주세요</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 테이블 이상치 감지 */}
            <div className="lg:col-span-1">
              <TableAnomalyDetection />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

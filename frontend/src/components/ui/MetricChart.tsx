import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { type MetricHistory } from '@/features/metrics/types'
import { convertUTCToKST, formatUTCToKST } from '@/lib/utils'

interface MetricChartProps {
  history: MetricHistory[]
  title?: string
  isLoading?: boolean
  timeRange?: '1h' | '6h' | '24h' | '7d' | '30d'
}

interface ChartDataPoint {
  time: string
  value: number
  fullTime: string
  status: string
  timestamp: number
}

export function MetricChart({
  history,
  title = '지표 추이',
  isLoading = false,
  timeRange = '24h',
}: MetricChartProps) {
  // 시간 범위에 따른 데이터 필터링
  const getFilteredHistory = () => {
    if (!timeRange || history.length === 0) return history

    const now = new Date()
    const cutoffTime = new Date()

    switch (timeRange) {
      case '1h':
        cutoffTime.setHours(now.getHours() - 1)
        break
      case '6h':
        cutoffTime.setHours(now.getHours() - 6)
        break
      case '24h':
        cutoffTime.setDate(now.getDate() - 1)
        break
      case '7d':
        cutoffTime.setDate(now.getDate() - 7)
        break
      case '30d':
        cutoffTime.setDate(now.getDate() - 30)
        break
      default:
        return history
    }

    return history.filter((h) => new Date(h.executed_at) >= cutoffTime)
  }

  // 데이터 변환 및 정렬
  const data: ChartDataPoint[] = getFilteredHistory()
    .slice()
    .sort((a, b) => new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime())
    .map((h) => {
      // UTC 시간을 한국 시간으로 변환
      const kstDate = convertUTCToKST(h.executed_at)
      const timeFormat = getOptimalTimeFormat(kstDate, timeRange, getFilteredHistory())

      return {
        time: timeFormat,
        value: typeof h.result_value === 'number' ? h.result_value : 0,
        fullTime: formatUTCToKST(h.executed_at, {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        }),
        status: h.status,
        timestamp: kstDate.getTime(),
      }
    })

  // 개선된 시간 포맷 함수 (이미 KST로 변환된 Date 객체 사용)
  function getOptimalTimeFormat(date: Date, timeRange: string, history: MetricHistory[]): string {
    if (history.length === 0) return ''

    // 데이터 수집 간격 계산
    const interval = calculateAverageInterval(history)

    if (timeRange === '1h') {
      // 1시간 범위: 분 단위 표시 (5분 간격일 경우 유용)
      return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } else if (timeRange === '6h') {
      // 6시간 범위: 시:분 표시
      return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } else if (timeRange === '24h') {
      // 24시간 범위: 간격에 따라 동적 결정
      if (interval < 20 * 60 * 1000) {
        // 20분 미만 간격: 시:분
        return date.toLocaleTimeString('ko-KR', {
          hour: '2-digit',
          minute: '2-digit',
        })
      } else {
        // 20분 이상 간격: 시간만
        return date.toLocaleTimeString('ko-KR', { hour: '2-digit' }) + '시'
      }
    } else if (timeRange === '7d') {
      // 7일 범위: 월/일 시간
      return date.toLocaleDateString('ko-KR', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
      })
    } else if (timeRange === '30d') {
      // 30일 범위: 월/일
      return date.toLocaleDateString('ko-KR', {
        month: '2-digit',
        day: '2-digit',
      })
    }

    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 평균 수집 간격 계산
  function calculateAverageInterval(history: MetricHistory[]): number {
    if (history.length < 2) return 60 * 60 * 1000 // 기본 1시간

    const timestamps = history.map((h) => new Date(h.executed_at).getTime()).sort((a, b) => a - b)

    const intervals: number[] = []
    for (let i = 1; i < timestamps.length; i++) {
      intervals.push(timestamps[i] - timestamps[i - 1])
    }

    const sum = intervals.reduce((a, b) => a + b, 0)
    return sum / intervals.length
  }

  // 수집 간격 텍스트 생성
  function getCollectionIntervalText(): string {
    if (data.length < 2) return '데이터 수집 중'

    const avgInterval = calculateAverageInterval(getFilteredHistory())
    const minutes = Math.round(avgInterval / (60 * 1000))

    if (minutes < 60) {
      return `${minutes}분 간격`
    } else if (minutes < 1440) {
      const hours = Math.round(minutes / 60)
      return `${hours}시간 간격`
    } else {
      const days = Math.round(minutes / 1440)
      return `${days}일 간격`
    }
  }

  // 개선된 X축 간격 계산
  const getXAxisInterval = () => {
    const dataLength = data.length

    if (dataLength <= 6) return 0 // 6개 이하: 모든 레이블 표시

    // 중복 레이블 감지
    const uniqueLabels = new Set(data.map((d) => d.time))
    const hasDuplicates = uniqueLabels.size < dataLength

    if (hasDuplicates) {
      // 중복이 있으면 간격 조정
      // 표시할 레이블 수 결정 (최대 8-10개)
      const targetLabels = 8
      return Math.max(1, Math.floor(dataLength / targetLabels))
    }

    // 중복 없음: 데이터 개수에 따라 조정
    if (dataLength <= 12) return 1
    if (dataLength <= 24) return 2
    if (dataLength <= 48) return 4
    return Math.floor(dataLength / 10)
  }

  // 빈 데이터 상태
  if (!isLoading && data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 animate-pulse rounded-full bg-gray-400"></div>
            <span className="text-xs text-gray-500">데이터 수집 대기중</span>
          </div>
        </div>
        <div className="flex h-64 items-center justify-center text-gray-500">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
              <i className="ri-line-chart-line text-2xl text-gray-400"></i>
            </div>
            <p className="mb-2 text-lg font-medium">첫 데이터 수집 중</p>
            <p className="mb-4 text-sm text-gray-400">스케줄러가 곧 데이터를 수집합니다</p>
            <div className="inline-block rounded bg-gray-50 px-3 py-2 text-xs text-gray-400">
              💡 Tip: "즉시 실행" 버튼으로 수동 실행 가능
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
            <p className="text-gray-500">차트 로딩 중...</p>
          </div>
        </div>
      </div>
    )
  }

  // 최신 값과 변화율 계산
  const latestValue = data[data.length - 1]?.value || 0
  const previousValue = data.length > 1 ? data[data.length - 2]?.value || 0 : 0
  const changeRate = previousValue !== 0 ? ((latestValue - previousValue) / previousValue) * 100 : 0

  // 변화율에 따른 색상 결정
  const getGradientColor = () => {
    if (changeRate > 0) {
      return {
        id: 'colorGradient',
        stroke: '#10B981',
        stops: [
          { offset: '0%', color: '#10B981', opacity: 0.8 },
          { offset: '50%', color: '#34D399', opacity: 0.4 },
          { offset: '100%', color: '#6EE7B7', opacity: 0.1 },
        ],
      }
    } else if (changeRate < 0) {
      return {
        id: 'colorGradient',
        stroke: '#EF4444',
        stops: [
          { offset: '0%', color: '#EF4444', opacity: 0.8 },
          { offset: '50%', color: '#F87171', opacity: 0.4 },
          { offset: '100%', color: '#FCA5A5', opacity: 0.1 },
        ],
      }
    } else {
      return {
        id: 'colorGradient',
        stroke: '#3B82F6',
        stops: [
          { offset: '0%', color: '#3B82F6', opacity: 0.8 },
          { offset: '50%', color: '#60A5FA', opacity: 0.4 },
          { offset: '100%', color: '#93C5FD', opacity: 0.1 },
        ],
      }
    }
  }

  const gradientConfig = getGradientColor()

  // 커스텀 툴팁
  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean
    payload?: Array<{ payload: ChartDataPoint }>
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
          <div className="mb-2 flex items-center space-x-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: gradientConfig.stroke }}
            ></div>
            <span className="text-sm font-medium text-gray-900">{data.fullTime}</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-gray-600">값:</span>
              <span className="text-sm font-bold text-gray-900">{data.value.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-gray-600">상태:</span>
              <span
                className={`text-sm font-medium ${
                  data.status === 'success' ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {data.status === 'success' ? '정상' : '오류'}
              </span>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  // 시간 범위 레이블
  const getTimeRangeLabel = () => {
    const labels = {
      '1h': '최근 1시간',
      '6h': '최근 6시간',
      '24h': '최근 24시간',
      '7d': '최근 7일',
      '30d': '최근 30일',
    }
    return labels[timeRange] || '시간 범위'
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {title} ({getTimeRangeLabel()})
          </h3>
          <div className="mt-1 text-sm text-gray-500">
            {getCollectionIntervalText()} • {data.length}개 포인트
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">{latestValue.toLocaleString()}</div>
            {changeRate !== 0 && data.length > 1 && (
              <div
                className={`text-sm font-medium ${
                  changeRate > 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {changeRate > 0 ? '▲' : '▼'} {Math.abs(changeRate).toFixed(1)}%
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="h-64 sm:h-72 md:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <defs>
              {/* 동적 그라데이션 정의 */}
              <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                {gradientConfig.stops.map((stop, index) => (
                  <stop
                    key={index}
                    offset={stop.offset}
                    stopColor={stop.color}
                    stopOpacity={stop.opacity}
                  />
                ))}
              </linearGradient>
              {/* 호버 시 그라데이션 */}
              <linearGradient id="colorGradientHover" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563EB" stopOpacity={0.9} />
                <stop offset="50%" stopColor="#3B82F6" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#60A5FA" stopOpacity={0.2} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="time"
              stroke="#9CA3AF"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
              interval={getXAxisInterval()}
              angle={data.length > 20 ? -45 : 0}
              textAnchor={data.length > 20 ? 'end' : 'middle'}
              height={data.length > 20 ? 60 : 30}
            />
            <YAxis
              stroke="#9CA3AF"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickFormatter={(value) => value.toLocaleString()}
            />
            <Tooltip content={<CustomTooltip />} />
            {/* 그라데이션 영역 */}
            <Area
              type="monotone"
              dataKey="value"
              stroke={gradientConfig.stroke}
              strokeWidth={2}
              fill="url(#colorGradient)"
              dot={{ fill: gradientConfig.stroke, r: 4, strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 6, stroke: gradientConfig.stroke, strokeWidth: 2, fill: '#fff' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 차트 하단 정보 */}
      <div className="mt-4 border-t border-gray-100 pt-4">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span>총 {data.length}개 데이터</span>
            {data.length > 0 && <span>최신: {data[data.length - 1]?.fullTime}</span>}
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: gradientConfig.stroke }}
            ></div>
            <span>{getCollectionIntervalText()}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

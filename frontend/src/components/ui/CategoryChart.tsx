import { useState } from 'react'

import { type MetricHistory } from '@/features/metrics/types'
import { formatUTCToKST } from '@/lib/utils'

interface CategoryChartProps {
  data: MetricHistory[]
  title: string
  isLoading?: boolean
}

interface CategoryData {
  label: string
  value: number
  percentage: number
  color: string
  originalData: Record<string, unknown>
}

const COLORS = [
  '#34D399', // emerald-400 - pending (더 부드러운 초록)
  '#60A5FA', // blue-400 - refunded (더 부드러운 파랑)
  '#A78BFA', // violet-400 - confirmed (더 부드러운 보라)
  '#F87171', // red-400 - delivered (더 부드러운 빨강)
  '#FBBF24', // amber-400 - shipped (더 부드러운 주황)
  '#22D3EE', // cyan-400 - processing (더 부드러운 청록)
  '#F472B6', // pink-400 - cancelled (더 부드러운 핑크)
  '#A3E635', // lime-400
  '#2DD4BF', // teal-400
  '#FB923C', // orange-400
]

export function CategoryChart({ data, title, isLoading = false }: CategoryChartProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [hoveredSlice, setHoveredSlice] = useState<number | null>(null)

  // 최신 데이터 가져오기
  const latestData = data[0]?.result_data || []

  // 카테고리 데이터 변환
  const categoryData: CategoryData[] = latestData.map((item, index) => {
    // 다양한 필드명 지원: count, order_count, total, value 등
    const value =
      typeof item.count === 'number'
        ? item.count
        : typeof item.order_count === 'number'
          ? item.order_count
          : typeof item.total === 'number'
            ? item.total
            : typeof item.value === 'number'
              ? item.value
              : parseInt(String(item.count || item.order_count || item.total || item.value)) || 0

    const total = latestData.reduce((sum, d) => {
      const count =
        typeof d.count === 'number'
          ? d.count
          : typeof d.order_count === 'number'
            ? d.order_count
            : typeof d.total === 'number'
              ? d.total
              : typeof d.value === 'number'
                ? d.value
                : parseInt(String(d.count || d.order_count || d.total || d.value)) || 0
      return sum + count
    }, 0)

    return {
      label: String(item.category || item.status || item.name || `항목 ${index + 1}`),
      value,
      percentage: total > 0 ? Math.round((value / total) * 100) : 0,
      color: COLORS[index % COLORS.length],
      originalData: item,
    }
  })

  const total = categoryData.reduce((sum, item) => sum + item.value, 0)

  // SVG 파이차트 경로 생성
  const generatePieSlices = () => {
    let cumulativePercentage = 0
    const radius = 70
    const centerX = 100
    const centerY = 100

    return categoryData.map((item, index) => {
      const startAngle = (cumulativePercentage / 100) * 360
      const endAngle = ((cumulativePercentage + item.percentage) / 100) * 360

      const startAngleRad = (startAngle - 90) * (Math.PI / 180)
      const endAngleRad = (endAngle - 90) * (Math.PI / 180)

      const x1 = centerX + radius * Math.cos(startAngleRad)
      const y1 = centerY + radius * Math.sin(startAngleRad)
      const x2 = centerX + radius * Math.cos(endAngleRad)
      const y2 = centerY + radius * Math.sin(endAngleRad)

      const largeArc = item.percentage > 50 ? 1 : 0

      const pathData = [
        `M ${centerX} ${centerY}`,
        `L ${x1} ${y1}`,
        `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
        'Z',
      ].join(' ')

      cumulativePercentage += item.percentage

      return {
        ...item,
        path: pathData,
        index,
      }
    })
  }

  const pieSlices = generatePieSlices()

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

  // 빈 데이터 상태
  if (categoryData.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="flex h-64 items-center justify-center text-gray-500">
          <div className="text-center">
            <i className="ri-pie-chart-line mb-2 text-4xl"></i>
            <p>카테고리 데이터가 없습니다</p>
            <p className="text-sm">지표가 실행되면 차트가 표시됩니다</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-800">{title}</h3>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-lg font-semibold text-gray-700">{total.toLocaleString()}</div>
            <div className="text-sm text-gray-500">{categoryData.length}개 카테고리</div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500">
              업데이트: {data[0]?.executed_at ? formatUTCToKST(data[0].executed_at) : '데이터 없음'}
            </span>
            <button className="inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap text-gray-700 transition-colors hover:bg-gray-100 disabled:text-gray-400">
              <i className="ri-refresh-line"></i>
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col space-y-4 lg:flex-row lg:items-start lg:space-y-0 lg:space-x-6">
        {/* 파이 차트 */}
        <div className="flex items-center justify-center lg:flex-shrink-0">
          <div className="relative">
            <svg className="h-48 w-48 sm:h-56 sm:w-56 lg:h-64 lg:w-64" viewBox="0 0 200 200">
              {/* 배경 원 */}
              <circle cx="100" cy="100" r="70" fill="#F8FAFC" stroke="#E2E8F0" strokeWidth="1" />

              {/* 파이 슬라이스들 */}
              {pieSlices.map((slice, index) => (
                <g key={index}>
                  {/* 그림자 효과 */}
                  <path
                    d={slice.path}
                    fill="rgba(0,0,0,0.1)"
                    transform="translate(2, 2)"
                    className="opacity-0"
                  />
                  {/* 메인 슬라이스 */}
                  <path
                    d={slice.path}
                    fill={slice.color}
                    className={`cursor-pointer transition-all duration-300 ${
                      hoveredSlice === index
                        ? 'scale-1.05 transform opacity-90'
                        : hoveredSlice !== null
                          ? 'opacity-60'
                          : 'opacity-100'
                    }`}
                    onMouseEnter={() => setHoveredSlice(index)}
                    onMouseLeave={() => setHoveredSlice(null)}
                    onClick={() =>
                      setSelectedCategory(selectedCategory === slice.label ? null : slice.label)
                    }
                    style={{
                      filter:
                        hoveredSlice === index ? 'drop-shadow(0 4px 8px rgba(0,0,0,0.15))' : 'none',
                    }}
                  />
                  {/* 테두리 */}
                  <path
                    d={slice.path}
                    fill="none"
                    stroke="white"
                    strokeWidth="2"
                    className="pointer-events-none"
                  />
                </g>
              ))}

              {/* 중앙 원 그라데이션 */}
              <defs>
                <radialGradient id="centerGradient" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#FFFFFF" stopOpacity="1" />
                  <stop offset="100%" stopColor="#F8FAFC" stopOpacity="1" />
                </radialGradient>
              </defs>
              <circle
                cx="100"
                cy="100"
                r="40"
                fill="url(#centerGradient)"
                stroke="#E2E8F0"
                strokeWidth="1"
              />

              {/* 중앙 텍스트 */}
              <text
                x="100"
                y="88"
                textAnchor="middle"
                className="fill-gray-700 text-lg font-semibold"
              >
                {total.toLocaleString()}
              </text>
              <text x="100" y="105" textAnchor="middle" className="fill-gray-500 text-xs">
                총계
              </text>
            </svg>

            {/* 호버 시 표시되는 정보 */}
            {hoveredSlice !== null && (
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-full transform rounded-lg bg-gray-900 px-3 py-2 text-sm font-medium whitespace-nowrap text-white shadow-lg">
                <div className="flex items-center space-x-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: categoryData[hoveredSlice].color }}
                  />
                  <span>{categoryData[hoveredSlice].label}</span>
                  <span className="text-gray-300">({categoryData[hoveredSlice].percentage}%)</span>
                </div>
                <div className="absolute top-full left-1/2 h-0 w-0 -translate-x-1/2 transform border-t-4 border-r-4 border-l-4 border-transparent border-t-gray-900"></div>
              </div>
            )}
          </div>
        </div>

        {/* 범례 및 상세 정보 */}
        <div className="flex-1 space-y-3">
          <div className="space-y-1">
            {categoryData.map((item, index) => (
              <div
                key={index}
                className={`flex cursor-pointer items-center justify-between rounded-lg p-3 transition-all duration-200 ${
                  selectedCategory === item.label
                    ? 'border-2 border-blue-200 bg-blue-50 shadow-sm'
                    : hoveredSlice === index
                      ? 'border border-gray-200 bg-gray-50'
                      : 'border border-transparent hover:bg-gray-50'
                }`}
                onMouseEnter={() => setHoveredSlice(index)}
                onMouseLeave={() => setHoveredSlice(null)}
                onClick={() =>
                  setSelectedCategory(selectedCategory === item.label ? null : item.label)
                }
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div
                      className="h-4 w-4 rounded-full shadow-sm transition-all duration-200"
                      style={{ backgroundColor: item.color }}
                    />
                    {selectedCategory === item.label && (
                      <div className="absolute -top-1 -right-1 flex h-2.5 w-2.5 items-center justify-center rounded-full bg-blue-600">
                        <i className="ri-check-line text-xs text-white"></i>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-800 capitalize">
                      {item.label}
                    </span>
                    <span className="text-xs text-gray-500">({item.percentage}%)</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-800">
                      {item.value.toLocaleString()}
                    </div>
                  </div>
                  {selectedCategory === item.label && (
                    <i className="ri-arrow-right-s-line text-sm text-blue-600"></i>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* 필터 버튼들 */}
          <div className="flex flex-wrap gap-1.5">
            <button
              className={`inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-all duration-200 ${
                selectedCategory === null
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'border border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50'
              }`}
              onClick={() => setSelectedCategory(null)}
            >
              <i className="ri-filter-line mr-1"></i>전체
            </button>
            {categoryData.slice(0, 4).map((item, index) => (
              <button
                key={index}
                className={`inline-flex cursor-pointer items-center justify-center rounded-lg px-3 py-1.5 text-xs font-medium whitespace-nowrap capitalize transition-all duration-200 ${
                  selectedCategory === item.label
                    ? 'text-white shadow-sm'
                    : 'border border-gray-200 text-gray-700 hover:bg-gray-100'
                }`}
                style={{
                  backgroundColor: selectedCategory === item.label ? item.color : 'transparent',
                  borderColor: selectedCategory === item.label ? item.color : '#E5E7EB',
                }}
                onClick={() =>
                  setSelectedCategory(selectedCategory === item.label ? null : item.label)
                }
              >
                <div
                  className="mr-1.5 h-1.5 w-1.5 rounded-full"
                  style={{
                    backgroundColor: selectedCategory === item.label ? 'white' : item.color,
                  }}
                />
                {item.label}
              </button>
            ))}
          </div>

          {/* 선택된 카테고리 상세 정보 */}
          {selectedCategory && (
            <div className="mt-4 rounded-lg border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div
                    className="h-4 w-4 rounded-full shadow-sm"
                    style={{
                      backgroundColor: categoryData.find((item) => item.label === selectedCategory)
                        ?.color,
                    }}
                  />
                  <h4 className="text-sm font-medium text-blue-800 capitalize">
                    {selectedCategory}
                  </h4>
                </div>
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="rounded-full p-1 text-blue-500 transition-colors hover:bg-blue-100 hover:text-blue-700"
                >
                  <i className="ri-close-line text-sm"></i>
                </button>
              </div>
              {(() => {
                const selected = categoryData.find((item) => item.label === selectedCategory)
                return selected ? (
                  <div className="grid grid-cols-3 gap-2">
                    <div className="rounded border border-blue-100 bg-white p-2 text-center">
                      <div className="text-base font-semibold text-blue-800">
                        {selected.value.toLocaleString()}
                      </div>
                      <div className="text-xs text-blue-600">건수</div>
                    </div>
                    <div className="rounded border border-blue-100 bg-white p-2 text-center">
                      <div className="text-base font-semibold text-blue-800">
                        {selected.percentage}%
                      </div>
                      <div className="text-xs text-blue-600">비율</div>
                    </div>
                    <div className="rounded border border-blue-100 bg-white p-2 text-center">
                      <div className="text-base font-semibold text-blue-800">
                        {((selected.value / total) * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-blue-600">전체 대비</div>
                    </div>
                  </div>
                ) : null
              })()}
            </div>
          )}
        </div>
      </div>

      {/* 차트 하단 정보 */}
      <div className="mt-4 flex flex-col space-y-2 text-xs text-gray-500 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div className="flex items-center space-x-4">
          <span>총 {categoryData.length}개 카테고리</span>
          <span>
            최신 업데이트:{' '}
            {data[0]?.executed_at ? formatUTCToKST(data[0].executed_at) : '데이터 없음'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 rounded-full bg-green-500"></div>
          <span>실시간 데이터</span>
        </div>
      </div>
    </div>
  )
}

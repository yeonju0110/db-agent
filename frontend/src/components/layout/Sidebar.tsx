import { Activity, PieChart, Plus, TrendingUp } from 'lucide-react'

import { type MetricListItem } from '@/features/metrics/types'
import { cn } from '@/lib/utils'

interface SidebarProps {
  metrics: MetricListItem[]
  selectedMetricId?: string
  onMetricSelect: (id: string) => void
  onAddMetric: () => void
}

export function Sidebar({ metrics, selectedMetricId, onMetricSelect, onAddMetric }: SidebarProps) {
  return (
    <aside className="flex w-96 flex-col border-r border-gray-200 bg-white">
      {/* 헤더 */}
      <div className="border-b border-gray-200 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">모니터링 지표</h2>
          <button
            onClick={onAddMetric}
            className="bg-primary hover:bg-primary-dark flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm text-white"
          >
            <Plus className="h-4 w-4" />
            추가
          </button>
        </div>

        {/* 필터 탭 */}
        <div className="flex gap-2 text-sm">
          <button className="rounded-lg bg-gray-100 px-3 py-1.5">전체</button>
          <button className="flex items-center gap-1 rounded-lg px-3 py-1.5 hover:bg-gray-100">
            <TrendingUp className="h-4 w-4" />
            숫자형
          </button>
          <button className="flex items-center gap-1 rounded-lg px-3 py-1.5 hover:bg-gray-100">
            <PieChart className="h-4 w-4" />
            카테고리형
          </button>
        </div>
      </div>

      {/* 지표 목록 */}
      <div className="flex-1 overflow-y-auto">
        {metrics.map((metric) => (
          <MetricCard
            key={metric.id}
            metric={metric}
            isSelected={metric.id === selectedMetricId}
            onClick={() => onMetricSelect(metric.id)}
          />
        ))}
      </div>

      {/* 요금제 정보 */}
      <div className="border-t border-gray-200 bg-blue-50 p-4">
        <div className="flex items-start gap-2 text-sm">
          <Activity className="text-primary mt-0.5 h-4 w-4" />
          <div>
            <p className="font-medium text-gray-900">요금제 정보</p>
            <p className="mt-1 text-xs text-gray-600">현재 4개 / 최대 10개 지표 사용 중</p>
            <div className="mt-2 h-2 w-full rounded-full bg-white">
              <div className="bg-primary h-2 rounded-full" style={{ width: '40%' }} />
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

function MetricCard({
  metric,
  isSelected,
  onClick,
}: {
  metric: MetricListItem
  isSelected: boolean
  onClick: () => void
}) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'bg-status-success'
      case 'warning':
        return 'bg-status-warning'
      case 'error':
        return 'bg-status-error'
      default:
        return 'bg-gray-400'
    }
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full border-b border-gray-100 p-4 text-left transition-colors hover:bg-gray-50',
        isSelected && 'bg-primary-light'
      )}
    >
      <div className="mb-2 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-gray-400" />
          <span className="font-medium text-gray-900">{metric.name}</span>
        </div>
        <span className={cn('h-2 w-2 rounded-full', getStatusColor(metric.status))} />
      </div>

      <div className="mb-1 text-2xl font-bold text-gray-900">{metric.latest_value}</div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{metric.latest_executed_at}</span>
        {metric.change_rate && (
          <span
            className={cn(
              'font-medium',
              metric.change_rate > 0 ? 'text-status-success' : 'text-status-error'
            )}
          >
            {metric.change_rate > 0 ? '+' : ''}
            {metric.change_rate}%
          </span>
        )}
      </div>
    </button>
  )
}

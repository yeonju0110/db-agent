export interface Metric {
  id: string
  name: string
  natural_query: string
  sql_query: string
  status: 'active' | 'paused'
  related_tables?: string[]
  threshold_config: {
    enabled: boolean
    operator: string
    value: number
  }
  created_at: string
  sql_generated_at: string | null
}

export interface MetricHistory {
  id: string
  executed_at: string
  result_type: 'single_value' | 'multiple_rows'
  result_value: number | null
  result_data: Array<Record<string, string | number>> | null
  status: string
}

export interface MetricDetail {
  metric: Metric
  latest_value: number | string | null
  latest_executed_at: string | null
  history: MetricHistory[]
  anomalies_count: number
}

// 목록 전용 요약 타입 (백엔드 응답에 맞춰 확장 가능)
export interface MetricListItem extends Metric {
  latest_value?: number | string | null
  latest_executed_at?: string | null
  change_rate?: string | null
}

// 이상징후
export interface AnomalyItem {
  id: string
  metric_id: string
  metric_name: string
  detected_at: string
  message: string
  level: 'high' | 'medium' | 'low'
  resolved: boolean
}

// DB 상태
export interface DbStatusItem {
  name: string
  type: string
  status: 'normal' | 'error'
  latency?: string | null
}

// 권장사항
export interface RecommendationItem {
  id: string
  type: 'optimization' | 'alert_setup' | 'maintenance'
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  action_url?: string | null
}

// 즉시 질문 응답
export interface QueryResponse {
  question: string
  sql: string
  result_type: 'single_value' | 'multiple_rows' | 'no_data'
  result_value: number | string | null
  result_data: Array<Record<string, unknown>> | null
  execution_time_ms?: number
  tables_used: string[]
}

// DB 연결 관리
export interface CreateDbConnectionRequest {
  name: string
  host: string
  port: number
  database: string
  username: string
  password: string
}

export interface DbConnectionItem {
  id: string
  name: string
  db_type: string
  host: string
  port: number
  database: string
  username: string
  created_at: string
  status: string
  last_tested_at?: string
}

export interface ConnectionTestResult {
  success: boolean
  message: string
  latency_ms?: number
  tested_at: string
}

export interface SetupStartResult {
  connection_id: string
  setup_id: string
  message: string
}

export interface SetupStep {
  name: string
  status: 'pending' | 'running' | 'success' | 'error'
  message: string
  started_at?: string
  completed_at?: string
  error_details?: string
}

export interface SetupStatus {
  connection_id: string
  status: 'pending' | 'running' | 'success' | 'error'
  steps: SetupStep[]
  started_at?: string
  completed_at?: string
  current_step: number
  total_steps: number
  progress_percentage: number
}

// 테이블 이상치 감지
export interface TableAnomalyDetection {
  id: string
  table_name: string
  detected_at: string
  total_records: number
  duplicate_count: number
  null_count: number
  anomaly_count: number
  status: 'normal' | 'warning' | 'error'
  is_acknowledged: boolean
  created_at: string
  updated_at: string
}

export interface TableAnomalyDetail {
  id: string
  anomaly_detection_id: string
  anomaly_type:
    | 'null_values'
    | 'duplicates'
    | 'data_quality'
    | 'business_logic'
    | 'pattern_anomaly'
    | 'time_inconsistency'
  severity: 'low' | 'medium' | 'high'
  count: number
  description: string
  affected_columns: string[]
  sample_data?: Record<string, unknown>
  is_acknowledged: boolean
  created_at: string
  updated_at: string
}

export interface TableAnomalySummary {
  total_detections: number
  total_anomalies: number
  status_breakdown: Record<string, number>
  table_breakdown: Array<{
    table_name: string
    detection_count: number
    anomaly_count: number
  }>
}

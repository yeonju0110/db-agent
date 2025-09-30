"""
API Request/Response 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from backend.models.monitoring import QueryResultType


# ===== 지표 관리 =====

class CreateMetricRequest(BaseModel):
    """지표 생성 요청"""
    natural_query: str = Field(..., description="자연어 질문", example="오늘 주문 건수")
    name: Optional[str] = Field(None, description="지표 이름 (없으면 자연어 질문 사용)")
    db_connection_id: str = Field(..., description="DB 연결 ID")
    
    # 관련 테이블 정보
    related_tables: List[str] = Field(default_factory=list, description="관련 테이블 목록")
    
    # 임계값 설정 (선택)
    threshold_enabled: bool = False
    threshold_operator: str = ">"
    threshold_value: float = 0.0
    
    # 스케줄 설정
    schedule_interval_minutes: int = 60


class MetricResponse(BaseModel):
    """지표 응답"""
    id: str
    name: str
    natural_query: str
    sql_query: str
    status: str
    related_tables: Optional[List[str]] = None
    threshold_config: Dict[str, Any]
    created_at: datetime
    sql_generated_at: Optional[datetime]
    # 대시보드용 추가 필드
    latest_value: Optional[Any] = None
    latest_executed_at: Optional[datetime] = None
    change_rate: Optional[str] = None


class MetricListResponse(BaseModel):
    """지표 목록 응답"""
    total: int
    items: List[MetricResponse]


# ===== 스케줄러 관리 =====

class SchedulerControlRequest(BaseModel):
    """스케줄러 제어 요청"""
    interval_minutes: int = Field(60, description="실행 간격 (분)", ge=1, le=1440)


class SchedulerStatusResponse(BaseModel):
    """스케줄러 상태 응답"""
    is_running: bool
    start_time: Optional[str]
    interval_minutes: int
    active_metrics_count: int
    uptime_seconds: float


# ===== 즉시 질문 =====

class QueryRequest(BaseModel):
    """즉시 질문 요청"""
    question: str = Field(..., description="자연어 질문", example="이번 달 매출액은?")
    db_connection_id: Optional[str] = Field(None, description="DB 연결 ID")


class QueryResponse(BaseModel):
    """즉시 질문 응답"""
    question: str
    sql: str
    result_type: Literal["no_data", "single_value", "multiple_rows"]
    result_value: Optional[Any]
    result_data: Optional[List[Dict[str, Any]]]
    execution_time_ms: Optional[int]
    tables_used: List[str]


# ===== 대시보드 데이터 =====

class HistoryResponse(BaseModel):
    """히스토리 응답"""
    id: str
    executed_at: datetime
    result_type: QueryResultType
    result_value: Optional[Any]
    result_data: Optional[List[Dict[str, Any]]]
    status: str


class MetricDetailResponse(BaseModel):
    """지표 상세 (히스토리 포함)"""
    metric: MetricResponse
    latest_value: Optional[Any]
    latest_executed_at: Optional[datetime]
    history: List[HistoryResponse]
    anomalies_count: int


class DashboardSummaryResponse(BaseModel):
    """대시보드 요약"""
    total_metrics: int
    active_metrics: int
    total_anomalies: int
    last_updated: datetime


# ===== 이상징후 =====

class AnomalyResponse(BaseModel):
    """이상징후 응답"""
    id: str
    metric_id: str
    metric_name: str
    detected_at: datetime
    message: str
    level: str  # high, medium, low
    resolved: bool = False
    

class AnomalyListResponse(BaseModel):
    """이상징후 목록"""
    total: int
    items: List[AnomalyResponse]


# ===== DB 연결 상태 =====

class DbStatusResponse(BaseModel):
    """DB 연결 상태"""
    name: str
    type: str
    status: str  # normal, error
    latency: Optional[str] = None


class DbStatusListResponse(BaseModel):
    """DB 연결 상태 목록"""
    items: List[DbStatusResponse]


# ===== 권장사항 =====

class RecommendationResponse(BaseModel):
    """권장사항"""
    id: str
    type: str  # optimization, alert_setup, maintenance
    title: str
    description: str
    priority: str  # high, medium, low
    action_url: Optional[str] = None


class RecommendationListResponse(BaseModel):
    """권장사항 목록"""
    items: List[RecommendationResponse]


# ===== DB 연결 관리 =====

class CreateDbConnectionRequest(BaseModel):
    """DB 연결 생성 요청"""
    name: str = Field(..., description="연결 이름", example="프로덕션 DB")
    host: str = Field(..., description="호스트", example="localhost")
    port: int = Field(..., description="포트", example=5432)
    database: str = Field(..., description="데이터베이스명", example="ecommerce_db")
    username: str = Field(..., description="사용자명", example="monitoring_user")
    password: str = Field(..., description="비밀번호", example="password123")


class DbConnectionResponse(BaseModel):
    """DB 연결 응답"""
    id: str
    name: str
    db_type: str = "postgres"
    host: str
    port: int
    database: str
    username: str
    created_at: datetime
    status: str
    last_tested_at: Optional[datetime] = None


class DbConnectionListResponse(BaseModel):
    """DB 연결 목록 응답"""
    total: int
    items: List[DbConnectionResponse]


class ConnectionTestResponse(BaseModel):
    """연결 테스트 응답"""
    success: bool
    message: str
    latency_ms: Optional[int] = None
    tested_at: datetime


class SetupStepResponse(BaseModel):
    """설정 단계 응답"""
    name: str
    status: str
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None


class SetupStatusResponse(BaseModel):
    """설정 상태 응답"""
    connection_id: str
    status: str
    steps: List[SetupStepResponse]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: int
    total_steps: int
    progress_percentage: float


class SetupResponse(BaseModel):
    """설정 시작 응답"""
    connection_id: str
    setup_id: str
    message: str
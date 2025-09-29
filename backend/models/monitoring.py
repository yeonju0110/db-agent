"""
모니터링 도메인 모델
"""
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    """지표 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class QueryStatus(str, Enum):
    """쿼리 실행 상태"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class QueryResultType(str, Enum):
    """쿼리 결과 유형"""
    SINGLE_VALUE = "single_value"  # 단일 숫자 (COUNT, SUM, AVG)
    MULTIPLE_ROWS = "multiple_rows"  # 다중 행 (GROUP BY 결과)
    NO_DATA = "no_data"  # 결과 없음


class AnomalyType(str, Enum):
    """이상 유형"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"  # 임계값 초과
    THRESHOLD_BELOW = "threshold_below"  # 임계값 미달
    NO_DATA = "no_data"  # 데이터 없음
    QUERY_ERROR = "query_error"  # 쿼리 오류


class ThresholdConfig(BaseModel):
    """임계값 설정 (MVP: 단순 비교)"""
    enabled: bool = False
    operator: str = ">"  # >, <, >=, <=, ==, !=
    value: float = 0.0
    
    
class MonitoringMetric(BaseModel):
    """모니터링 지표"""
    id: Optional[str] = None
    name: str = Field(..., description="지표 이름")
    natural_query: str = Field(..., description="자연어 질문")
    sql_query: str = Field(default="", description="캐싱된 SQL")  # ← 수정
    sql_generated_at: Optional[datetime] = None  # ← 추가
    use_cached_sql: bool = True  # ← 추가
    
    # DB 연결 정보
    db_connection_id: str = Field(..., description="DB 연결 ID")
    
    # 스케줄 설정
    schedule_interval_minutes: int = Field(default=60, description="실행 주기(분)")
    
    # 임계값 설정
    threshold_config: ThresholdConfig = Field(default_factory=ThresholdConfig)
    
    # 메타데이터
    status: MetricStatus = MetricStatus.ACTIVE
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # 관련 테이블 정보
    related_tables: List[str] = Field(default_factory=list)


class QueryHistory(BaseModel):
    """쿼리 실행 히스토리"""
    id: Optional[str] = None
    metric_id: str
    
    # 실행 정보
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    execution_time_ms: Optional[int] = None
    
    # 결과
    status: QueryStatus
    result_type: QueryResultType = QueryResultType.SINGLE_VALUE
    result_value: Optional[Any] = None  # 단일 값 (숫자형)
    result_data: Optional[List[Dict[str, Any]]] = None  # 다중 행 (카테고리형)
    row_count: Optional[int] = None
    
    # 에러 정보
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class Anomaly(BaseModel):
    """이상 탐지 내역"""
    id: Optional[str] = None
    metric_id: str
    history_id: str  # 해당 쿼리 실행 ID
    
    # 이상 정보
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    anomaly_type: AnomalyType
    
    # 임계값 비교 정보
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    
    # 해결 정보
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # 알림 발송 여부
    notification_sent: bool = False


class DBConnection(BaseModel):
    """DB 연결 정보"""
    id: Optional[str] = None
    name: str = Field(..., description="연결 이름")
    
    # 연결 정보 (실제로는 암호화 저장)
    host: str
    port: int = 5432
    database: str
    user: str
    password: str  # 암호화 필요
    
    # 메타데이터
    is_active: bool = True
    last_tested_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
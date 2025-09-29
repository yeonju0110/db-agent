"""
API Request/Response 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ===== 지표 관리 =====

class CreateMetricRequest(BaseModel):
    """지표 생성 요청"""
    natural_query: str = Field(..., description="자연어 질문", example="오늘 주문 건수")
    name: Optional[str] = Field(None, description="지표 이름 (없으면 자연어 질문 사용)")
    db_connection_id: str = Field(..., description="DB 연결 ID")
    
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
    threshold_config: Dict[str, Any]
    created_at: datetime
    sql_generated_at: Optional[datetime]


class MetricListResponse(BaseModel):
    """지표 목록 응답"""
    total: int
    items: List[MetricResponse]


# ===== 즉시 질문 =====

class QueryRequest(BaseModel):
    """즉시 질문 요청"""
    question: str = Field(..., description="자연어 질문", example="이번 달 매출액은?")
    db_connection_id: Optional[str] = Field(None, description="DB 연결 ID")


class QueryResponse(BaseModel):
    """즉시 질문 응답"""
    question: str
    sql: str
    result_type: str  # single_value, multiple_rows
    result_value: Optional[Any]
    result_data: Optional[List[Dict[str, Any]]]
    execution_time_ms: Optional[int]
    tables_used: List[str]


# ===== 대시보드 데이터 =====

class HistoryResponse(BaseModel):
    """히스토리 응답"""
    id: str
    executed_at: datetime
    result_type: str
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
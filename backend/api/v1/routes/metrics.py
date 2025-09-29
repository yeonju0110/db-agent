"""
지표 관리 API
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.v1.schemas.requests import (
    CreateMetricRequest,
    MetricResponse,
    MetricListResponse,
    MetricDetailResponse,
    HistoryResponse
)
from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MonitoringMetric, ThresholdConfig, MetricStatus
from backend.core.ai.agent_graph import create_agent_graph
from datetime import datetime

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
repository = get_repository()


@router.post("", response_model=MetricResponse)
async def create_metric(request: CreateMetricRequest):
    """
    지표 생성
    - 자연어 질문으로 지표 등록
    - 즉시 SQL 생성 및 테스트 실행
    """
    # 지표 생성
    metric = MonitoringMetric(
        name=request.name or request.natural_query,
        natural_query=request.natural_query,
        sql_query="",
        db_connection_id=request.db_connection_id,
        schedule_interval_minutes=request.schedule_interval_minutes,
        threshold_config=ThresholdConfig(
            enabled=request.threshold_enabled,
            operator=request.threshold_operator,
            value=request.threshold_value
        )
    )
    
    saved = repository.create_metric(metric)
    
    # 즉시 SQL 생성 및 테스트 (백그라운드)
    try:
        graph = create_agent_graph()
        result = graph.invoke({
            "user_query": saved.natural_query,
            "metric_id": saved.id,
            "threshold_config": {
                "enabled": saved.threshold_config.enabled,
                "operator": saved.threshold_config.operator,
                "value": saved.threshold_config.value
            },
            "relevant_tables": None,
            "generated_sql": None,
            "sql_valid": None,
            "query_result": None,
            "history_id": None,
            "anomaly_detected": None,
            "anomaly_id": None,
            "notification_sent": None,
            "error": None,
            "retry_count": 0,
            "final_answer": None
        })
        
        # SQL 캐싱
        if result.get('generated_sql') and not result.get('error'):
            saved.sql_query = result['generated_sql']
            saved.sql_generated_at = datetime.utcnow()
            repository.update_metric(saved.id, saved)
    except Exception as e:
        # SQL 생성 실패해도 지표는 생성됨 (스케줄러에서 재시도)
        print(f"SQL 생성 실패 (스케줄러에서 재시도): {e}")
    
    return MetricResponse(
        id=saved.id,
        name=saved.name,
        natural_query=saved.natural_query,
        sql_query=saved.sql_query,
        status=saved.status.value,
        threshold_config=saved.threshold_config.model_dump(),
        created_at=saved.created_at,
        sql_generated_at=saved.sql_generated_at
    )


@router.get("", response_model=MetricListResponse)
async def list_metrics(status: Optional[str] = None):
    """지표 목록 조회"""
    metric_status = MetricStatus(status) if status else None
    metrics = repository.list_metrics(status=metric_status)
    
    return MetricListResponse(
        total=len(metrics),
        items=[
            MetricResponse(
                id=m.id,
                name=m.name,
                natural_query=m.natural_query,
                sql_query=m.sql_query,
                status=m.status.value,
                threshold_config=m.threshold_config.model_dump(),
                created_at=m.created_at,
                sql_generated_at=m.sql_generated_at
            )
            for m in metrics
        ]
    )


@router.get("/{metric_id}", response_model=MetricDetailResponse)
async def get_metric(metric_id: str):
    """지표 상세 조회 (히스토리 포함)"""
    metric = repository.get_metric(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="지표를 찾을 수 없습니다")
    
    # 히스토리 조회 (최근 24개 = 24시간)
    histories = repository.list_histories(metric_id=metric_id, limit=24)
    
    # 이상 개수
    anomalies = repository.list_anomalies(metric_id=metric_id, resolved=False)
    
    # 최신 값
    latest = histories[0] if histories else None
    
    return MetricDetailResponse(
        metric=MetricResponse(
            id=metric.id,
            name=metric.name,
            natural_query=metric.natural_query,
            sql_query=metric.sql_query,
            status=metric.status.value,
            threshold_config=metric.threshold_config.model_dump(),
            created_at=metric.created_at,
            sql_generated_at=metric.sql_generated_at
        ),
        latest_value=latest.result_value if latest else None,
        latest_executed_at=latest.executed_at if latest else None,
        history=[
            HistoryResponse(
                id=h.id,
                executed_at=h.executed_at,
                result_type=h.result_type.value,
                result_value=h.result_value,
                result_data=h.result_data,
                status=h.status.value
            )
            for h in histories
        ],
        anomalies_count=len(anomalies)
    )


@router.delete("/{metric_id}")
async def delete_metric(metric_id: str):
    """지표 삭제"""
    success = repository.delete_metric(metric_id)
    if not success:
        raise HTTPException(status_code=404, detail="지표를 찾을 수 없습니다")
    
    return {"message": "지표가 삭제되었습니다"}
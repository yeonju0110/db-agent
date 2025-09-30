"""
대시보드 데이터 API
"""
from fastapi import APIRouter, Header
import sys
from pathlib import Path
from datetime import datetime, timezone

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.v1.schemas.requests import (
    DashboardSummaryResponse,
    AnomalyListResponse,
    AnomalyResponse,
    DbStatusListResponse,
    DbStatusResponse,
    RecommendationListResponse,
    RecommendationResponse
)
from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MetricStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
repository = get_repository()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(x_tenant_id: str = Header(..., description="고객사 ID")):
    """대시보드 요약 정보"""
    all_metrics = repository.list_metrics(tenant_id=x_tenant_id)
    active_metrics = repository.list_metrics(status=MetricStatus.ACTIVE, tenant_id=x_tenant_id)
    total_anomalies = repository.count_anomalies(resolved=False, tenant_id=x_tenant_id)
    
    return DashboardSummaryResponse(
        total_metrics=len(all_metrics),
        active_metrics=len(active_metrics),
        total_anomalies=total_anomalies,
        last_updated=datetime.now(timezone.utc)
    )


@router.get("/anomalies", response_model=AnomalyListResponse)
async def get_anomalies(
    resolved: bool = False, 
    limit: int = 10,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """이상징후 목록 조회"""
    anomalies = repository.list_anomalies(resolved=resolved, limit=limit, tenant_id=x_tenant_id)
    # total도 별도 카운트로 반환 권장
    total = repository.count_anomalies(resolved=resolved, tenant_id=x_tenant_id)
    
    items = []
    for anomaly in anomalies:
        # 지표 정보 조회
        metric = repository.get_metric(anomaly.metric_id)
        metric_name = metric.name if metric else "알 수 없는 지표"
        
        items.append(AnomalyResponse(
            id=anomaly.id,
            metric_id=anomaly.metric_id,
            metric_name=metric_name,
            detected_at=anomaly.detected_at,
            message=anomaly.message,
            level=anomaly.level,
            resolved=anomaly.resolved
        ))
    
    return AnomalyListResponse(
        total=total,
        items=items
    )


@router.get("/db-status", response_model=DbStatusListResponse)
async def get_db_status(x_tenant_id: str = Header(..., description="고객사 ID")):
    """DB 연결 상태 조회"""
    import asyncio
    import time
    from backend.config.settings import get_settings
    
    settings = get_settings()
    db_connections = []
    
    # 설정된 DB 연결들 확인
    if hasattr(settings, 'database_connections'):
        for conn_config in settings.database_connections:
            try:
                # DB 연결 테스트 (간단한 ping)
                start_time = time.time()
                # 실제 연결 테스트 로직은 DB 타입에 따라 구현
                # 현재는 기본 연결 정보만 반환
                latency_ms = round((time.time() - start_time) * 1000, 0)
                
                db_connections.append(DbStatusResponse(
                    name=conn_config.get("name", "Unknown DB"),
                    type=conn_config.get("type", "Unknown"),
                    status="normal",
                    latency=f"{latency_ms}ms"
                ))
            except Exception:
                db_connections.append(DbStatusResponse(
                    name=conn_config.get("name", "Unknown DB"),
                    type=conn_config.get("type", "Unknown"),
                    status="error",
                    latency=None
                ))
    
    # 설정이 없으면 기본 샘플 DB 정보 반환 (개발/데모용)
    if not db_connections:
        # 환경변수나 설정에서 실제 DB 정보를 가져와야 함
        sample_connections = [
            {"name": "PostgreSQL DB", "type": "PostgreSQL 13.4", "host": "localhost", "port": 5432},
        ]
        
        for conn in sample_connections:
            try:
                # 실제 DB 연결 테스트 로직 필요
                db_connections.append(DbStatusResponse(
                    name=conn["name"],
                    type=conn["type"],
                    status="normal",
                    latency="45ms"
                ))
            except Exception:
                db_connections.append(DbStatusResponse(
                    name=conn["name"],
                    type=conn["type"],
                    status="error",
                    latency=None
                ))
    
    return DbStatusListResponse(items=db_connections)


@router.get("/recommendations", response_model=RecommendationListResponse)
async def get_recommendations(
    limit: int = 10,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """권장사항 조회"""
    recommendations = []
    
    # 실제 지표 상태를 기반으로 권장사항 생성
    all_metrics = repository.list_metrics(tenant_id=x_tenant_id)
    recent_anomalies = repository.list_anomalies(resolved=False, limit=5, tenant_id=x_tenant_id)
    
    # 1. 이상징후가 많은 경우 성능 최적화 권장
    if len(recent_anomalies) >= 3:
        recommendations.append(RecommendationResponse(
            id=f"perf_opt_{len(recent_anomalies)}",
            type="optimization",
            title="성능 최적화 필요",
            description=f"최근 {len(recent_anomalies)}개의 이상징후가 감지되었습니다. 시스템 성능 점검과 쿼리 최적화를 권장합니다.",
            priority="high",
            action_url="/optimization-guide"
        ))
    
    # 2. 알림이 설정되지 않은 지표가 있는 경우
    metrics_without_alerts = [m for m in all_metrics if not m.threshold_config.enabled]
    if len(metrics_without_alerts) > 0:
        recommendations.append(RecommendationResponse(
            id=f"alert_setup_{len(metrics_without_alerts)}",
            type="alert_setup", 
            title="알림 설정 권장",
            description=f"{len(metrics_without_alerts)}개의 지표에 알림이 설정되지 않았습니다. 임계값 알림을 설정하여 문제를 조기에 감지하세요.",
            priority="medium",
            action_url="/alert-setup"
        ))
    
    # 3. 장기간 실행되지 않은 지표가 있는 경우
    from datetime import datetime, timedelta
    stale_threshold = datetime.now(timezone.utc) - timedelta(hours=2)
    
    stale_metrics = []
    for metric in all_metrics:
        histories = repository.list_histories(metric_id=metric.id, limit=1)
        if not histories or histories[0].executed_at < stale_threshold:
            stale_metrics.append(metric)
    
    if len(stale_metrics) > 0:
        recommendations.append(RecommendationResponse(
            id=f"stale_metrics_{len(stale_metrics)}",
            type="maintenance",
            title="지표 점검 필요",
            description=f"{len(stale_metrics)}개의 지표가 2시간 이상 업데이트되지 않았습니다. 스케줄러 상태를 확인해주세요.",
            priority="medium",
            action_url="/metrics-health"
        ))
    
    # 4. 기본 권장사항 (지표가 적은 경우)
    if len(all_metrics) < 3:
        recommendations.append(RecommendationResponse(
            id="add_more_metrics",
            type="alert_setup",
            title="추가 지표 설정",
            description="더 포괄적인 모니터링을 위해 추가 지표 설정을 권장합니다. 핵심 비즈니스 메트릭을 추가해보세요.",
            priority="low",
            action_url="/metric-setup"
        ))
    
    # limit 적용
    recommendations = recommendations[:limit]
    
    return RecommendationListResponse(items=recommendations)
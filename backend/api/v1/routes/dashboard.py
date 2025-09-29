"""
대시보드 데이터 API
"""
from fastapi import APIRouter
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.v1.schemas.requests import DashboardSummaryResponse
from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MetricStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
repository = get_repository()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary():
    """대시보드 요약 정보"""
    all_metrics = repository.list_metrics()
    active_metrics = repository.list_metrics(status=MetricStatus.ACTIVE)
    all_anomalies = repository.list_anomalies(resolved=False)
    
    return DashboardSummaryResponse(
        total_metrics=len(all_metrics),
        active_metrics=len(active_metrics),
        total_anomalies=len(all_anomalies),
        last_updated=datetime.utcnow()
    )
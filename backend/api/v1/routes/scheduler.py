"""
스케줄러 관리 API
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.scheduler_service import get_scheduler_service
from backend.api.v1.schemas.requests import SchedulerStatusResponse, SchedulerControlRequest

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """스케줄러 상태 조회"""
    scheduler_service = get_scheduler_service()
    status = scheduler_service.get_status()
    
    return SchedulerStatusResponse(
        is_running=status["is_running"],
        start_time=status["start_time"],
        interval_minutes=status["interval_minutes"],
        active_metrics_count=status["active_metrics_count"],
        uptime_seconds=status["uptime_seconds"]
    )


@router.post("/start")
async def start_scheduler(
    request: SchedulerControlRequest,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """스케줄러 시작"""
    scheduler_service = get_scheduler_service()
    
    try:
        await scheduler_service.start(request.interval_minutes)
        return {"message": f"스케줄러가 시작되었습니다 (간격: {request.interval_minutes}분)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 시작 실패: {str(e)}")


@router.post("/stop")
async def stop_scheduler(
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """스케줄러 중지"""
    scheduler_service = get_scheduler_service()
    
    try:
        await scheduler_service.stop()
        return {"message": "스케줄러가 중지되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 중지 실패: {str(e)}")


@router.post("/restart")
async def restart_scheduler(
    request: SchedulerControlRequest,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """스케줄러 재시작"""
    scheduler_service = get_scheduler_service()
    
    try:
        await scheduler_service.restart(request.interval_minutes)
        return {"message": f"스케줄러가 재시작되었습니다 (간격: {request.interval_minutes}분)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 재시작 실패: {str(e)}")


@router.post("/execute-all")
async def execute_all_metrics_now(
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """모든 활성 지표 즉시 실행"""
    scheduler_service = get_scheduler_service()
    
    if not scheduler_service.is_running:
        raise HTTPException(status_code=400, detail="스케줄러가 실행 중이 아닙니다")
    
    try:
        result = await scheduler_service.execute_all_metrics_now()
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지표 실행 실패: {str(e)}")


@router.post("/execute/{metric_id}")
async def execute_metric_now(
    metric_id: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """특정 지표 즉시 실행"""
    scheduler_service = get_scheduler_service()
    
    if not scheduler_service.is_running:
        raise HTTPException(status_code=400, detail="스케줄러가 실행 중이 아닙니다")
    
    try:
        result = await scheduler_service.execute_metric_now(metric_id)
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지표 실행 실패: {str(e)}")

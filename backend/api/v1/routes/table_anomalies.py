from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.table_anomaly_service import TableAnomalyService

router = APIRouter(prefix="/api/table-anomalies", tags=["table-anomalies"])

# 서비스 인스턴스
anomaly_service = TableAnomalyService()


@router.get("")
async def get_table_anomalies(
    table_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """테이블 이상치 목록 조회"""
    try:
        anomalies = await anomaly_service.get_anomalies(
            table_name=table_name,
            status=status,
            limit=limit,
            tenant_id=x_tenant_id
        )
        
        return {
            "items": anomalies,
            "total": len(anomalies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def scan_table_anomalies(
    table_name: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """테이블 이상치 수동 검사"""
    try:
        result = await anomaly_service.scan_table_anomalies(table_name, x_tenant_id)
        
        return {
            "success": True,
            "data": result,
            "message": f"{table_name} 테이블 이상치 검사가 완료되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{detection_id}/details")
async def get_anomaly_details(
    detection_id: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """이상치 상세 정보 조회"""
    try:
        details = await anomaly_service.get_anomaly_details(detection_id, x_tenant_id)
        
        return {
            "items": details,
            "total": len(details)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{detection_id}/acknowledge")
async def acknowledge_anomaly(
    detection_id: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """이상치 확인 처리"""
    try:
        result = await anomaly_service.acknowledge_anomaly(detection_id, x_tenant_id)
        
        return {
            "success": True,
            "message": "이상치가 확인 처리되었습니다.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_anomaly_summary(
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """이상치 요약 정보"""
    try:
        summary = await anomaly_service.get_anomaly_summary(x_tenant_id)
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{detection_id}")
async def delete_anomaly_detection(
    detection_id: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """이상치 검사 결과 삭제"""
    try:
        success = await anomaly_service.delete_anomaly_detection(detection_id, x_tenant_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Anomaly detection not found")
        
        return {"success": True, "message": "이상치 검사 결과가 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/table/{table_name}")
async def delete_table_anomalies(
    table_name: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """특정 테이블의 모든 이상치 검사 결과 삭제"""
    try:
        success = await anomaly_service.delete_table_anomalies(table_name, x_tenant_id)
        
        return {
            "success": True, 
            "message": f"{table_name} 테이블의 모든 이상치 검사 결과가 삭제되었습니다.",
            "deleted_count": success
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

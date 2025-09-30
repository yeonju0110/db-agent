"""
DB 연결 관리 API
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import sys
from pathlib import Path
import time
import psycopg2
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.v1.schemas.requests import (
    CreateDbConnectionRequest,
    DbConnectionResponse,
    DbConnectionListResponse,
    ConnectionTestResponse,
    SetupResponse,
    SetupStatusResponse,
    SetupStepResponse
)
from backend.models.db_connection import (
    DbConnection,
    SetupStatus,
    SetupStep,
    get_setup_status,
    set_setup_status,
    clear_setup_status
)
from backend.repositories.db_connection_repository import get_db_connection_repository

router = APIRouter(prefix="/api/db-connections", tags=["db-connections"])

# Cosmos DB 리포지토리
db_repository = get_db_connection_repository()


@router.post("", response_model=DbConnectionResponse)
async def create_connection(
    request: CreateDbConnectionRequest, 
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """DB 연결 생성"""
    connection = DbConnection(
        name=request.name,
        db_type="postgres",
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password=request.password,
        status="inactive"
    )
    
    # Cosmos DB에 저장
    saved_connection = db_repository.create_connection(connection, x_tenant_id)
    
    return DbConnectionResponse(
        id=saved_connection.id,
        name=saved_connection.name,
        db_type=saved_connection.db_type,
        host=saved_connection.host,
        port=saved_connection.port,
        database=saved_connection.database,
        username=saved_connection.username,
        created_at=saved_connection.created_at,
        status=saved_connection.status,
        last_tested_at=saved_connection.last_tested_at
    )


@router.get("", response_model=DbConnectionListResponse)
async def list_connections(x_tenant_id: str = Header(..., description="고객사 ID")):
    """DB 연결 목록 조회"""
    connections = db_repository.list_connections(x_tenant_id)
    
    items = []
    for conn in connections:
        items.append(DbConnectionResponse(
            id=conn.id,
            name=conn.name,
            db_type=conn.db_type,
            host=conn.host,
            port=conn.port,
            database=conn.database,
            username=conn.username,
            created_at=conn.created_at,
            status=conn.status,
            last_tested_at=conn.last_tested_at
        ))
    
    return DbConnectionListResponse(
        total=len(items),
        items=items
    )


@router.get("/{connection_id}", response_model=DbConnectionResponse)
async def get_connection(connection_id: str, x_tenant_id: str = Header(..., description="고객사 ID")):
    """DB 연결 상세 조회"""
    connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not connection:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    return DbConnectionResponse(
        id=connection.id,
        name=connection.name,
        db_type=connection.db_type,
        host=connection.host,
        port=connection.port,
        database=connection.database,
        username=connection.username,
        created_at=connection.created_at,
        status=connection.status,
        last_tested_at=connection.last_tested_at
    )


@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_connection(connection_id: str, x_tenant_id: str = Header(..., description="고객사 ID")):
    """DB 연결 테스트"""
    result = db_repository.test_connection(connection_id, x_tenant_id)
    
    return ConnectionTestResponse(
        success=result["success"],
        message=result["message"],
        latency_ms=result.get("latency_ms"),
        tested_at=datetime.fromisoformat(result["tested_at"])
    )


@router.put("/{connection_id}", response_model=DbConnectionResponse)
async def update_connection(connection_id: str, request: CreateDbConnectionRequest, x_tenant_id: str = Header(..., description="고객사 ID")):
    """DB 연결 수정"""
    # 기존 연결 조회
    existing_connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not existing_connection:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    # 연결 정보 업데이트
    updated_connection = DbConnection(
        id=connection_id,
        name=request.name,
        db_type="postgres",
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password=request.password,
        status=existing_connection.status,  # 상태는 유지
        created_at=existing_connection.created_at,
        updated_at=datetime.utcnow(),
        last_tested_at=existing_connection.last_tested_at
    )
    
    # Cosmos DB에 업데이트
    saved_connection = db_repository.update_connection(updated_connection, x_tenant_id)
    if not saved_connection:
        raise HTTPException(status_code=500, detail="연결 수정에 실패했습니다")
    
    return DbConnectionResponse(
        id=saved_connection.id,
        name=saved_connection.name,
        db_type=saved_connection.db_type,
        host=saved_connection.host,
        port=saved_connection.port,
        database=saved_connection.database,
        username=saved_connection.username,
        created_at=saved_connection.created_at,
        status=saved_connection.status,
        last_tested_at=saved_connection.last_tested_at
    )


@router.delete("/{connection_id}")
async def delete_connection(connection_id: str, x_tenant_id: str = Header(..., description="고객사 ID")):
    """DB 연결 삭제"""
    success = db_repository.delete_connection(connection_id, x_tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    return {"message": "연결이 삭제되었습니다"}


@router.post("/{connection_id}/setup", response_model=SetupResponse)
async def start_setup(connection_id: str, x_tenant_id: str = Header(..., description="고객사 ID")):
    """설정 파이프라인 시작"""
    connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not connection:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    # 설정 단계 정의
    steps = [
        SetupStep(name="연결 테스트", message="DB 연결을 확인합니다"),
        SetupStep(name="스키마 추출", message="데이터베이스 스키마를 분석합니다"),
        SetupStep(name="AI 초안 생성", message="비즈니스 컨텍스트를 생성합니다"),
        SetupStep(name="컨텍스트 적용", message="스키마에 비즈니스 정보를 적용합니다"),
        SetupStep(name="검색 인덱싱", message="Azure AI Search에 인덱싱합니다")
    ]
    
    setup_status = SetupStatus(
        tenant_id=x_tenant_id,
        connection_id=connection_id,
        status="running",
        steps=steps,
        started_at=datetime.utcnow(),
        total_steps=len(steps)
    )
    
    set_setup_status(x_tenant_id, connection_id, setup_status)
    
    # 백그라운드에서 설정 실행 (실제로는 별도 스레드나 큐에서 실행)
    import asyncio
    import threading
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_setup_pipeline(connection_id, x_tenant_id))
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_in_thread)
    thread.daemon = True
    thread.start()
    
    return SetupResponse(
        connection_id=connection_id,
        setup_id=f"setup_{connection_id}",
        message="설정이 시작되었습니다"
    )


@router.get("/{connection_id}/setup-status", response_model=SetupStatusResponse)
async def get_setup_status_endpoint(
    connection_id: str,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """설정 진행 상태 조회"""
    setup_status = get_setup_status(x_tenant_id, connection_id)
    if not setup_status:
        raise HTTPException(status_code=404, detail="설정 상태를 찾을 수 없습니다")
    
    # 진행률 계산
    completed_steps = sum(1 for step in setup_status.steps if step.status == "success")
    progress_percentage = (completed_steps / setup_status.total_steps) * 100 if setup_status.total_steps > 0 else 0
    
    return SetupStatusResponse(
        connection_id=setup_status.connection_id,
        status=setup_status.status,
        steps=[
            SetupStepResponse(
                name=step.name,
                status=step.status,
                message=step.message,
                started_at=step.started_at,
                completed_at=step.completed_at,
                error_details=step.error_details
            )
            for step in setup_status.steps
        ],
        started_at=setup_status.started_at,
        completed_at=setup_status.completed_at,
        current_step=setup_status.current_step,
        total_steps=setup_status.total_steps,
        progress_percentage=progress_percentage
    )


async def run_setup_pipeline(connection_id: str, x_tenant_id: str = "default_tenant"):
    """설정 파이프라인 실행 (백그라운드)"""
    print(f"🚀 설정 파이프라인 시작: {connection_id}")
    setup_status = get_setup_status(x_tenant_id, connection_id)
    if not setup_status:
        print(f"❌ 설정 상태를 찾을 수 없음: {connection_id}")
        return
    
    try:
        # 1. 연결 테스트
        print(f"📋 1단계: 연결 테스트 시작")
        await update_step_status(x_tenant_id, connection_id, 0, "running", "DB 연결을 확인합니다...")
        test_result = await test_connection_internal(connection_id, x_tenant_id)
        print(f"📋 1단계 결과: {test_result}")
        if not test_result["success"]:
            await update_step_status(x_tenant_id, connection_id, 0, "error", "연결 테스트 실패", test_result["error"])
            await update_setup_status(x_tenant_id, connection_id, "error")
            return
        await update_step_status(x_tenant_id, connection_id, 0, "success", "연결 테스트 완료")
        
        # 2. 스키마 추출
        await update_step_status(x_tenant_id, connection_id, 1, "running", "스키마를 추출합니다...")
        schema_result = await extract_schema(connection_id, x_tenant_id)
        if not schema_result["success"]:
            await update_step_status(x_tenant_id, connection_id, 1, "error", "스키마 추출 실패", schema_result["error"])
            await update_setup_status(x_tenant_id, connection_id, "error")
            return
        await update_step_status(x_tenant_id, connection_id, 1, "success", "스키마 추출 완료")
        
        # 3. AI 초안 생성
        await update_step_status(x_tenant_id, connection_id, 2, "running", "AI로 비즈니스 컨텍스트를 생성합니다...")
        ai_result = await generate_business_context(connection_id, x_tenant_id)
        if not ai_result["success"]:
            await update_step_status(x_tenant_id, connection_id, 2, "error", "AI 초안 생성 실패", ai_result["error"])
            await update_setup_status(x_tenant_id, connection_id, "error")
            return
        await update_step_status(x_tenant_id, connection_id, 2, "success", "AI 초안 생성 완료")
        
        # 4. 컨텍스트 적용
        await update_step_status(x_tenant_id, connection_id, 3, "running", "비즈니스 컨텍스트를 적용합니다...")
        context_result = await apply_business_context(connection_id, x_tenant_id)
        if not context_result["success"]:
            await update_step_status(x_tenant_id, connection_id, 3, "error", "컨텍스트 적용 실패", context_result["error"])
            await update_setup_status(x_tenant_id, connection_id, "error")
            return
        await update_step_status(x_tenant_id, connection_id, 3, "success", "컨텍스트 적용 완료")
        
        # 5. 검색 인덱싱
        await update_step_status(x_tenant_id, connection_id, 4, "running", "Azure AI Search에 인덱싱합니다...")
        index_result = await index_to_ai_search(connection_id, x_tenant_id)
        if not index_result["success"]:
            await update_step_status(x_tenant_id, connection_id, 4, "error", "인덱싱 실패", index_result["error"])
            await update_setup_status(x_tenant_id, connection_id, "error")
            return
        await update_step_status(x_tenant_id, connection_id, 4, "success", "인덱싱 완료")
        
        # 전체 완료
        print(f"✅ 설정 파이프라인 완료: {connection_id}")
        await update_setup_status(x_tenant_id, connection_id, "success")
        
    except Exception as e:
        print(f"❌ 설정 파이프라인 오류: {e}")
        await update_setup_status(x_tenant_id, connection_id, "error")


async def update_step_status(tenant_id: str, connection_id: str, step_index: int, status: str, message: str, error_details: str = None):
    """단계 상태 업데이트"""
    setup_status = get_setup_status(tenant_id, connection_id)
    if setup_status and 0 <= step_index < len(setup_status.steps):
        step = setup_status.steps[step_index]
        step.status = status
        step.message = message
        step.error_details = error_details
        
        if status == "running" and not step.started_at:
            step.started_at = datetime.utcnow()
        elif status in ["success", "error"]:
            step.completed_at = datetime.utcnow()
        
        setup_status.current_step = step_index
        set_setup_status(tenant_id, connection_id, setup_status)


async def update_setup_status(tenant_id: str, connection_id: str, status: str):
    """전체 설정 상태 업데이트"""
    setup_status = get_setup_status(tenant_id, connection_id)
    if setup_status:
        setup_status.status = status
        if status in ["success", "error"]:
            setup_status.completed_at = datetime.utcnow()
        set_setup_status(tenant_id, connection_id, setup_status)


# 서비스 임포트
from backend.services.schema_service import SchemaService
from backend.services.business_context_service import BusinessContextService
from backend.services.ai_search_service import AISearchService

# 서비스 인스턴스
schema_service = SchemaService()
business_context_service = BusinessContextService()
ai_search_service = AISearchService()


# 실제 구현 함수들
async def test_connection_internal(connection_id: str, x_tenant_id: str = "default_tenant") -> dict:
    """내부 연결 테스트"""
    result = db_repository.test_connection(connection_id, x_tenant_id)
    return {
        "success": result["success"],
        "error": result.get("message") if not result["success"] else None
    }


async def extract_schema(connection_id: str, x_tenant_id: str = "default_tenant") -> dict:
    """스키마 추출"""
    connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not connection:
        return {"success": False, "error": "연결 정보 없음"}
    
    return await schema_service.extract_schema(connection)


async def generate_business_context(connection_id: str, x_tenant_id: str = "default_tenant") -> dict:
    """AI 비즈니스 컨텍스트 생성"""
    connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not connection:
        return {"success": False, "error": "연결 정보 없음"}
    
    return await business_context_service.generate_business_context(connection)


async def apply_business_context(connection_id: str, x_tenant_id: str = "default_tenant") -> dict:
    """비즈니스 컨텍스트 적용"""
    connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not connection:
        return {"success": False, "error": "연결 정보 없음"}
    
    return await business_context_service.apply_business_context(connection)


async def index_to_ai_search(connection_id: str, x_tenant_id: str = "default_tenant") -> dict:
    """Azure AI Search 인덱싱"""
    connection = db_repository.get_connection(connection_id, x_tenant_id)
    if not connection:
        return {"success": False, "error": "연결 정보 없음"}
    
    return await ai_search_service.index_schema(connection)

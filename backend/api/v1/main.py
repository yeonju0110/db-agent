"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 라우터 임포트
from backend.api.v1.routes import metrics, query, dashboard, db_connections, scheduler, table_anomalies

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.scheduler_service import start_scheduler_service, stop_scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 스케줄러 서비스 시작 (5분 간격으로 변경)
    print("🚀 애플리케이션 시작 - 스케줄러 서비스 시작")
    await start_scheduler_service(interval_minutes=5)
    
    yield
    
    # 종료 시 스케줄러 서비스 중지
    print("🛑 애플리케이션 종료 - 스케줄러 서비스 중지")
    await stop_scheduler_service()


# FastAPI 앱 생성
app = FastAPI(
    title="DB Monitoring Pro API",
    description="자연어 기반 DB 모니터링 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(metrics.router)
app.include_router(query.router)
app.include_router(dashboard.router)
app.include_router(db_connections.router)
app.include_router(scheduler.router)
app.include_router(table_anomalies.router)


@app.get("/")
async def root():
    """헬스체크"""
    return {
        "status": "ok",
        "service": "DB Monitoring Pro API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """헬스체크 (상세)"""
    from backend.services.scheduler_service import get_scheduler_service
    
    scheduler_service = get_scheduler_service()
    scheduler_status = scheduler_service.get_status()
    
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "cosmos_db": "up",
            "postgres": "up",
            "scheduler": "up" if scheduler_status["is_running"] else "down"
        },
        "scheduler": {
            "is_running": scheduler_status["is_running"],
            "active_metrics_count": scheduler_status["active_metrics_count"],
            "uptime_seconds": scheduler_status["uptime_seconds"]
        }
    }
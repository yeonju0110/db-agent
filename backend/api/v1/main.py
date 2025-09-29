"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 임포트
from backend.api.v1.routes import metrics, query, dashboard

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# FastAPI 앱 생성
app = FastAPI(
    title="DB Monitoring Pro API",
    description="자연어 기반 DB 모니터링 시스템",
    version="1.0.0"
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
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "cosmos_db": "up",
            "postgres": "up"
        }
    }
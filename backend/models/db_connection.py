"""
DB 연결 모델
"""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class DbConnection(BaseModel):
    """DB 연결 정보"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="연결 이름")
    db_type: str = Field(..., description="DB 타입 (postgres, mysql, etc.)")
    host: str = Field(..., description="호스트")
    port: int = Field(..., description="포트")
    database: str = Field(..., description="데이터베이스명")
    username: str = Field(..., description="사용자명")
    password: str = Field(..., description="비밀번호 (암호화 필요)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None
    status: str = Field(default="inactive", description="연결 상태 (active, inactive, error)")
    last_tested_at: Optional[datetime] = None


class SetupStep(BaseModel):
    """설정 단계"""
    name: str
    status: str = "pending"  # pending, running, success, error
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None


class SetupStatus(BaseModel):
    """설정 진행 상태"""
    tenant_id: str
    connection_id: str
    status: str = "pending"  # pending, running, success, error
    steps: list[SetupStep] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: int = 0
    total_steps: int = 0


# 전역 상태 저장소 (메모리 기반)
_setup_statuses: dict[str, SetupStatus] = {}


def get_setup_status(tenant_id: str, connection_id: str) -> Optional[SetupStatus]:
    """설정 상태 조회"""
    return _setup_statuses.get(f"{tenant_id}:{connection_id}")


def set_setup_status(tenant_id: str, connection_id: str, status: SetupStatus) -> None:
    """설정 상태 저장"""
    _setup_statuses[f"{tenant_id}:{connection_id}"] = status


def clear_setup_status(tenant_id: str, connection_id: str) -> None:
    """설정 상태 삭제"""
    _setup_statuses.pop(f"{tenant_id}:{connection_id}", None)

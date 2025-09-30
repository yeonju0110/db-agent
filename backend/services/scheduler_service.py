"""
스케줄러 서비스
백그라운드에서 지표 스케줄러를 실행하고 관리
"""
import asyncio
import threading
from datetime import datetime, UTC
from typing import Optional, Dict, Any
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.scheduler.metric_scheduler import MetricScheduler
from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MetricStatus
from backend.config.settings import get_settings

settings = get_settings()


class SchedulerService:
    """스케줄러 서비스 싱글톤"""
    
    _instance: Optional['SchedulerService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.scheduler: Optional[MetricScheduler] = None
        self.scheduler_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.repository = get_repository()
        
        # 스케줄러 설정
        self.interval_minutes = settings.scheduler_interval_minutes
        self.auto_start = True  # 자동 시작 여부
    
    async def start(self, interval_minutes: int = None):
        """스케줄러 시작"""
        if self.is_running:
            print("[스케줄러 서비스] 이미 실행 중입니다")
            return
        
        if interval_minutes is None:
            interval_minutes = settings.scheduler_default_interval_minutes
        
        self.interval_minutes = interval_minutes
        self.scheduler = MetricScheduler(interval_minutes=interval_minutes)
        
        # 백그라운드 태스크로 실행
        self.scheduler_task = asyncio.create_task(self._run_scheduler())
        self.is_running = True
        self.start_time = datetime.now(UTC)
        
        print(f"[스케줄러 서비스] 시작됨 (간격: {interval_minutes}분)")
    
    async def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            print("[스케줄러 서비스] 실행 중이 아닙니다")
            return
        
        if self.scheduler:
            self.scheduler.stop()
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.is_running = False
        self.start_time = None
        print("[스케줄러 서비스] 중지됨")
    
    async def restart(self, interval_minutes: int = None):
        """스케줄러 재시작"""
        await self.stop()
        await asyncio.sleep(1)  # 잠시 대기
        await self.start(interval_minutes)
    
    async def _run_scheduler(self):
        """스케줄러 실행 루프"""
        try:
            await self.scheduler.start()
        except asyncio.CancelledError:
            print("[스케줄러 서비스] 취소됨")
        except Exception as e:
            print(f"[스케줄러 서비스] 오류 발생: {e}")
            self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회"""
        active_metrics_count = len(self.repository.list_metrics(status=MetricStatus.ACTIVE))
        
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "interval_minutes": self.interval_minutes,
            "active_metrics_count": active_metrics_count,
            "uptime_seconds": (
                (datetime.now(UTC) - self.start_time).total_seconds() 
                if self.start_time else 0
            )
        }
    
    async def execute_metric_now(self, metric_id: str) -> Dict[str, Any]:
        """특정 지표 즉시 실행"""
        if not self.scheduler:
            raise RuntimeError("스케줄러가 초기화되지 않았습니다")
        
        metric = self.repository.get_metric(metric_id)
        if not metric:
            raise ValueError(f"지표를 찾을 수 없습니다: {metric_id}")
        
        if metric.status != MetricStatus.ACTIVE:
            raise ValueError(f"비활성 지표입니다: {metric_id}")
        
        try:
            await self.scheduler.execute_metric(metric)
            return {"success": True, "message": "지표 실행 완료"}
        except Exception as e:
            return {"success": False, "message": f"지표 실행 실패: {str(e)}"}
    
    async def execute_all_metrics_now(self) -> Dict[str, Any]:
        """모든 활성 지표 즉시 실행"""
        if not self.scheduler:
            raise RuntimeError("스케줄러가 초기화되지 않았습니다")
        
        try:
            await self.scheduler.execute_all_metrics()
            return {"success": True, "message": "모든 지표 실행 완료"}
        except Exception as e:
            return {"success": False, "message": f"지표 실행 실패: {str(e)}"}


# 전역 인스턴스
scheduler_service = SchedulerService()


async def start_scheduler_service(interval_minutes: int = None):
    """스케줄러 서비스 시작 (애플리케이션 시작 시 호출)"""
    await scheduler_service.start(interval_minutes)


async def stop_scheduler_service():
    """스케줄러 서비스 중지 (애플리케이션 종료 시 호출)"""
    await scheduler_service.stop()


def get_scheduler_service() -> SchedulerService:
    """스케줄러 서비스 인스턴스 반환"""
    return scheduler_service

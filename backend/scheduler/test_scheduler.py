"""
테스트용 스케줄러 (1분 간격)
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.scheduler.metric_scheduler import MetricScheduler


async def main():
    # 1분 간격 테스트 스케줄러
    scheduler = MetricScheduler(interval_minutes=1)
    
    print("테스트 스케줄러 시작 (1분 간격)")
    print("중지하려면 Ctrl+C를 누르세요\n")
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
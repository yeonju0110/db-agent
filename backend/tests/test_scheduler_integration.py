"""
스케줄러 통합 테스트
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.scheduler_service import get_scheduler_service
from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MonitoringMetric, ThresholdConfig, MetricStatus


async def test_scheduler_service():
    """스케줄러 서비스 테스트"""
    print("🧪 스케줄러 서비스 테스트 시작")
    
    scheduler_service = get_scheduler_service()
    repository = get_repository()
    
    # 1. 스케줄러 상태 확인
    print("\n1. 초기 스케줄러 상태 확인")
    status = scheduler_service.get_status()
    print(f"   실행 상태: {status['is_running']}")
    print(f"   활성 지표 수: {status['active_metrics_count']}")
    
    # 2. 스케줄러 시작
    print("\n2. 스케줄러 시작 (1분 간격)")
    await scheduler_service.start(interval_minutes=1)
    
    status = scheduler_service.get_status()
    print(f"   실행 상태: {status['is_running']}")
    print(f"   시작 시간: {status['start_time']}")
    
    # 3. 테스트 지표 생성
    print("\n3. 테스트 지표 생성")
    test_metric = MonitoringMetric(
        name="테스트 지표 - 스케줄러",
        natural_query="오늘 주문 건수",
        sql_query="SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE",
        db_connection_id="test-db",
        schedule_interval_minutes=1,
        threshold_config=ThresholdConfig(
            enabled=True,
            operator=">",
            value=10
        )
    )
    
    saved_metric = repository.create_metric(test_metric)
    print(f"   지표 생성됨: {saved_metric.id}")
    
    # 4. 지표 즉시 실행 테스트
    print("\n4. 지표 즉시 실행 테스트")
    try:
        result = await scheduler_service.execute_metric_now(saved_metric.id)
        print(f"   실행 결과: {result}")
    except Exception as e:
        print(f"   실행 실패 (예상됨): {e}")
    
    # 5. 모든 지표 실행 테스트
    print("\n5. 모든 지표 실행 테스트")
    try:
        result = await scheduler_service.execute_all_metrics_now()
        print(f"   실행 결과: {result}")
    except Exception as e:
        print(f"   실행 실패 (예상됨): {e}")
    
    # 6. 스케줄러 상태 재확인
    print("\n6. 스케줄러 상태 재확인")
    status = scheduler_service.get_status()
    print(f"   실행 상태: {status['is_running']}")
    print(f"   활성 지표 수: {status['active_metrics_count']}")
    print(f"   가동 시간: {status['uptime_seconds']:.1f}초")
    
    # 7. 스케줄러 중지
    print("\n7. 스케줄러 중지")
    await scheduler_service.stop()
    
    status = scheduler_service.get_status()
    print(f"   실행 상태: {status['is_running']}")
    
    # 8. 테스트 지표 삭제
    print("\n8. 테스트 지표 삭제")
    repository.delete_metric(saved_metric.id)
    print("   테스트 지표 삭제됨")
    
    print("\n✅ 스케줄러 서비스 테스트 완료")


async def test_scheduler_api():
    """스케줄러 API 테스트"""
    print("\n🧪 스케줄러 API 테스트 시작")
    
    import httpx
    
    base_url = "http://localhost:8000"
    headers = {"X-Tenant-ID": "test"}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. 스케줄러 상태 조회
            print("\n1. 스케줄러 상태 조회")
            response = await client.get(f"{base_url}/api/scheduler/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"   상태: {data}")
            else:
                print(f"   실패: {response.status_code}")
            
            # 2. 스케줄러 시작
            print("\n2. 스케줄러 시작")
            response = await client.post(
                f"{base_url}/api/scheduler/start",
                json={"interval_minutes": 1},
                headers=headers
            )
            if response.status_code == 200:
                print(f"   시작 성공: {response.json()}")
            else:
                print(f"   시작 실패: {response.status_code}")
            
            # 3. 헬스체크 확인
            print("\n3. 헬스체크 확인")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   스케줄러 상태: {data.get('services', {}).get('scheduler')}")
            else:
                print(f"   헬스체크 실패: {response.status_code}")
            
        except Exception as e:
            print(f"   API 테스트 실패 (서버가 실행 중이지 않을 수 있음): {e}")
    
    print("\n✅ 스케줄러 API 테스트 완료")


async def main():
    """메인 테스트 함수"""
    print("🚀 스케줄러 통합 테스트 시작")
    print("=" * 60)
    
    try:
        await test_scheduler_service()
        await test_scheduler_api()
        
        print("\n" + "=" * 60)
        print("🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

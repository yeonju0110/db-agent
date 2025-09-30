"""
모니터링 지표 스케줄러
등록된 지표를 주기적으로 실행 (SQL 캐싱 지원)
"""
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Optional
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MetricStatus, MonitoringMetric
from backend.core.ai.agent_graph import create_agent_graph
from backend.core.ai.sql_executor import SQLExecutor
from backend.services.table_anomaly_service import TableAnomalyService


class MetricScheduler:
    """지표 스케줄러 (SQL 캐싱 지원)"""
    
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.repository = get_repository()
        self.graph = create_agent_graph()
        self.executor = SQLExecutor()
        self.table_anomaly_service = TableAnomalyService()
        self.running = False
    
    async def start(self):
        """스케줄러 시작"""
        self.running = True
        self._stop_evt = getattr(self, "_stop_evt", asyncio.Event())
        print(f"[스케줄러] 시작됨 (실행 주기: {self.interval_minutes}분)")
        
        while self.running:
            try:
                await self.execute_all_metrics()
                # interval 동안 대기하되, stop 이벤트 발생 시 즉시 종료
                try:
                    await asyncio.wait_for(self._stop_evt.wait(), timeout=self.interval_minutes * 60)
                    break
                except asyncio.TimeoutError:
                    self._stop_evt.clear()
                    pass
            except KeyboardInterrupt:
                print("\n[스케줄러] 중지 신호 수신")
                break
            except asyncio.CancelledError:
                # 태스크 취소는 상위로 전파
                raise
            except Exception as e:
                # TODO: 로거로 변경하여 스택 추적 남기기
                print(f"[스케줄러] 오류 발생: {e!r}")
                await asyncio.sleep(60)
    
    async def execute_all_metrics(self):
        """모든 활성 지표 실행"""
        print(f"\n{'='*80}")
        print(f"[스케줄러] 실행 시작: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"{'='*80}")
        
        metrics = self.repository.list_metrics(status=MetricStatus.ACTIVE)
        
        if not metrics:
            print("[스케줄러] 실행할 지표 없음")
            return
        
        print(f"[스케줄러] 실행할 지표 수: {len(metrics)}개\n")
        
        for idx, metric in enumerate(metrics, 1):
            print(f"\n[{idx}/{len(metrics)}] 지표: {metric.name}")
            print(f"  ID: {metric.id}")
            
            try:
                await self.execute_metric(metric)
            except Exception as e:
                print(f"  ❌ 실행 실패: {e}")
        
        # 테이블 이상치 검사 실행
        print(f"\n[테이블 이상치 검사] 시작")
        try:
            await self.execute_table_anomaly_detection()
        except Exception as e:
            print(f"  ❌ 테이블 이상치 검사 실패: {e}")
        
        print(f"\n{'='*80}")
        print(f"[스케줄러] 실행 완료")
        print(f"{'='*80}")
    
    async def execute_metric(self, metric: MonitoringMetric):
        """단일 지표 실행 (SQL 캐싱 로직)"""
        
        # SQL 재생성 필요 여부 확인
        should_regenerate = self._should_regenerate_sql(metric)
        
        if should_regenerate or not metric.sql_query:
            print(f"  → SQL 재생성 필요")
            await self._execute_with_generation(metric)
        else:
            print(f"  → 캐싱된 SQL 사용")
            await self._execute_cached_sql(metric)
    
    def _should_regenerate_sql(self, metric: MonitoringMetric) -> bool:
        """SQL 재생성 필요 여부 판단"""
        if not metric.use_cached_sql:
            return True
        
        if not metric.sql_query:
            return True
        
        # 24시간 이상 지났으면 재생성 (날짜 변경 대응)
        if metric.sql_generated_at:
            # metric.sql_generated_at가 naive라면 UTC로 간주
            gen_at = metric.sql_generated_at
            if gen_at.tzinfo is None:
                gen_at = gen_at.replace(tzinfo=UTC)
            age = datetime.now(UTC) - gen_at
            if age > timedelta(hours=24):
                print(f"  (SQL 생성 후 24시간 경과)")
                return True
        
        return False
    
    async def _execute_with_generation(self, metric: MonitoringMetric):
        """워크플로우 전체 실행 (SQL 생성 포함)"""
        initial_state = {
            "user_query": metric.natural_query,
            "metric_id": metric.id,
            "threshold_config": {
                "enabled": metric.threshold_config.enabled,
                "operator": metric.threshold_config.operator,
                "value": metric.threshold_config.value
            },
            "relevant_tables": None,
            "generated_sql": None,
            "sql_valid": None,
            "query_result": None,
            "history_id": None,
            "anomaly_detected": None,
            "anomaly_id": None,
            "notification_sent": None,
            "error": None,
            "retry_count": 0,
            "final_answer": None
        }
        
        result = await asyncio.to_thread(self.graph.invoke, initial_state)
        
        # 생성된 SQL을 캐싱
        if result.get('generated_sql') and not result.get('error'):
            metric.sql_query = result['generated_sql']
            metric.sql_generated_at = datetime.now(UTC)
            self.repository.update_metric(metric.id, metric)
            print(f"  ✅ SQL 캐싱 완료")
        
        self._print_result(result)
    
    async def _execute_cached_sql(self, metric: MonitoringMetric):
        """캐싱된 SQL만 실행 (빠른 경로)"""
        from backend.core.ai.graph_nodes import GraphNodes
        
        nodes = GraphNodes()
        
        # 간소화된 state (SQL 생성 생략)
        state = {
            "metric_id": metric.id,
            "generated_sql": metric.sql_query,
            "threshold_config": {
                "enabled": metric.threshold_config.enabled,
                "operator": metric.threshold_config.operator,
                "value": metric.threshold_config.value
            }
        }
        
        # SQL 실행 → 저장 → 이상 감지
        result = {}
        result.update(nodes.execute_sql_node(state))
        state.update(result)
        
        result.update(nodes.save_history_node(state))
        state.update(result)
        
        result.update(nodes.detect_anomaly_node(state))
        state.update(result)
        
        self._print_result(state)
    
    async def execute_table_anomaly_detection(self):
        """테이블 이상치 검사 실행"""
        # 모든 활성 지표에서 관련 테이블들 추출
        metrics = self.repository.list_metrics(status=MetricStatus.ACTIVE)
        monitored_tables = set()
        
        for metric in metrics:
            if metric.related_tables:
                for table in metric.related_tables:
                    # 스키마명 제거 (예: "public.orders" -> "orders")
                    table_name = table.split('.').pop() if '.' in table else table
                    monitored_tables.add(table_name.lower())
        
        if not monitored_tables:
            print("  → 모니터링 중인 테이블 없음")
            return
        
        print(f"  → 검사할 테이블: {', '.join(sorted(monitored_tables))}")
        
        for table_name in sorted(monitored_tables):
            try:
                print(f"  → {table_name} 테이블 검사 중...")
                result = await self.table_anomaly_service.scan_table_anomalies(table_name)
                print(f"    ✅ 완료: {result['total_records']}개 레코드, {result['anomaly_count']}개 이상치")
            except Exception as e:
                print(f"    ❌ 실패: {e}")
    
    def _print_result(self, result: dict):
        """실행 결과 출력"""
        if result.get('error'):
            print(f"  ❌ 오류: {result['error']}")
        else:
            print(f"  ✅ 성공")
            if result.get('history_id'):
                print(f"  히스토리: {result['history_id']}")
            if result.get('anomaly_detected'):
                print(f"  🚨 이상 감지됨!")
    
    def stop(self):
        """스케줄러 중지"""
        self.running = False
        if hasattr(self, "_stop_evt"):
            self._stop_evt.set()


async def main():
    scheduler = MetricScheduler(interval_minutes=60)
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║           DB Monitoring Pro - 스케줄러                    ║
╚══════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
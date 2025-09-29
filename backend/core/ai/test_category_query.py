"""
카테고리형 쿼리 테스트
"""
from datetime import datetime, UTC
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.ai.agent_graph import create_agent_graph
from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import MonitoringMetric, ThresholdConfig

# 테스트용 지표 생성
repository = get_repository()

# 카테고리형 지표: 주문 상태별 개수
test_metric = MonitoringMetric(
    name="테스트: 주문 상태별 분포",
    natural_query="주문 상태별 건수를 알려줘",
    sql_query="",
    db_connection_id="test-connection",
    threshold_config=ThresholdConfig(enabled=False)  # 카테고리형은 임계값 없음
)

saved_metric = repository.create_metric(test_metric)
print(f"생성된 지표 ID: {saved_metric.id}")

# 그래프 실행
graph = create_agent_graph()

initial_state = {
    "user_query": "주문 상태별 건수를 알려줘",
    "metric_id": saved_metric.id,
    "threshold_config": {"enabled": False},
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

print(f"\n{'='*80}")
print(f"워크플로우 시작")
print(f"{'='*80}")

result = graph.invoke(initial_state)

print(f"\n{'='*80}")
print(f"최종 답변: {result['final_answer']}")
print(f"히스토리 ID: {result.get('history_id')}")
print(f"{'='*80}")

# SQL 캐싱 추가
if result.get('generated_sql') and not result.get('error'):
    saved_metric.sql_query = result['generated_sql']
    saved_metric.sql_generated_at = datetime.now(UTC)
    repository.update_metric(saved_metric.id, saved_metric)
    print(f"\n✅ SQL 캐싱 완료: {result['generated_sql']}")

# 저장된 히스토리 확인
if result.get('history_id'):
    history = repository.get_history(result['history_id'])
    if history:
        print("\n저장된 데이터:")
        print(f"  유형: {history.result_type}")
        print(f"  단일 값: {history.result_value}")
        print(f"  다중 행: {history.result_data}")
    else:
        print("\n저장된 히스토리를 찾을 수 없습니다.")
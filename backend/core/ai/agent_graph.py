"""
LangGraph 에이전트 그래프 정의 - 확장 버전
"""
from langgraph.graph import StateGraph, END
import sys
from pathlib import Path
from datetime import datetime, UTC

# 프로젝트 루트를 sys.path에 추가 (임포트보다 먼저)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 상대 임포트를 절대 임포트 + try-except로 변경
try:
    from .graph_state import AgentState
    from .graph_nodes import GraphNodes
except ImportError:
    from graph_state import AgentState
    from graph_nodes import GraphNodes


def create_agent_graph():
    """에이전트 그래프 생성 (모니터링 기능 포함)"""
    
    nodes = GraphNodes()
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("search_tables", nodes.search_tables_node)
    workflow.add_node("generate_sql", nodes.generate_sql_node)
    workflow.add_node("validate_sql", nodes.validate_sql_node)
    workflow.add_node("execute_sql", nodes.execute_sql_node)
    workflow.add_node("save_history", nodes.save_history_node)
    workflow.add_node("detect_anomaly", nodes.detect_anomaly_node)
    workflow.add_node("send_notification", nodes.send_notification_node)
    workflow.add_node("format_result", nodes.format_result_node)
    
    # 엣지 연결
    workflow.set_entry_point("search_tables")
    workflow.add_edge("search_tables", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    
    # 조건부 분기: 검증 성공 시 실행, 실패 시 종료
    workflow.add_conditional_edges(
        "validate_sql",
        lambda state: "execute" if state.get("sql_valid") else "end",
        {
            "execute": "execute_sql",
            "end": "format_result"
        }
    )
    
    # 실행 후 히스토리 저장
    workflow.add_edge("execute_sql", "save_history")
    
    # 히스토리 저장 후 이상 감지
    workflow.add_edge("save_history", "detect_anomaly")
    
    # 조건부 분기: 이상 감지 시 알림, 아니면 결과 포맷팅
    workflow.add_conditional_edges(
        "detect_anomaly",
        lambda state: "notify" if state.get("anomaly_detected") else "format",
        {
            "notify": "send_notification",
            "format": "format_result"
        }
    )
    
    # 알림 후 결과 포맷팅
    workflow.add_edge("send_notification", "format_result")
    workflow.add_edge("format_result", END)
    
    return workflow.compile()


# 테스트
if __name__ == "__main__":
    from backend.repositories.monitoring_repository import get_repository
    from backend.models.monitoring import MonitoringMetric, ThresholdConfig
    
    repository = get_repository()
    
    test_metric = MonitoringMetric(
        name="테스트: 오늘 주문 건수",
        natural_query="오늘 주문 건수",
        sql_query="",
        db_connection_id="test-connection",
        threshold_config=ThresholdConfig(
            enabled=True,
            operator=">",
            value=10.0
        )
    )
    
    saved_metric = repository.create_metric(test_metric)
    print(f"생성된 지표 ID: {saved_metric.id}")
    
    graph = create_agent_graph()
    
    initial_state = {
        "user_query": "오늘 주문 건수",
        "metric_id": saved_metric.id,
        "threshold_config": {
            "enabled": True,
            "operator": ">",
            "value": 10.0
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
    
    print(f"\n{'='*80}")
    print(f"워크플로우 시작")
    print(f"{'='*80}")
    
    result = graph.invoke(initial_state)
    
    print(f"\n{'='*80}")
    print(f"최종 답변: {result['final_answer']}")
    print(f"히스토리 ID: {result.get('history_id')}")
    print(f"이상 감지: {result.get('anomaly_detected')}")
    print(f"{'='*80}")
    
    # ✨ SQL 캐싱 추가
    if result.get('generated_sql') and not result.get('error'):
        saved_metric.sql_query = result['generated_sql']
        saved_metric.sql_generated_at = datetime.now(UTC)
        repository.update_metric(saved_metric.id, saved_metric)
        print(f"\n✅ SQL 캐싱 완료: {result['generated_sql']}")
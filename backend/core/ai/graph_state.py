"""
LangGraph State 정의
노드 간 전달되는 데이터 구조
"""
from typing import TypedDict, List, Optional, Any, Dict, NotRequired, Required


class AgentState(TypedDict, total=False):
    """에이전트 상태"""
    # 입력
    user_query: Required[str]
    metric_id: NotRequired[Optional[str]]  # 모니터링 지표 ID (스케줄러에서 전달)
    
    # 중간 결과
    relevant_tables: NotRequired[List[dict]]  # schema_retriever 결과
    generated_sql: NotRequired[Optional[str]]  # sql_generator 결과
    sql_valid: NotRequired[Optional[bool]]  # 검증 결과
    
    # 실행 결과
    query_result: NotRequired[Optional[dict]]  # sql_executor 결과
    history_id: NotRequired[Optional[str]]  # 저장된 히스토리 ID
    
    # 이상 감지
    threshold_config: NotRequired[Optional[Dict[str, Any]]]  # 임계값 설정
    anomaly_detected: NotRequired[Optional[bool]]
    anomaly_id: NotRequired[Optional[str]]
    
    # 알림
    notification_sent: NotRequired[Optional[bool]]
    
    # 메타데이터
    error: NotRequired[Optional[str]]
    retry_count: Required[int]
    
    # 최종 출력
    final_answer: NotRequired[Optional[str]]
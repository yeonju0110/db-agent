"""
LangGraph State 정의
노드 간 전달되는 데이터 구조
"""
from typing import TypedDict, List, Optional, Any, Dict


class AgentState(TypedDict):
    """에이전트 상태"""
    # 입력
    user_query: str
    metric_id: Optional[str]  # 모니터링 지표 ID (스케줄러에서 전달)
    
    # 중간 결과
    relevant_tables: Optional[List[dict]]  # schema_retriever 결과
    generated_sql: Optional[str]  # sql_generator 결과
    sql_valid: Optional[bool]  # 검증 결과
    
    # 실행 결과
    query_result: Optional[dict]  # sql_executor 결과
    history_id: Optional[str]  # 저장된 히스토리 ID
    
    # 이상 감지
    threshold_config: Optional[Dict[str, Any]]  # 임계값 설정
    anomaly_detected: Optional[bool]
    anomaly_id: Optional[str]
    
    # 알림
    notification_sent: Optional[bool]
    
    # 메타데이터
    error: Optional[str]
    retry_count: int
    
    # 최종 출력
    final_answer: Optional[str]
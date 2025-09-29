"""
즉시 질문 API (테스트용)
"""
from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.v1.schemas.requests import QueryRequest, QueryResponse
from backend.core.ai.agent_graph import create_agent_graph

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    즉시 질문 실행 (테스트용)
    - 지표 등록 없이 즉시 실행
    - 결과는 저장되지 않음
    """
    graph = create_agent_graph()
    
    initial_state = {
        "user_query": request.question,
        "metric_id": None,  # 저장 안 함
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
    
    try:
        result = graph.invoke(initial_state)
        
        if result.get('error'):
            raise HTTPException(status_code=400, detail=result['error'])
        
        query_result = result.get('query_result', {})
        
        # 실행 시간 계산 (간단히)
        execution_time_ms = query_result.get('execution_time_ms', 0)
        
        # 결과 유형 판별
        data = query_result.get('data', [])
        if not data:
            result_type = "no_data"
            result_value = None
            result_data = None
        elif len(data) == 1 and len(data[0]) == 1:
            result_type = "single_value"
            result_value = list(data[0].values())[0]
            result_data = None
        else:
            result_type = "multiple_rows"
            result_value = None
            result_data = data
        
        # 사용된 테이블
        tables_used = [t['name'] for t in result.get('relevant_tables', [])]
        
        return QueryResponse(
            question=request.question,
            sql=result.get('generated_sql', ''),
            result_type=result_type,
            result_value=result_value,
            result_data=result_data,
            execution_time_ms=execution_time_ms,
            tables_used=tables_used
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
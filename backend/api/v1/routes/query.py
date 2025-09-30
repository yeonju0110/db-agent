"""
즉시 질문 API (테스트용)
"""
from fastapi import APIRouter, HTTPException, Header
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.v1.schemas.requests import QueryRequest, QueryResponse
from backend.core.ai.agent_graph import create_agent_graph
from backend.core.ai.sql_executor import SQLExecutor
from backend.core.ai.schema_retriever import SchemaRetriever

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
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


@router.post("/execute", response_model=QueryResponse)
async def execute_sql(
    request: QueryRequest,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """
    SQL 직접 실행 (테스트용)
    - 생성된 SQL을 직접 실행
    - 결과는 저장되지 않음
    """
    executor = SQLExecutor()
    
    try:
        # SQL 검증
        validation = executor.validate_query(request.question)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=f"SQL 검증 실패: {validation['error']}")
        
        # SQL 실행
        result = executor.execute_query(request.question)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"SQL 실행 실패: {result['error']}")
        
        # 결과 유형 판별
        data = result.get('data', [])
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
        
        return QueryResponse(
            question=request.question,
            sql=request.question,
            result_type=result_type,
            result_value=result_value,
            result_data=result_data,
            execution_time_ms=0,  # TODO: 실제 실행 시간 측정
            tables_used=[]  # TODO: 사용된 테이블 추출
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-tables")
async def recommend_tables(
    request: QueryRequest,
    x_tenant_id: str = Header(..., description="고객사 ID")
):
    """
    모니터링용 추천 테이블 목록 반환
    - 자연어 쿼리 기반으로 관련 테이블들을 점수순으로 추천
    - 사용자가 함께 모니터링할 테이블을 선택할 수 있도록 도움
    """
    try:
        retriever = SchemaRetriever()
        recommended_tables = retriever.get_recommended_tables(
            query=request.question,
            min_score=1.0,  # 최소 점수 임계값
            max_tables=5    # 최대 추천 개수
        )
        
        # 응답 형식 변환
        table_recommendations = []
        for table in recommended_tables:
            table_recommendations.append({
                "name": table.name,
                "description": table.description,
                "score": table.score,
                "columns_text": table.columns_text,
                "common_queries": table.common_queries,
                "recommendation_reason": _get_recommendation_reason(table.score)
            })
        
        return {
            "query": request.question,
            "recommended_tables": table_recommendations,
            "total_count": len(table_recommendations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_recommendation_reason(score: float) -> str:
    """점수 기반 추천 이유 생성"""
    if score >= 2.0:
        return "매우 관련성 높음 - 핵심 테이블"
    elif score >= 1.5:
        return "관련성 높음 - 주요 테이블"
    elif score >= 1.0:
        return "관련성 보통 - 참고 테이블"
    else:
        return "관련성 낮음 - 선택적 테이블"
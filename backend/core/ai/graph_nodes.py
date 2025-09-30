"""
LangGraph 노드 정의
"""
from typing import Dict, Any
from decimal import Decimal
import sys
import logging
from pathlib import Path
from openai import OpenAIError, APIError, APITimeoutError, RateLimitError

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from .graph_state import AgentState
    from .schema_retriever import SchemaRetriever, TableInfo
    from .sql_generator import SQLGenerator
    from .sql_executor import SQLExecutor
    from .prompt_builder import SQLPromptBuilder
except ImportError:
    from graph_state import AgentState
    from schema_retriever import SchemaRetriever, TableInfo
    from sql_generator import SQLGenerator
    from sql_executor import SQLExecutor
    from prompt_builder import SQLPromptBuilder

from backend.repositories.monitoring_repository import get_repository
from backend.models.monitoring import (
    QueryHistory,
    QueryStatus,
    Anomaly,
    AnomalyType,
    QueryResultType
)


class GraphNodes:
    """LangGraph 노드 모음"""
    
    def __init__(self):
        self.retriever = SchemaRetriever()
        self.generator = SQLGenerator()
        self.executor = SQLExecutor()
        self.repository = get_repository()
        self.logger = logging.getLogger(__name__)
    
    # ===== 기존 노드들 (동일) =====
    
    def search_tables_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 1: 관련 테이블 검색"""
        print(f"\n[노드 1] 테이블 검색 중: {state['user_query']}")
        
        tables = self.retriever.search_relevant_tables(
            state['user_query'],
            top_k=3
        )
        
        if not tables:
            return {
                "error": "관련 테이블을 찾을 수 없습니다",
                "relevant_tables": []
            }
        
        tables_dict = [
            {
                "name": t.name,
                "description": t.description,
                "columns_text": t.columns_text,
                "common_queries": t.common_queries,
                "score": t.score,
                "business_tags": t.business_tags,
                "relations_text": t.relations_text,
                "sample_queries_text": t.sample_queries_text
            }
            for t in tables
        ]
        
        # 검색 결과 상세 출력
        print(f"  ✓ 검색된 테이블 ({len(tables_dict)}개):")
        for i, table in enumerate(tables_dict, 1):
            print(f"    {i}. {table['name']} (점수: {table['score']:.2f})")
            if table['description']:
                print(f"       설명: {table['description'][:60]}...")
            if table['business_tags']:
                print(f"       태그: {', '.join(table['business_tags'])}")
        
        return {"relevant_tables": tables_dict}
    

    def generate_sql_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 2: SQL 생성"""
        print(f"\n[노드 2] SQL 생성 중...")
        
        if not state.get('relevant_tables'):
            return {"error": "테이블 정보가 없습니다"}
        
        # 이미 상단에서 임포트했으므로 중복 임포트 제거
        tables = [
            TableInfo(
                name=t['name'],
                description=t['description'],
                columns_text=t['columns_text'],
                common_queries=t['common_queries'],
                score=t['score'],
                business_tags=t.get('business_tags', []),
                relations_text=t.get('relations_text', ''),
                sample_queries_text=t.get('sample_queries_text', '')
            )
            for t in state['relevant_tables']
        ]
        
        # 이미 상단에서 임포트했으므로 중복 임포트 제거
        messages = SQLPromptBuilder.build_messages(state['user_query'], tables)
        
        try:
            response = self.generator.openai_client.chat.completions.create(
                model=self.generator.chat_deployment,
                messages=messages,
                temperature=0.0,
                max_tokens=500,
                timeout=30.0  # 30초 타임아웃
            )
            
            sql = response.choices[0].message.content.strip()
            
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            elif sql.startswith("```"):
                sql = sql.replace("```", "").strip()
            
            if not sql.endswith(";"):
                sql += ";"
            
            print(f"  ✓ SQL 생성 완료")
            print(f"  {sql}")
            
            return {"generated_sql": sql}
            
        except APITimeoutError as e:
            error_msg = f"SQL 생성 타임아웃 (30초 초과): {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        except RateLimitError as e:
            error_msg = f"API 호출 한도 초과: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        except APIError as e:
            error_msg = f"OpenAI API 오류: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        except OpenAIError as e:
            error_msg = f"OpenAI 클라이언트 오류: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        except Exception as e:
            # 예상하지 못한 예외는 로깅 후 재발생
            error_msg = f"예상치 못한 SQL 생성 오류: {str(e)}"
            self.logger.exception(error_msg)  # 스택 트레이스 포함
            raise  # 예상치 못한 예외는 상위로 전파
    
    
    def validate_sql_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 3: SQL 검증"""
        print(f"\n[노드 3] SQL 검증 중...")
        
        if not state.get('generated_sql'):
            return {"error": "생성된 SQL이 없습니다", "sql_valid": False}
        
        validation = self.executor.validate_query(state['generated_sql'])
        
        if validation['valid']:
            print(f"  ✓ SQL 검증 통과")
            return {"sql_valid": True}
        else:
            print(f"  ✗ SQL 검증 실패: {validation['error']}")
            return {
                "sql_valid": False,
                "error": f"SQL 검증 실패: {validation['error']}"
            }
    
    def execute_sql_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 4: SQL 실행"""
        print(f"\n[노드 4] SQL 실행 중...")
        
        if not state.get('generated_sql'):
            return {"error": "실행할 SQL이 없습니다"}
        
        result = self.executor.execute_query(state['generated_sql'])
        
        if result['success']:
            print(f"  ✓ 실행 성공: {result.get('row_count', 0)}개 행 반환")
            return {"query_result": result}
        else:
            print(f"  ✗ 실행 실패: {result['error']}")
            return {
                "error": f"SQL 실행 실패: {result['error']}",
                "query_result": result
            }
    
    # ===== 새로운 노드들 =====
    
    def save_history_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 5: 쿼리 실행 히스토리 저장 (카테고리형 지원)"""
        print(f"\n[노드 5] 히스토리 저장 중...")
        
        result = state.get('query_result')
        if not result:
            print(f"  ✗ 저장할 결과 없음")
            return {}
        
        metric_id = state.get('metric_id')
        if not metric_id:
            print(f"  ⚠ metric_id 없음, 히스토리 저장 스킵")
            return {}
        
        data = result.get('data', [])
        
        # 결과 유형 판별
        if not data:
            # 데이터 없음
            result_type = QueryResultType.NO_DATA
            result_value = None
            result_data = None
            print(f"  → 유형: 데이터 없음")
            
        elif len(data) == 1 and len(data[0]) == 1:
            # 단일 값 (COUNT, SUM, AVG 등)
            result_type = QueryResultType.SINGLE_VALUE
            result_value = list(data[0].values())[0]
            result_data = None
            
            # Decimal → float 변환
            if isinstance(result_value, Decimal):
                result_value = float(result_value)
            
            print(f"  → 유형: 단일 값 ({result_value})")
            
        else:
            # 다중 행 (GROUP BY, 상태별 분포 등)
            result_type = QueryResultType.MULTIPLE_ROWS
            result_value = None  # 단일 값 없음
            result_data = []
            
            # Decimal 변환 및 저장
            for row in data:
                converted_row = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        converted_row[key] = float(value)
                    else:
                        converted_row[key] = value
                result_data.append(converted_row)
            
            print(f"  → 유형: 다중 행 ({len(result_data)}개)")
        
        # 히스토리 생성
        history = QueryHistory(
            metric_id=metric_id,
            status=QueryStatus.SUCCESS if result['success'] else QueryStatus.FAILED,
            result_type=result_type,
            result_value=result_value,
            result_data=result_data,
            row_count=result.get('row_count'),
            error_message=result.get('error'),
            execution_time_ms=None
        )
        
        saved = self.repository.create_history(history)
        print(f"  ✓ 히스토리 저장 완료: {saved.id}")
        
        return {"history_id": saved.id}
    
    def detect_anomaly_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 6: 고도화된 이상 감지 (단일값 + 카테고리형 지원)"""
        print(f"\n[노드 6] 고도화된 이상 감지 중...")
        
        metric_id = state.get('metric_id')
        history_id = state.get('history_id')
        threshold_config = state.get('threshold_config')
        
        if not all([metric_id, history_id]):
            print(f"  ⚠ 이상 감지 스킵 (필수 정보 없음)")
            return {"anomaly_detected": False}
        
        # 임계값 설정이 없어도 카테고리형 이상치 감지 가능
        if not threshold_config or not threshold_config.get('enabled'):
            print(f"  ℹ 임계값 검사 비활성화 - 카테고리형 이상치만 검사")
            return self._detect_categorical_anomalies(state)
        
        # 최신 히스토리 가져오기
        history = self.repository.get_history(history_id)
        if not history:
            print(f"  ⚠ 히스토리 없음")
            return {"anomaly_detected": False}
        
        # 다중 행 결과는 임계값 비교 불가
        if history.result_type == QueryResultType.MULTIPLE_ROWS:
            print(f"  ⚠ 다중 행 결과는 임계값 검사 미지원")
            return {"anomaly_detected": False}
        
        # 단일 값이 없으면 스킵
        if history.result_value is None:
            print(f"  ⚠ 결과 값 없음")
            return {"anomaly_detected": False}
        
        # 임계값 설정 검증
        operator = threshold_config.get('operator')
        threshold_value = threshold_config.get('value')
        
        if operator is None or threshold_value is None:
            print("  ⚠ 임계값 설정 불완전(operator/value 누락)")
            return {"anomaly_detected": False}
        
        # operator 유효성 검증
        valid_operators = ['>', '>=', '<', '<=', '==', '!=']
        if operator not in valid_operators:
            print(f"  ⚠ 유효하지 않은 연산자: {operator}")
            return {"anomaly_detected": False}
        
        # threshold 값을 float로 안전하게 변환
        try:
            threshold = float(threshold_value)
        except (ValueError, TypeError) as e:
            print(f"  ⚠ 임계값을 숫자로 변환 실패: {threshold_value} ({e})")
            return {"anomaly_detected": False}
        
        # 실제 값도 float로 안전하게 변환
        try:
            actual = float(history.result_value)
        except (ValueError, TypeError) as e:
            print(f"  ⚠ 결과값을 숫자로 변환 실패: {history.result_value} ({e})")
            return {"anomaly_detected": False}
        
        is_anomaly = self._check_threshold(actual, operator, threshold)
        
        if is_anomaly:
            print(f"  🚨 이상 감지! {actual} {operator} {threshold}")
            if operator in ('>', '>='):
                anomaly_type = AnomalyType.THRESHOLD_EXCEEDED
            elif operator in ('<', '<='):
                anomaly_type = AnomalyType.THRESHOLD_BELOW
            elif operator in ('==', '!='):
                # 동등/비동등 조건 충족도 '임계 초과' 계열로 분류(대안: 전용 타입 도입)
                anomaly_type = AnomalyType.THRESHOLD_EXCEEDED
            else:
                anomaly_type = AnomalyType.QUERY_ERROR
            
            anomaly = Anomaly(
                metric_id=metric_id,
                history_id=history_id,
                anomaly_type=anomaly_type,
                threshold_value=threshold,
                actual_value=actual
            )
            saved = self.repository.create_anomaly(anomaly)
            
            return {
                "anomaly_detected": True,
                "anomaly_id": saved.id
            }
        else:
            print(f"  ✓ 정상 범위: {actual} {operator} {threshold}")
            return {"anomaly_detected": False}
    
    def _detect_categorical_anomalies(self, state: AgentState) -> Dict[str, Any]:
        """카테고리형 데이터 이상치 감지 (20개 중 1개도 감지)"""
        print(f"  🔍 카테고리형 이상치 감지 중...")
        
        history_id = state.get('history_id')
        history = self.repository.get_history(history_id)
        
        if not history or history.result_type != QueryResultType.MULTIPLE_ROWS:
            print(f"  ⚠ 카테고리형 데이터 없음")
            return {"anomaly_detected": False}
        
        result_data = history.result_data
        if not result_data or len(result_data) == 0:
            print(f"  ⚠ 결과 데이터 없음")
            return {"anomaly_detected": False}
        
        # 분포 분석
        total_records = sum(row.get('count', 0) for row in result_data)
        anomalies = []
        
        for row in result_data:
            count = row.get('count', 0)
            if count == 0:
                continue
                
            percentage = (count / total_records) * 100
            
            # 극소 카테고리 (1% 미만) - 100개 중 1개
            if percentage < 1.0 and count >= 1:
                anomalies.append({
                    "type": "rare_category",
                    "value": row,
                    "count": count,
                    "percentage": percentage,
                    "severity": "high"
                })
                print(f"  🚨 극소 카테고리: {row} ({count}개, {percentage:.2f}%)")
            
            # 소수 카테고리 (5% 미만) - 20개 중 1개
            elif percentage < 5.0 and count >= 1:
                anomalies.append({
                    "type": "minority_category", 
                    "value": row,
                    "count": count,
                    "percentage": percentage,
                    "severity": "medium"
                })
                print(f"  ⚠ 소수 카테고리: {row} ({count}개, {percentage:.2f}%)")
        
        if anomalies:
            # 이상치 저장
            anomaly = Anomaly(
                metric_id=state.get('metric_id'),
                history_id=history_id,
                anomaly_type=AnomalyType.THRESHOLD_EXCEEDED,  # 임시로 사용
                threshold_value=5.0,  # 5% 기준
                actual_value=len(anomalies)
            )
            saved = self.repository.create_anomaly(anomaly)
            
            return {
                "anomaly_detected": True,
                "anomaly_id": saved.id,
                "anomaly_count": len(anomalies),
                "anomaly_details": anomalies
            }
        else:
            print(f"  ✓ 카테고리 분포 정상")
            return {"anomaly_detected": False}
    
    def send_notification_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 7: 알림 발송 (MVP: 콘솔 출력만)"""
        print(f"\n[노드 7] 알림 발송 중...")
        
        if not state.get('anomaly_detected'):
            print(f"  ⚠ 이상 없음, 알림 스킵")
            return {}
        
        anomaly_id = state.get('anomaly_id')
        if not anomaly_id:
            return {}
        
        anomaly = self.repository.anomalies_container.read_item(
            item=anomaly_id,
            partition_key=state['metric_id']
        )
        
        # MVP: 콘솔 출력
        print(f"\n" + "="*60)
        print(f"🚨 이상 알림")
        print(f"="*60)
        print(f"지표 ID: {anomaly['metric_id']}")
        print(f"이상 유형: {anomaly['anomaly_type']}")
        print(f"임계값: {anomaly['threshold_value']}")
        print(f"실제값: {anomaly['actual_value']}")
        print(f"="*60)
        
        # TODO: Slack/이메일 발송 로직 추가
        
        return {"notification_sent": True}
    
    def format_result_node(self, state: AgentState) -> Dict[str, Any]:
        """노드 8: 결과 포맷팅"""
        print(f"\n[노드 8] 결과 포맷팅 중...")
        
        if state.get('error'):
            return {"final_answer": f"❌ 오류: {state['error']}"}
        
        result = state.get('query_result')
        if not result or not result.get('success'):
            return {"final_answer": "❌ 쿼리 실행 실패"}
        
        data = result.get('data', [])
        if not data:
            answer = "✅ 쿼리 실행 성공, 결과 없음"
        elif len(data) == 1 and len(data[0]) == 1:
            value = list(data[0].values())[0]
            answer = f"✅ 결과: {value}"
        else:
            answer = f"✅ {len(data)}개 행 반환:\n"
            for i, row in enumerate(data[:5], 1):
                answer += f"{i}. {row}\n"
            if len(data) > 5:
                answer += f"... (총 {len(data)}개)"
        
        print(f"  ✓ 포맷팅 완료")
        
        return {"final_answer": answer}
    
    # ===== 헬퍼 메서드 =====
    
    def _check_threshold(self, actual: float, operator: str, threshold: float) -> bool:
        """임계값 비교"""
        if operator == '>':
            return actual > threshold
        elif operator == '>=':
            return actual >= threshold
        elif operator == '<':
            return actual < threshold
        elif operator == '<=':
            return actual <= threshold
        elif operator == '==':
            return actual == threshold
        elif operator == '!=':
            return actual != threshold
        return False
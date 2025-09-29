"""
SQL 실행기 - 생성된 SQL을 DB에서 실행
"""
import os
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


class SQLExecutor:
    """PostgreSQL 쿼리 실행기"""
    
    def __init__(self):
        load_dotenv()
        self.connection_params = {
            "host": os.getenv("TEST_CLIENT_DB_HOST"),
            "port": int(os.getenv("TEST_CLIENT_DB_PORT", 5432)),
            "database": os.getenv("TEST_CLIENT_DB_NAME"),
            "user": os.getenv("TEST_CLIENT_DB_USER"),
            "password": os.getenv("TEST_CLIENT_DB_PASSWORD")
        }
    
    def _has_disallowed_semicolon(self, sql: str) -> bool:
        """멀티 스테이트먼트 방지를 위한 세미콜론 검사.
        허용: 문장 끝의 단 하나의 세미콜론
        차단: 그 외 모든 세미콜론 존재
        """
        if sql is None:
            return False
        stripped = sql.strip()
        semicolons = [i for i, ch in enumerate(stripped) if ch == ';']
        if not semicolons:
            return False
        # 오직 마지막 문자 하나만 세미콜론이면 허용
        return not (len(semicolons) == 1 and semicolons[0] == len(stripped) - 1)
    
    def execute_query(
        self,
        sql: str,
        fetch_limit: int = 100,
        allow_writes: bool = False,
        statement_timeout_ms: int = 10000,
        search_path: Optional[str] = None,
        allow_multi_statements: bool = False,
    ) -> dict:
        """
        SQL 쿼리 실행
        
        Args:
            sql: 실행할 SQL 쿼리
            fetch_limit: 최대 반환 row 수
            
        Returns:
            {
                "success": True,
                "data": [...],
                "row_count": 10,
                "columns": ["col1", "col2"]
            }
        """
        conn = None
        cursor = None
        
        try:
            # 멀티 스테이트먼트 차단
            if not allow_multi_statements and self._has_disallowed_semicolon(sql):
                return {
                    "success": False,
                    "error": "멀티 스테이트먼트는 허용되지 않습니다. 쿼리를 단일 문장으로 제공하세요.",
                    "sql": sql
                }
            sanitized_sql = sql.strip()
            if sanitized_sql.endswith(';'):
                sanitized_sql = sanitized_sql[:-1]

            # 1. DB 연결
            params = dict(self.connection_params)
            params.setdefault("connect_timeout", 10)
            conn = psycopg2.connect(**params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 세션 안전장치
            if not allow_writes:
                cursor.execute("SET LOCAL default_transaction_read_only = on")
            cursor.execute(f"SET LOCAL statement_timeout = {int(statement_timeout_ms)}")
            if search_path:
                cursor.execute("SET LOCAL search_path = %s", (search_path,))

            # 2. 쿼리 실행
            cursor.execute(sanitized_sql)
            
            # 3. SELECT 쿼리인 경우 결과 가져오기
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(fetch_limit)
                data = [dict(row) for row in rows]
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": columns,
                    "sql": sanitized_sql
                }
            else:
                # INSERT/UPDATE/DELETE 등
                conn.commit()
                return {
                    "success": True,
                    "message": f"{cursor.rowcount} rows affected",
                    "sql": sanitized_sql
                }
                
        except psycopg2.Error as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.pgcode,
                "sql": sql
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def validate_query(self, sql: str) -> dict:
        """
        쿼리 유효성 검사 (EXPLAIN으로 확인)
        
        Returns:
            {"valid": True/False, "error": "..."}
        """
        try:
            # 멀티 스테이트먼트 차단
            if self._has_disallowed_semicolon(sql):
                return {"valid": False, "error": "멀티 스테이트먼트는 허용되지 않습니다."}

            sanitized_sql = sql.strip()
            if sanitized_sql.endswith(';'):
                sanitized_sql = sanitized_sql[:-1]

            params = dict(self.connection_params)
            params.setdefault("connect_timeout", 10)
            with psycopg2.connect(**params) as conn:
                with conn.cursor() as cursor:
                    # EXPLAIN으로 쿼리 검증 (실행은 안 함)
                    cursor.execute(f"EXPLAIN {sanitized_sql}")
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}


# 통합 테스트
if __name__ == "__main__":
    from sql_generator import SQLGenerator
    
    generator = SQLGenerator()
    executor = SQLExecutor()
    
    test_queries = [
        "오늘 주문 건수",
        "이번 달 총 매출액"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"질문: {query}")
        print(f"{'='*80}")
        
        # 1. SQL 생성
        result = generator.generate_sql(query)
        
        if result.get("error"):
            print(f"❌ SQL 생성 실패: {result['error']}")
            continue
        
        sql = result["sql"]
        print(f"\n생성된 SQL:\n{sql}")
        
        # 2. 쿼리 검증
        validation = executor.validate_query(sql)
        if not validation["valid"]:
            print(f"\n⚠️ 쿼리 검증 실패: {validation['error']}")
            continue
        
        # 3. 쿼리 실행
        exec_result = executor.execute_query(sql)
        
        if exec_result["success"]:
            print(f"\n✅ 실행 성공!")
            print(f"결과: {exec_result.get('data', exec_result.get('message'))}")
        else:
            print(f"\n❌ 실행 실패: {exec_result['error']}")
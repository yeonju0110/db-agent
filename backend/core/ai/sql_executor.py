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
    
    def execute_query(
        self,
        sql: str,
        fetch_limit: int = 100
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
            # 1. DB 연결
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 2. 쿼리 실행
            cursor.execute(sql)
            
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
                    "sql": sql
                }
            else:
                # INSERT/UPDATE/DELETE 등
                conn.commit()
                return {
                    "success": True,
                    "message": f"{cursor.rowcount} rows affected",
                    "sql": sql
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
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            # EXPLAIN으로 쿼리 검증 (실행은 안 함)
            cursor.execute(f"EXPLAIN {sql}")
            cursor.close()
            conn.close()
            
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
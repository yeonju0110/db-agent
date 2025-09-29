"""
SQL 실행기 - 생성된 SQL을 DB에서 실행
"""
import os
import re
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


class SQLExecutor:
    """PostgreSQL 쿼리 실행기"""
    
    def __init__(self):
        load_dotenv()
        host = os.getenv("TEST_CLIENT_DB_HOST")
        db = os.getenv("TEST_CLIENT_DB_NAME")
        user = os.getenv("TEST_CLIENT_DB_USER")
        pwd = os.getenv("TEST_CLIENT_DB_PASSWORD")
        port_env = os.getenv("TEST_CLIENT_DB_PORT")

        # 필수 환경변수 누락 체크
        missing = [k for k, v in {
            "TEST_CLIENT_DB_HOST": host,
            "TEST_CLIENT_DB_NAME": db,
            "TEST_CLIENT_DB_USER": user,
            "TEST_CLIENT_DB_PASSWORD": pwd,
        }.items() if not v]

        # 포트 유효성 검증 및 정규화 (기본값 5432)
        invalid = []
        port = 5432
        if port_env:
            try:
                port = int(str(port_env).strip())
                if port <= 0 or port > 65535:
                    invalid.append("TEST_CLIENT_DB_PORT")
                    port = 5432
            except (ValueError, TypeError):
                invalid.append("TEST_CLIENT_DB_PORT")
                port = 5432

        if missing or invalid:
            parts = []
            if missing:
                parts.append(f"누락: {', '.join(missing)}")
            if invalid:
                parts.append(f"유효하지 않음: {', '.join(invalid)}")
            raise ValueError(f"DB 접속 환경 변수 오류 - {'; '.join(parts)}")

        self.connection_params = {
            "host": host,
            "port": port,
            "database": db,
            "user": user,
            "password": pwd,
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
            # 입력 유효성 검증: None/빈 문자열 방지
            if not isinstance(sql, str) or not sql.strip():
                return {
                    "success": False,
                    "error": "빈 SQL 입니다.",
                    "sql": sql,
                }

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

            # 2. 구문 화이트리스트/블랙리스트 검사
            normalized = sanitized_sql.lstrip()
            # 선행 괄호 제거 (서브쿼리로 감싼 형태 방지)
            while normalized.startswith('('):
                normalized = normalized[1:].lstrip()
            # 선행 주석 제거 (--, /* */)
            while normalized.startswith('--') or normalized.startswith('/*'):
                if normalized.startswith('--'):
                    nl = normalized.find('\n')
                    normalized = '' if nl == -1 else normalized[nl + 1:]
                else:
                    end = normalized.find('*/')
                    normalized = '' if end == -1 else normalized[end + 2:]
                normalized = normalized.lstrip()
            # 공백 축약
            normalized = ' '.join(normalized.split())
            first_kw = (normalized.split(None, 1)[0] if normalized else '').upper()

            # 즉시 차단: 위험/세션 영향/메타 명령
            disallowed_any = {
                'COPY', 'DO', 'CALL', 'LISTEN', 'NOTIFY', 'EXECUTE',
                'PG_SLEEP', 'PG_TERMINATE_BACKEND',
            }
            if first_kw.startswith('\\') or first_kw in disallowed_any:
                return {
                    "success": False,
                    "error": f"허용되지 않는 구문입니다: {first_kw or '(empty)'}",
                    "sql": sql,
                }

            allowed_ro = {"SELECT", "WITH", "VALUES", "TABLE", "EXPLAIN"}
            allowed_rw = allowed_ro | {"INSERT", "UPDATE", "DELETE"}
            allowed = allowed_rw if allow_writes else allowed_ro
            if first_kw and first_kw not in allowed:
                return {
                    "success": False,
                    "error": (
                        f"허용되지 않는 첫 구문입니다({first_kw}). "
                        f"읽기 전용: {', '.join(sorted(allowed_ro))}"
                        + (", 쓰기 허용 시: " + ", ".join(sorted(allowed_rw - allowed_ro)) if allow_writes else "")
                    ),
                    "sql": sql,
                }

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
            
            # 3. SELECT/RETURNING 결과 처리
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(fetch_limit)
                data = [dict(row) for row in rows]
                if allow_writes:
                    conn.commit()
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": columns,
                    "sql": sanitized_sql
                }
            else:
                # INSERT/UPDATE/DELETE 등
                if allow_writes:
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
        쿼리 유효성 검사 (정적 검증 전용)
        
        Returns:
            {"valid": True/False, "error": "..."}
        """
        try:
            # 입력 유효성 검증: None/빈 문자열 방지
            if not isinstance(sql, str) or not sql.strip():
                return {"valid": False, "error": "빈 SQL 입니다."}

            # 멀티 스테이트먼트 차단
            if self._has_disallowed_semicolon(sql):
                return {"valid": False, "error": "멀티 스테이트먼트는 허용되지 않습니다."}

            sanitized_sql = sql.strip()
            if sanitized_sql.endswith(';'):
                sanitized_sql = sanitized_sql[:-1]

            # 2. 구문 화이트리스트/블랙리스트 검사 (검증 단계는 읽기 전용 허용 집합만 허용)
            normalized = sanitized_sql.lstrip()
            while normalized.startswith('('):
                normalized = normalized[1:].lstrip()
            while normalized.startswith('--') or normalized.startswith('/*'):
                if normalized.startswith('--'):
                    nl = normalized.find('\n')
                    normalized = '' if nl == -1 else normalized[nl + 1:]
                else:
                    end = normalized.find('*/')
                    normalized = '' if end == -1 else normalized[end + 2:]
                normalized = normalized.lstrip()
            normalized = ' '.join(normalized.split())
            first_kw = (normalized.split(None, 1)[0] if normalized else '').upper()
            disallowed_any = {
                'COPY', 'DO', 'CALL', 'LISTEN', 'NOTIFY', 'EXECUTE',
                'PG_SLEEP', 'PG_TERMINATE_BACKEND',
            }
            if first_kw.startswith('\\') or first_kw in disallowed_any:
                return {"valid": False, "error": f"허용되지 않는 구문입니다: {first_kw or '(empty)'}"}
            # EXPLAIN/ANALYZE 안전 검사
            tokens_upper = re.findall(r"[A-Z_]+", normalized.upper()) if normalized else []
            if first_kw == 'EXPLAIN':
                second_kw = tokens_upper[1] if len(tokens_upper) > 1 else ''
                if second_kw == 'EXPLAIN':
                    return {"valid": False, "error": "중복 EXPLAIN은 허용되지 않습니다."}
                if 'ANALYZE' in tokens_upper:
                    return {"valid": False, "error": "EXPLAIN ANALYZE는 허용되지 않습니다."}
            else:
                if 'ANALYZE' in tokens_upper:
                    return {"valid": False, "error": "ANALYZE 사용은 검증 단계에서 허용되지 않습니다."}

            allowed_ro = {"SELECT", "WITH", "VALUES", "TABLE", "EXPLAIN"}
            if first_kw and first_kw not in allowed_ro:
                return {"valid": False, "error": f"허용되지 않는 첫 구문입니다({first_kw}). 읽기 전용: {', '.join(sorted(allowed_ro))}"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def run_explain(
        self,
        sql: str,
        analyze: bool = False,
        verbose: bool = False,
        buffers: bool = False,
        timing: bool = False,
        statement_timeout_ms: int = 10000,
        search_path: Optional[str] = None,
    ) -> dict:
        """
        EXPLAIN 실행 (옵션 포함). 실제 실행 경로에서만 호출하세요.
        기본값은 EXPLAIN (ANALYZE 없음)으로 실제 실행 없이 플랜만 확인합니다.
        """
        conn = None
        cursor = None
        try:
            if not isinstance(sql, str) or not sql.strip():
                return {"success": False, "error": "빈 SQL 입니다.", "sql": sql}

            if self._has_disallowed_semicolon(sql):
                return {"success": False, "error": "멀티 스테이트먼트는 허용되지 않습니다.", "sql": sql}

            sanitized_sql = sql.strip()
            if sanitized_sql.endswith(';'):
                sanitized_sql = sanitized_sql[:-1]

            # 안전 옵션 구성 및 중복/분기 방지
            upper_norm = ' '.join(sql.strip().split()).upper()
            if upper_norm.startswith('EXPLAIN'):
                # 사용자가 이미 EXPLAIN을 붙인 경우: ANALYZE 포함 여부 차단
                if ' ANALYZE' in upper_norm.split():
                    return {"success": False, "error": "EXPLAIN ANALYZE는 허용되지 않습니다."}
            options = []
            if analyze:
                options.append("ANALYZE")
            if verbose:
                options.append("VERBOSE")
            if buffers:
                options.append("BUFFERS")
            if timing:
                options.append("TIMING")
            opt_clause = (" " + " ".join(options)) if options else ""
            if upper_norm.startswith('EXPLAIN'):
                # 중복 EXPLAIN 방지: 사용자가 준 EXPLAIN을 그대로 사용 (옵션 병합은 하지 않음)
                if options:
                    return {"success": False, "error": "이미 EXPLAIN이 포함된 쿼리에 옵션을 추가할 수 없습니다."}
                explain_sql = sanitized_sql
            else:
                explain_sql = f"EXPLAIN{opt_clause} {sanitized_sql}"

            params = dict(self.connection_params)
            params.setdefault("connect_timeout", 10)
            conn = psycopg2.connect(**params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 안전장치: ANALYZE가 꺼져 있으면 읽기 전용 세션으로 강제
            if not analyze:
                cursor.execute("SET LOCAL default_transaction_read_only = on")
            cursor.execute(f"SET LOCAL statement_timeout = {int(statement_timeout_ms)}")
            if search_path:
                cursor.execute("SET LOCAL search_path = %s", (search_path,))

            cursor.execute(explain_sql)
            rows = cursor.fetchall()
            plan_lines = [row.get('QUERY PLAN') for row in rows] if rows else []
            return {
                "success": True,
                "plan": plan_lines,
                "explain_sql": explain_sql,
                "sql": sanitized_sql,
            }
        except psycopg2.Error as e:
            return {"success": False, "error": str(e), "error_code": e.pgcode}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


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
        
        # 3. (선택) 실행 전 플랜 확인
        explain = executor.run_explain(sql)
        if explain.get("success"):
            print("\n실행 계획 (요약):")
            for line in (explain.get("plan") or [])[:10]:
                print("  ", line)
        else:
            print(f"\n(EXPLAIN 실패: {explain.get('error')})")

        # 4. 쿼리 실행
        exec_result = executor.execute_query(sql)
        
        if exec_result["success"]:
            print("\n✅ 실행 성공!")
            print(f"결과: {exec_result.get('data', exec_result.get('message'))}")
        else:
            print(f"\n❌ 실행 실패: {exec_result['error']}")
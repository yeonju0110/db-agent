import os
import sys
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from dotenv import load_dotenv


@dataclass
class DbConfig:
    """데이터베이스 연결 설정 정보 (PostgreSQL 전용)"""
    host: str
    port: int
    name: str
    user: str
    password: str


def load_config_from_env() -> DbConfig:
    """환경변수에서 PostgreSQL 설정을 로드"""
    load_dotenv()

    host = os.getenv("TEST_CLIENT_DB_HOST", "127.0.0.1")
    port_str = os.getenv("TEST_CLIENT_DB_PORT", "5432")
    name = os.getenv("TEST_CLIENT_DB_NAME", "ecommerce_db")
    user = os.getenv("TEST_CLIENT_DB_USER", "monitoring_user")
    password = os.getenv("TEST_CLIENT_DB_PASSWORD", "")

    try:
        port = int(port_str)
    except ValueError:
        raise ValueError(f"Invalid port: {port_str}")

    return DbConfig(
        host=host,
        port=port,
        name=name,
        user=user,
        password=password,
    )


def connect_postgres(cfg: DbConfig):
    """PostgreSQL 데이터베이스에 연결"""
    import psycopg2

    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        dbname=cfg.name,
        connect_timeout=5,
    )


def try_connect(cfg: DbConfig):
    """PostgreSQL 연결"""
    return connect_postgres(cfg)


def run_basic_queries(conn) -> Tuple[bool, Optional[str]]:
    """기본적인 쿼리를 실행하여 연결 상태 확인"""
    try:
        # 연결 테스트 쿼리
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            _ = cur.fetchone()

        # 테이블 목록 조회 테스트
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') LIMIT 5")
            _ = cur.fetchall()
        return True, None
    except Exception as e:  # noqa: BLE001 - surface errors for diagnostics
        return False, str(e)


def main() -> int:
    """메인 실행 함수 - 데이터베이스 연결 테스트"""
    cfg = load_config_from_env()
    print(f"[INFO] postgres 연결 시도 중: {cfg.user}@{cfg.host}:{cfg.port}/{cfg.name}")
    start = time.time()
    try:
        conn = try_connect(cfg)
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 연결 실패: {e}")
        return 2

    elapsed = (time.time() - start) * 1000
    print(f"[OK] {elapsed:.0f} ms 만에 연결 성공")

    ok, err = run_basic_queries(conn)
    if not ok:
        print(f"[ERROR] 기본 쿼리 실행 실패: {err}")
        return 3

    # 최소 권한 점검: 읽기 권한으로 가능한지 간단 확인
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT CURRENT_USER")
            who = cur.fetchone()
        print(f"[OK] 현재 사용자: {who}")
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] 현재 사용자 확인 불가: {e}")

    # 연결 종료
    try:
        conn.close()
    except Exception:
        pass

    print("[SUCCESS] 연결 및 기본 쿼리 검증 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


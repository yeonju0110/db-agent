"""
DB 스키마 수집/정규화/문서화 스크립트

기능
- PostgreSQL 전용 (INFORMATION_SCHEMA/pg_catalog 기반)
- 테이블/컬럼/PK/FK/인덱스 수집 및 정규화
- 간단한 샘플 쿼리 생성
- 산출물: 테이블 카드 Markdown(.md) + JSON(.json)

환경변수 (test_db_connection.py와 동일 키 사용)
- TEST_CLIENT_DB_TYPE: postgres
- TEST_CLIENT_DB_HOST
- TEST_CLIENT_DB_PORT
- TEST_CLIENT_DB_NAME
- TEST_CLIENT_DB_USER
- TEST_CLIENT_DB_PASSWORD

사용 예시
  uv run python scripts/setup/export_schema.py --out-dir scripts/setup/outputs
"""

from __future__ import annotations

import argparse
import json
import os
import textwrap
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv


# ---------------------------
# 데이터 모델
# ---------------------------


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    default_value: Optional[str]
    extra: Optional[str]
    description: Optional[str]


@dataclass
class ForeignKeyInfo:
    column: str
    referenced_table: str
    referenced_column: str
    constraint_name: str


@dataclass
class IndexInfo:
    name: str
    columns: List[str]
    is_unique: bool


@dataclass
class TableCard:
    id: str
    object_type: str  # table
    name: str  # table name (optionally schema-qualified)
    table: str  # same as name
    schema: str
    description: Optional[str]
    columns: List[ColumnInfo]
    primary_key: List[str]
    foreign_keys: List[ForeignKeyInfo]
    indexes: List[IndexInfo]
    sample_queries: List[str]
    business_tags: List[str]
    embedding: Optional[List[float]]


# ---------------------------
# 설정 로딩
# ---------------------------


@dataclass
class DbConfig:
    db_type: str
    host: str
    port: int
    name: str
    user: str
    password: str


def load_config_from_env() -> DbConfig:
    load_dotenv()
    db_type = os.getenv("TEST_CLIENT_DB_TYPE", "postgres").lower()
    host = os.getenv("TEST_CLIENT_DB_HOST", "127.0.0.1")
    port = int(os.getenv("TEST_CLIENT_DB_PORT", "5432"))
    name = os.getenv("TEST_CLIENT_DB_NAME", "ecommerce_db")
    user = os.getenv("TEST_CLIENT_DB_USER", "monitoring_user")
    password = os.getenv("TEST_CLIENT_DB_PASSWORD", "")
    return DbConfig(db_type=db_type, host=host, port=port, name=name, user=user, password=password)


# ---------------------------
# DB 연결
# ---------------------------


def connect_postgres(cfg: DbConfig):
    import psycopg2

    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        dbname=cfg.name,
        connect_timeout=10,
    )


def connect_database(cfg: DbConfig):
    if cfg.db_type not in ("postgres", "postgresql"):
        raise ValueError("This exporter supports PostgreSQL only. Set TEST_CLIENT_DB_TYPE=postgres")
    return connect_postgres(cfg)


## MySQL 관련 로직 제거 (PostgreSQL only)


# ---------------------------
# 수집 쿼리 (PostgreSQL)
# ---------------------------


def fetch_pg_tables(conn) -> List[Tuple[str, str, str]]:
    # returns (schema, table, comment)
    sql = textwrap.dedent(r"""
        SELECT n.nspname AS table_schema,
               c.relname AS table_name,
               COALESCE(d.description, '') AS table_comment
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0
        WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY n.nspname, c.relname
        """
    )
    with conn.cursor() as cur:
        cur.execute(sql)
        return [(row[0], row[1], row[2]) for row in cur.fetchall()]


def fetch_pg_columns(conn) -> Dict[Tuple[str, str], List[ColumnInfo]]:
    sql = textwrap.dedent(r"""
        SELECT c.table_schema,
               c.table_name,
               c.column_name,
               c.udt_name,
               c.is_nullable,
               c.column_default,
               COALESCE(col_desc.description, '') AS column_comment
        FROM information_schema.columns c
        JOIN pg_class pc ON pc.relname = c.table_name
        JOIN pg_namespace pn ON pn.nspname = c.table_schema AND pn.oid = pc.relnamespace
        LEFT JOIN pg_attribute pattr ON pattr.attrelid = pc.oid AND pattr.attname = c.column_name
        LEFT JOIN pg_description col_desc ON col_desc.objoid = pc.oid AND col_desc.objsubid = pattr.attnum
        WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY c.table_schema, c.table_name, c.ordinal_position
        """
    )
    cols: Dict[Tuple[str, str], List[ColumnInfo]] = {}
    with conn.cursor() as cur:
        cur.execute(sql)
        for schema, table, col, udt, is_nullable, default_value, comment in cur.fetchall():
            cols.setdefault((schema, table), []).append(
                ColumnInfo(
                    name=col,
                    data_type=udt,
                    is_nullable=(str(is_nullable).upper() == "YES"),
                    is_primary_key=False,  # fill later
                    is_foreign_key=False,  # fill later
                    default_value=str(default_value) if default_value is not None else None,
                    extra=None,
                    description=comment if comment else None,
                )
            )
    return cols


def fetch_pg_primary_keys(conn) -> Dict[Tuple[str, str], List[str]]:
    sql = textwrap.dedent(r"""
        SELECT tc.table_schema, tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema AND tc.table_name = kcu.table_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY kcu.ordinal_position
        """
    )
    pks: Dict[Tuple[str, str], List[str]] = {}
    with conn.cursor() as cur:
        cur.execute(sql)
        for schema, table, col in cur.fetchall():
            pks.setdefault((schema, table), []).append(col)
    return pks


def fetch_pg_foreign_keys(conn) -> Dict[Tuple[str, str], List[ForeignKeyInfo]]:
    sql = textwrap.dedent(r"""
        SELECT kcu.table_schema,
               kcu.table_name,
               kcu.column_name,
               ccu.constraint_schema AS referenced_table_schema,
               ccu.table_name  AS referenced_table,
               ccu.column_name AS referenced_column,
               kcu.constraint_name
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.table_constraints tc
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = kcu.constraint_name AND ccu.constraint_schema = kcu.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND kcu.table_schema NOT IN ('pg_catalog', 'information_schema')
        """
    )
    fks: Dict[Tuple[str, str], List[ForeignKeyInfo]] = {}
    with conn.cursor() as cur:
        cur.execute(sql)
        for schema, table, col, ref_schema, ref_table, ref_col, cname in cur.fetchall():
            fk = ForeignKeyInfo(
                column=col,
                referenced_table=f"{ref_schema}.{ref_table}",
                referenced_column=ref_col,
                constraint_name=cname,
            )
            fks.setdefault((schema, table), []).append(fk)
    return fks


def fetch_pg_indexes(conn) -> Dict[Tuple[str, str], List[IndexInfo]]:
    # 카탈로그 기반: 인덱스 컬럼명을 정확히 추출 (표현식 인덱스는 제외)
    sql = textwrap.dedent(
        """
        WITH idx_cols AS (
          SELECT
            n.nspname AS schemaname,
            t.relname AS tablename,
            i.relname AS indexname,
            ix.indisunique AS is_unique,
            a.attname AS colname,
            x.ordinality AS ord
          FROM pg_index ix
          JOIN pg_class i ON i.oid = ix.indexrelid
          JOIN pg_class t ON t.oid = ix.indrelid
          JOIN pg_namespace n ON n.oid = t.relnamespace
          JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS x(attnum, ordinality) ON true
          JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = x.attnum
          WHERE n.nspname NOT IN ('pg_catalog','information_schema')
        )
        SELECT schemaname, tablename, indexname,
               array_agg(colname ORDER BY ord) AS cols,
               bool_or(is_unique) AS is_unique
        FROM idx_cols
        GROUP BY schemaname, tablename, indexname
        """
    )
    idx: Dict[Tuple[str, str], List[IndexInfo]] = {}
    with conn.cursor() as cur:
        cur.execute(sql)
        for schema, table, indexname, cols, is_unique in cur.fetchall():
            columns = [str(c) for c in (cols or [])]
            idx.setdefault((schema, table), []).append(
                IndexInfo(name=indexname, columns=columns, is_unique=bool(is_unique))
            )
    return idx


# ---------------------------
# 정규화 및 산출물
# ---------------------------


def build_sample_queries(schema: str, table: str, primary_key: List[str], foreign_keys: List[ForeignKeyInfo]) -> List[str]:
    qualified = f"{schema}.{table}" if schema else table
    samples: List[str] = []
    samples.append(f"SELECT * FROM {qualified} LIMIT 10;")
    if primary_key:
        pk_predicates = " AND ".join([f"{col} = :{col}" for col in primary_key])
        samples.append(f"SELECT * FROM {qualified} WHERE {pk_predicates};")
    for fk in foreign_keys[:2]:  # limit to 2 examples for brevity
        samples.append(
            f"SELECT t.* FROM {qualified} t JOIN {fk.referenced_table} r ON t.{fk.column} = r.{fk.referenced_column} LIMIT 10;"
        )
    return samples


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_table_outputs(base_dir: Path, card: TableCard) -> None:
    # 파일명은 안전한 basename으로 사용하되, JSON 내용의 name은 원본 유지
    basename = card.name.replace("/", "_").replace(" ", "_")
    # JSON
    json_path = base_dir / f"{basename}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "id": card.id,
                "object_type": card.object_type,
                "name": card.name,
                "table": card.table,
                "schema": card.schema,
                "description": card.description,
                "columns": [asdict(c) for c in card.columns],
                "primary_key": card.primary_key,
                "foreign_keys": [asdict(fk) for fk in card.foreign_keys],
                "indexes": [asdict(ix) for ix in card.indexes],
                "sample_queries": card.sample_queries,
                "business_tags": card.business_tags,
                "embedding": card.embedding,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Markdown
    md_path = base_dir / f"{basename}.md"
    lines: List[str] = []
    lines.append(f"# Table: {card.name}")
    if card.description:
        lines.append("")
        lines.append(card.description)
    lines.append("")
    lines.append("## Columns")
    lines.append("")
    lines.append("| Name | Type | Nullable | PK | FK | Default | Extra | Description |")
    lines.append("|---|---|:---:|:--:|:--:|---|---|---|")
    for col in card.columns:
        lines.append(
            f"| {col.name} | {col.data_type} | {'YES' if col.is_nullable else 'NO'} | "
            f"{'Y' if col.is_primary_key else ''} | {'Y' if col.is_foreign_key else ''} | "
            f"{col.default_value or ''} | {col.extra or ''} | {col.description or ''} |"
        )
    lines.append("")
    lines.append("## Primary Key")
    lines.append("")
    lines.append(", ".join(card.primary_key) if card.primary_key else "(none)")
    lines.append("")
    lines.append("## Foreign Keys")
    if card.foreign_keys:
        for fk in card.foreign_keys:
            lines.append(f"- {fk.constraint_name}: {fk.column} -> {fk.referenced_table}({fk.referenced_column})")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Indexes")
    if card.indexes:
        for ix in card.indexes:
            uniq = "UNIQUE" if ix.is_unique else "NON-UNIQUE"
            lines.append(f"- {ix.name} ({uniq}): {', '.join(ix.columns)}")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Sample Queries")
    lines.append("")
    for q in card.sample_queries:
        lines.append("```sql")
        lines.append(q)
        lines.append("```")
        lines.append("")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------
# 메인 로직
# ---------------------------


## MySQL 카드 빌더 제거


def build_cards_postgres(conn) -> List[TableCard]:
    tables = fetch_pg_tables(conn)
    columns_map = fetch_pg_columns(conn)
    pk_map = fetch_pg_primary_keys(conn)
    fk_map = fetch_pg_foreign_keys(conn)
    idx_map = fetch_pg_indexes(conn)

    cards: List[TableCard] = []
    for schema, table, comment in tables:
        cols = columns_map.get((schema, table), [])
        # PK 컬럼 순서 보존 + 멤버십 체크 성능을 위해 set 병행 사용
        pk_ordered = pk_map.get((schema, table), [])
        pk_cols_set = set(pk_ordered)
        fk_cols = {fk.column for fk in fk_map.get((schema, table), [])}
        for col in cols:
            # 멤버십 체크는 set으로, 순서는 리스트로 유지
            col.is_primary_key = col.name in pk_cols_set
            col.is_foreign_key = col.name in fk_cols

        fks = fk_map.get((schema, table), [])
        idxs = idx_map.get((schema, table), [])
        qualified = f"{schema}.{table}"
        samples = build_sample_queries(schema, table, pk_ordered, fks)
        card = TableCard(
            id=qualified,
            object_type="table",
            name=qualified,
            table=qualified,
            schema=schema,
            description=comment or None,
            columns=cols,
            # 다운스트림에서 PK 순서가 중요하므로 원본 순서를 그대로 사용
            primary_key=pk_ordered,
            foreign_keys=fks,
            indexes=idxs,
            sample_queries=samples,
            business_tags=[],
            embedding=None,
        )
        cards.append(card)
    return cards


def export_schema(out_dir: Path) -> Tuple[int, Path]:
    cfg = load_config_from_env()
    conn = connect_database(cfg)
    try:
        cards = build_cards_postgres(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # 출력 디렉토리 구성
    target_base = out_dir / "schema" / f"{cfg.db_type}_{cfg.name}"
    tables_dir = target_base / "tables"
    ensure_dir(tables_dir)

    for card in cards:
        # 파일명은 함수 내부에서 안전화 처리; 카드 객체의 원본 name은 유지
        write_table_outputs(tables_dir, card)

    # index.json (간단한 요약)
    index = [
        {
            "id": c.id,
            "name": c.name,
            "schema": c.schema,
            "table": c.table,
            "num_columns": len(c.columns),
        }
        for c in cards
    ]
    ensure_dir(target_base)
    with (target_base / "index.json").open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return len(cards), target_base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export DB schema as Markdown/JSON table cards")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("scripts/setup/outputs"),
        help="Base output directory",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count, base = export_schema(args["out_dir"] if isinstance(args, dict) else args.out_dir)
    print(f"[SUCCESS] Exported {count} table cards to {base}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())



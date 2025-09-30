"""
스키마 추출 서비스
기존 export_schema.py 로직을 서비스로 변환
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import psycopg2
from dataclasses import dataclass, asdict
from datetime import datetime

from backend.models.db_connection import DbConnection


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
    object_type: str
    name: str
    table: str
    schema: str
    description: Optional[str]
    columns: List[ColumnInfo]
    primary_key: List[str]
    foreign_keys: List[ForeignKeyInfo]
    indexes: List[IndexInfo]
    sample_queries: List[str]
    business_tags: List[str]
    embedding: Optional[List[float]]


class SchemaService:
    """스키마 추출 서비스"""
    
    def __init__(self):
        self.output_dir = Path("scripts/setup/outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.interval_minutes = 5  # 5분 간격으로 변경 (더 세밀한 모니터링)
    
    async def extract_schema(self, connection: DbConnection) -> Dict:
        """스키마 추출"""
        try:
            # DB 연결
            conn = psycopg2.connect(
                host=connection.host,
                port=connection.port,
                database=connection.database,
                user=connection.username,
                password=connection.password,
                connect_timeout=10
            )
            
            # 스키마 정보 수집
            tables = self._fetch_tables(conn)
            columns_map = self._fetch_columns(conn)
            pk_map = self._fetch_primary_keys(conn)
            fk_map = self._fetch_foreign_keys(conn)
            idx_map = self._fetch_indexes(conn)
            
            # 테이블 카드 생성
            cards = self._build_table_cards(tables, columns_map, pk_map, fk_map, idx_map)
            
            # 파일로 저장
            output_path = await self._save_schema_files(connection, cards)
            
            conn.close()
            
            return {
                "success": True,
                "message": f"{len(cards)}개 테이블 스키마 추출 완료",
                "output_path": str(output_path),
                "table_count": len(cards)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _fetch_tables(self, conn) -> List[Tuple[str, str, str]]:
        """테이블 목록 조회"""
        sql = """
        SELECT n.nspname AS table_schema,
               c.relname AS table_name,
               COALESCE(d.description, '') AS table_comment
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0
        WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY n.nspname, c.relname
        """
        with conn.cursor() as cur:
            cur.execute(sql)
            return [(row[0], row[1], row[2]) for row in cur.fetchall()]
    
    def _fetch_columns(self, conn) -> Dict[Tuple[str, str], List[ColumnInfo]]:
        """컬럼 정보 조회"""
        sql = """
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
        cols: Dict[Tuple[str, str], List[ColumnInfo]] = {}
        with conn.cursor() as cur:
            cur.execute(sql)
            for schema, table, col, udt, is_nullable, default_value, comment in cur.fetchall():
                cols.setdefault((schema, table), []).append(
                    ColumnInfo(
                        name=col,
                        data_type=udt,
                        is_nullable=(str(is_nullable).upper() == "YES"),
                        is_primary_key=False,  # 나중에 설정
                        is_foreign_key=False,  # 나중에 설정
                        default_value=str(default_value) if default_value is not None else None,
                        extra=None,
                        description=comment if comment else None,
                    )
                )
        return cols
    
    def _fetch_primary_keys(self, conn) -> Dict[Tuple[str, str], List[str]]:
        """기본키 조회"""
        sql = """
        SELECT tc.table_schema, tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema AND tc.table_name = kcu.table_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY kcu.ordinal_position
        """
        pks: Dict[Tuple[str, str], List[str]] = {}
        with conn.cursor() as cur:
            cur.execute(sql)
            for schema, table, col in cur.fetchall():
                pks.setdefault((schema, table), []).append(col)
        return pks
    
    def _fetch_foreign_keys(self, conn) -> Dict[Tuple[str, str], List[ForeignKeyInfo]]:
        """외래키 조회"""
        sql = """
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
    
    def _fetch_indexes(self, conn) -> Dict[Tuple[str, str], List[IndexInfo]]:
        """인덱스 조회"""
        sql = """
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
        idx: Dict[Tuple[str, str], List[IndexInfo]] = {}
        with conn.cursor() as cur:
            cur.execute(sql)
            for schema, table, indexname, cols, is_unique in cur.fetchall():
                columns = [str(c) for c in (cols or [])]
                idx.setdefault((schema, table), []).append(
                    IndexInfo(name=indexname, columns=columns, is_unique=bool(is_unique))
                )
        return idx
    
    def _build_table_cards(self, tables, columns_map, pk_map, fk_map, idx_map) -> List[TableCard]:
        """테이블 카드 생성"""
        cards = []
        for schema, table, comment in tables:
            cols = columns_map.get((schema, table), [])
            pk_ordered = pk_map.get((schema, table), [])
            pk_cols_set = set(pk_ordered)
            fk_cols = {fk.column for fk in fk_map.get((schema, table), [])}
            
            # PK, FK 설정
            for col in cols:
                col.is_primary_key = col.name in pk_cols_set
                col.is_foreign_key = col.name in fk_cols
            
            fks = fk_map.get((schema, table), [])
            idxs = idx_map.get((schema, table), [])
            qualified = f"{schema}.{table}"
            samples = self._build_sample_queries(schema, table, pk_ordered, fks)
            
            card = TableCard(
                id=qualified,
                object_type="table",
                name=qualified,
                table=qualified,
                schema=schema,
                description=comment or None,
                columns=cols,
                primary_key=pk_ordered,
                foreign_keys=fks,
                indexes=idxs,
                sample_queries=samples,
                business_tags=[],
                embedding=None,
            )
            cards.append(card)
        return cards
    
    def _build_sample_queries(self, schema: str, table: str, primary_key: List[str], foreign_keys: List[ForeignKeyInfo]) -> List[str]:
        """샘플 쿼리 생성"""
        qualified = f"{schema}.{table}" if schema else table
        samples = []
        samples.append(f"SELECT * FROM {qualified} LIMIT 10;")
        if primary_key:
            pk_predicates = " AND ".join([f"{col} = :{col}" for col in primary_key])
            samples.append(f"SELECT * FROM {qualified} WHERE {pk_predicates};")
        for fk in foreign_keys[:2]:
            samples.append(
                f"SELECT t.* FROM {qualified} t JOIN {fk.referenced_table} r ON t.{fk.column} = r.{fk.referenced_column} LIMIT 10;"
            )
        return samples
    
    async def _save_schema_files(self, connection: DbConnection, cards: List[TableCard]) -> Path:
        """스키마 파일 저장"""
        target_base = self.output_dir / "schema" / f"postgres_{connection.database}"
        tables_dir = target_base / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)
        
        for card in cards:
            # JSON 파일
            basename = card.name.replace("/", "_").replace(" ", "_")
            json_path = tables_dir / f"{basename}.json"
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
        
        # index.json
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
        with (target_base / "index.json").open("w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        return target_base

"""
Azure AI Search 인덱싱 스크립트 (전처리 + 임베딩 + 업서트)

기능 개요
- 스키마 테이블 카드(JSON)들을 읽어 한국어 검색 최적화용 텍스트로 평탄화
- Azure OpenAI 임베딩 생성(옵션)
- Azure AI Search 인덱스 생성(없으면) 및 문서 업서트

필수 환경변수
- AZURE_SEARCH_ENDPOINT: 예) https://<service>.search.windows.net
- AZURE_SEARCH_API_KEY: 관리 키(Admin Key)
- AZURE_SEARCH_INDEX_NAME: 생성/사용할 인덱스 이름

임베딩 환경변수(옵션: --no-embedding 사용 시 불필요)
- AZURE_OPENAI_ENDPOINT: https://<resource>.openai.azure.com
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT: 배포명(예: text-embedding-3-small)
- AZURE_OPENAI_API_VERSION: 기본 2024-12-01-preview
- EMBEDDING_DIM: 기본 3072 (배포 모델 차원과 일치하도록 설정 권장)

사용 예시
  uv run python scripts/setup/ingest_schema_ai_search.py \
    --cards-dir scripts/setup/outputs/schema/postgres_ecommerce_db/tables \
    --index-name dbschema-tables
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

try:
    # openai v1
    from openai import AzureOpenAI  # type: ignore
except Exception:  # noqa: BLE001
    AzureOpenAI = None  # type: ignore


# ---------------------------
# 설정/유틸
# ---------------------------


@dataclass
class Config:
    search_endpoint: str
    search_api_key: str
    search_index_name: str

    cards_dir: Path
    create_index: bool
    batch_size: int
    use_embedding: bool

    aoai_endpoint: Optional[str]
    aoai_api_key: Optional[str]
    aoai_deployment: Optional[str]
    aoai_api_version: str
    embedding_dim: int


def load_config(args: argparse.Namespace) -> Config:
    load_dotenv()
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
    api_key = os.getenv("AZURE_SEARCH_API_KEY", "")
    index_name = args.index_name or os.getenv("AZURE_SEARCH_INDEX_NAME", "dbschema-tables")
    if not endpoint or not api_key:
        print("[ERROR] AZURE_SEARCH_ENDPOINT 또는 AZURE_SEARCH_API_KEY 가 비어있습니다.")
        raise SystemExit(2)

    aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    aoai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    aoai_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    aoai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    embedding_dim_str = os.getenv("EMBEDDING_DIM", "3072")
    try:
        embedding_dim = int(embedding_dim_str)
    except ValueError:
        embedding_dim = 3072

    use_embedding = not args.no_embedding
    if use_embedding and (AzureOpenAI is None or not (aoai_endpoint and aoai_api_key and aoai_deployment)):
        print("[WARN] 임베딩 설정이 불충분하여 임베딩 없이 진행합니다. (--no-embedding 권장)")
        use_embedding = False

    return Config(
        search_endpoint=endpoint,
        search_api_key=api_key,
        search_index_name=index_name,
        cards_dir=args.cards_dir,
        create_index=(not args.skip_index_create),
        batch_size=args.batch_size,
        use_embedding=use_embedding,
        aoai_endpoint=aoai_endpoint,
        aoai_api_key=aoai_api_key,
        aoai_deployment=aoai_deployment,
        aoai_api_version=aoai_api_version,
        embedding_dim=embedding_dim,
    )


def iter_card_jsons(cards_dir: Path) -> Iterable[Dict]:
    for p in sorted(cards_dir.glob("*.json")):
        with p.open("r", encoding="utf-8") as f:
            yield json.load(f)


def summarize_columns(cols: List[Dict]) -> str:
    parts: List[str] = []
    for c in cols:
        flags: List[str] = []
        if c.get("is_primary_key"):
            flags.append("PK")
        if c.get("is_foreign_key"):
            flags.append("FK")
        flag_str = f" ({', '.join(flags)})" if flags else ""
        parts.append(f"{c.get('name')}:{c.get('data_type')}{flag_str}")
    return "; ".join(parts)


def summarize_foreign_keys(fks: List[Dict]) -> str:
    if not fks:
        return ""
    return "; ".join(
        f"{fk.get('column')} -> {fk.get('referenced_table')}({fk.get('referenced_column')})" for fk in fks
    )


def summarize_indexes(idxs: List[Dict]) -> str:
    if not idxs:
        return ""
    items: List[str] = []
    for ix in idxs:
        uniq = "UNIQUE" if ix.get("is_unique") else "NON-UNIQUE"
        cols = ", ".join(ix.get("columns") or [])
        items.append(f"{ix.get('name')} ({uniq}) on {cols}")
    return "; ".join(items)


def build_content(card: Dict) -> Tuple[str, str, str, str]:
    """
    비즈니스 컨텍스트를 우선한 검색 최적화 텍스트 생성
    """
    # 기존 기술 정보
    desc = card.get("description") or ""
    cols_text = summarize_columns(card.get("columns") or [])
    rels_text = summarize_foreign_keys(card.get("foreign_keys") or [])
    idx_text = summarize_indexes(card.get("indexes") or [])
    samples = card.get("sample_queries") or []
    samples_text = " | ".join(samples)
    
    # ===== 새로 추가: 비즈니스 컨텍스트 =====
    
    # 1. 비즈니스 용도
    business_purpose = card.get("business_purpose", "")
    
    # 2. 자주 사용하는 쿼리 (한국어)
    common_queries = card.get("common_queries", [])
    common_queries_text = " | ".join(common_queries) if common_queries else ""
    
    # 3. 비즈니스 용어 매핑
    business_terms = card.get("business_terms", {})
    terms_list = []
    for main_term, synonyms in business_terms.items():
        terms_list.append(f"{main_term}({', '.join(synonyms)})")
    terms_text = "; ".join(terms_list)
    
    # 4. KPI 컬럼 강조
    kpi_columns = []
    for col in card.get("columns", []):
        if col.get("is_kpi"):
            kpi_desc = col.get("kpi_description", "")
            kpi_columns.append(f"{col['name']}: {kpi_desc}")
    kpi_text = "; ".join(kpi_columns)
    
    # ===== 한국어 우선 content 생성 =====
    content_parts = [
        f"테이블명: {card.get('name')}",
    ]
    
    # 비즈니스 정보 (있으면 먼저)
    if desc:
        content_parts.append(f"설명: {desc}")
    if business_purpose:
        content_parts.append(f"업무 용도: {business_purpose}")
    
    # 자주 사용하는 지표 (핵심!)
    if common_queries_text:
        content_parts.append(f"자주 분석하는 지표: {common_queries_text}")
    
    # 비즈니스 용어
    if terms_text:
        content_parts.append(f"관련 업무 용어: {terms_text}")
    
    # KPI 컬럼
    if kpi_text:
        content_parts.append(f"주요 지표 컬럼: {kpi_text}")
    
    # 기술 정보 (뒤쪽에)
    content_parts.extend([
        f"전체 컬럼: {cols_text}",
        f"Primary Key: {', '.join(card.get('primary_key') or [])}",
    ])
    
    if rels_text:
        content_parts.append(f"Foreign Keys: {rels_text}")
    if idx_text:
        content_parts.append(f"Indexes: {idx_text}")
    if samples_text:
        content_parts.append(f"예시 SQL: {samples_text}")
    
    content = "\n".join(content_parts)
    
    return content, cols_text, rels_text, samples_text


def ensure_index(cfg: Config) -> None:
    if not cfg.create_index:
        return

    url = f"{cfg.search_endpoint}/indexes/{cfg.search_index_name}?api-version=2024-07-01"
    headers = {"Content-Type": "application/json", "api-key": cfg.search_api_key}
    
    index_def = {
        "name": cfg.search_index_name,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True},
            {"name": "object_type", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "schema", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "table", "type": "Edm.String", "filterable": True, "facetable": True},
            {"name": "name", "type": "Edm.String", "searchable": True, "filterable": True},
            {"name": "description", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
            {"name": "content", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
            {"name": "columns_text", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
            {"name": "relations_text", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
            {"name": "sample_queries_text", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
            {"name": "business_tags", "type": "Collection(Edm.String)", "filterable": True, "facetable": True},
        ]
    }

    # 벡터 필드 추가 (임베딩 사용 시)
    if cfg.use_embedding:
        index_def["fields"].append({
            "name": "embedding",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "dimensions": cfg.embedding_dim,
            "vectorSearchProfile": "vs-hnsw-profile",
        })
        index_def["vectorSearch"] = {
            "algorithms": [{
                "name": "vs-hnsw",
                "kind": "hnsw",
                "hnswParameters": {
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            }],
            "profiles": [{
                "name": "vs-hnsw-profile",
                "algorithm": "vs-hnsw"
            }]
        }

    # 생성 시도
    try:
        resp = httpx.put(url, headers=headers, json=index_def, timeout=30)
        if resp.status_code not in (200, 201, 204):
            print(f"[WARN] 인덱스 생성 실패: {resp.status_code} {resp.text}")
        else:
            print(f"[OK] 인덱스 준비 완료: {cfg.search_index_name}")
    except Exception as e:
        print(f"[WARN] 인덱스 생성 중 예외: {e}")


def embed_texts(cfg: Config, texts: List[str]) -> List[List[float]]:
    if not cfg.use_embedding:
        return [[] for _ in texts]
    assert AzureOpenAI is not None
    client = AzureOpenAI(api_key=cfg.aoai_api_key, azure_endpoint=cfg.aoai_endpoint, api_version=cfg.aoai_api_version)
    vectors: List[List[float]] = [[] for _ in texts]
    B = 16  # 배치 크기(필요 시 CLI 옵션화 가능)
    from openai import APIError, RateLimitError  # type: ignore
    import httpx  # 안전상 재임포트 (버전별 예외 타입 호환)
    for i in range(0, len(texts), B):
        batch = texts[i : i + B]
        try:
            res = client.embeddings.create(model=cfg.aoai_deployment, input=batch)
            emb = [d.embedding for d in res.data]  # type: ignore
            # 차원 검증(최초 확인 시점에 오류를 빠르게 감지)
            if cfg.embedding_dim and emb and len(emb[0]) != cfg.embedding_dim:
                raise RuntimeError(f"EMBEDDING_DIM({cfg.embedding_dim}) != actual({len(emb[0])})")
            vectors[i : i + len(emb)] = emb
        except (APIError, RateLimitError, httpx.HTTPError, RuntimeError) as e:
            print(f"[WARN] 임베딩 배치 실패({i}-{i+len(batch)-1}): {e}")
            # 실패 구간은 빈 벡터 유지
            continue
    return vectors


def build_documents(cfg: Config) -> List[Dict]:
    docs: List[Dict] = []
    raw_cards = list(iter_card_jsons(cfg.cards_dir))
    texts: List[str] = []
    metas: List[Dict] = []

    for card in raw_cards:
        content, cols_text, rels_text, samples_text = build_content(card)
        
        # ✅ ID에서 점(.)을 언더스코어(_)로 변경
        safe_id = (card.get("id") or card.get("name")).replace(".", "_")
        
        doc = {
            "@search.action": "mergeOrUpload",
            "id": safe_id,  # ✅ 안전한 ID 사용
            "object_type": card.get("object_type"),
            "schema": card.get("schema"),
            "table": card.get("table"),
            "name": card.get("name"),
            "description": card.get("description") or "",
            "content": content,
            "columns_text": cols_text,
            "relations_text": rels_text,
            "sample_queries_text": samples_text,
            "business_tags": card.get("business_tags") or [],
        }
        texts.append(content)
        metas.append(doc)

    vectors = embed_texts(cfg, texts)
    for doc, vec in zip(metas, vectors):
        if cfg.use_embedding and vec:
            doc["embedding"] = vec
        docs.append(doc)

    return docs


def upload_documents(cfg: Config, docs: List[Dict]) -> None:
    url = f"{cfg.search_endpoint}/indexes/{cfg.search_index_name}/docs/index?api-version=2024-07-01"
    headers = {"Content-Type": "application/json", "api-key": cfg.search_api_key}
    # 배치 업로드
    for i in range(0, len(docs), cfg.batch_size):
        batch = {"value": docs[i : i + cfg.batch_size]}
        resp = httpx.post(url, headers=headers, json=batch, timeout=60)
        if resp.status_code not in (200, 201):
            print(f"[WARN] 업서트 실패({resp.status_code}): {resp.text}")
        else:
            print(f"[OK] 업서트 성공: {i}..{min(i+cfg.batch_size, len(docs))-1}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest schema table cards into Azure AI Search")
    parser.add_argument(
        "--cards-dir",
        type=Path,
        default=Path("scripts/setup/outputs/schema/postgres_ecommerce_db/tables"),
        help="테이블 카드 JSON 디렉토리",
    )
    parser.add_argument("--index-name", type=str, default=os.getenv("AZURE_SEARCH_INDEX_NAME", "dbschema-tables"))
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--skip-index-create", action="store_true")
    parser.add_argument("--no-embedding", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(args)
    print(f"[INFO] 인덱스 대상: {cfg.search_index_name} @ {cfg.search_endpoint}")
    print(f"[INFO] 카드 디렉토리: {cfg.cards_dir}")
    ensure_index(cfg)
    docs = build_documents(cfg)
    print(f"[INFO] 업서트 문서 수: {len(docs)} (임베딩: {'ON' if cfg.use_embedding else 'OFF'})")
    upload_documents(cfg, docs)
    print("[SUCCESS] 인덱싱 완료")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())



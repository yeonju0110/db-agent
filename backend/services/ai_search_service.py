"""
Azure AI Search 인덱싱 서비스
기존 ingest_schema_ai_search.py 로직을 서비스로 변환
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

from backend.models.db_connection import DbConnection


class AISearchService:
    """Azure AI Search 인덱싱 서비스"""
    
    def __init__(self):
        load_dotenv()
        from backend.config.settings import settings
        
        self.search_endpoint = settings.azure_search_endpoint or os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = settings.azure_search_api_key or os.getenv("AZURE_SEARCH_KEY")
        self.index_name = settings.azure_search_index_name or os.getenv("AZURE_SEARCH_INDEX_NAME", "dbschema-tables")
        
        if not self.search_endpoint or not self.search_key:
            raise ValueError("Azure Search 설정이 필요합니다. AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY를 설정하세요.")
        
        self.credential = AzureKeyCredential(self.search_key)
        self.client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
    
    async def _ensure_index_exists(self):
        """인덱스가 존재하지 않으면 생성"""
        try:
            import httpx
            
            # 인덱스 존재 확인
            url = f"{self.search_endpoint}/indexes/{self.index_name}?api-version=2024-07-01"
            headers = {"api-key": self.search_key}
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        print(f"✅ 인덱스 존재 확인: {self.index_name}")
                        return
                except httpx.HTTPStatusError:
                    pass  # 인덱스가 없음
                
                # 인덱스가 없으면 생성
                print(f"🔨 인덱스 생성 중: {self.index_name}")
                await self._create_index_http(client, headers)
                
        except Exception as e:
            print(f"❌ 인덱스 확인/생성 실패: {e}")
            raise
    
    async def _create_index_http(self, client, headers):
        """HTTP API로 인덱스 생성"""
        url = f"{self.search_endpoint}/indexes/{self.index_name}?api-version=2024-07-01"
        headers["Content-Type"] = "application/json"
        
        index_def = {
            "name": self.index_name,
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True},
                {"name": "db_schema", "type": "Edm.String", "filterable": True},  # schema → db_schema
                {"name": "table_name", "type": "Edm.String", "filterable": True, "searchable": True},
                {"name": "display_name", "type": "Edm.String", "searchable": True, "filterable": True},  # name → display_name
                {"name": "description", "type": "Edm.String", "searchable": True},
                {"name": "content", "type": "Edm.String", "searchable": True},
                {"name": "columns_text", "type": "Edm.String", "searchable": True},
                {"name": "relations_text", "type": "Edm.String", "searchable": True},
                {"name": "sample_queries_text", "type": "Edm.String", "searchable": True},
                {"name": "business_tags", "type": "Collection(Edm.String)", "filterable": True},
                {"name": "tenant_id", "type": "Edm.String", "filterable": True},
                {"name": "connection_id", "type": "Edm.String", "filterable": True},
                {"name": "table_id", "type": "Edm.String", "filterable": True},
            ]
        }
        
        response = await client.put(url, headers=headers, json=index_def, timeout=30)
        if response.status_code in (200, 201, 204):
            print(f"✅ 인덱스 생성 완료: {self.index_name}")
        else:
            raise Exception(f"인덱스 생성 실패: {response.status_code} {response.text}")
    
    async def index_schema(self, connection: DbConnection, tenant_id: str = "default_tenant") -> Dict:
        """스키마를 Azure AI Search에 인덱싱 (멀티테넌트 지원)"""
        try:
            # 인덱스가 없으면 생성
            await self._ensure_index_exists()
            
            # 스키마 파일 로드
            schema_dir = Path("scripts/setup/outputs/schema") / f"postgres_{connection.database}" / "tables"
            if not schema_dir.exists():
                return {
                    "success": False,
                    "error": "스키마 파일이 없습니다. 먼저 스키마 추출을 실행하세요."
                }
            
            # 문서 생성
            documents = []
            for json_file in schema_dir.glob("*.json"):
                with json_file.open('r', encoding='utf-8') as f:
                    table_data = json.load(f)
                
                # 검색 문서 생성 (테넌트 ID 포함)
                doc = self._create_search_document(table_data, connection, tenant_id)
                documents.append(doc)
            
            # 인덱싱 실행
            result = self.client.upload_documents(documents)
            
            # 결과 확인
            success_count = sum(1 for r in result if r.succeeded)
            failed_count = len(result) - success_count
            
            return {
                "success": failed_count == 0,
                "message": f"{success_count}개 문서 인덱싱 완료, {failed_count}개 실패",
                "indexed_count": success_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_search_document(self, table_data: Dict, connection: DbConnection, tenant_id: str = "default_tenant") -> Dict:
        """검색 문서 생성"""
        content, cols_text, rels_text, samples_text = self._build_content(table_data)
        
        safe_id = (table_data.get("id") or table_data.get("name", "")).replace(".", "_")
        doc_id = f"{tenant_id}_{connection.id}_{safe_id}"
        
        business_tags = table_data.get('business_tags', [])
        
        doc = {
            "@search.action": "mergeOrUpload",
            "id": doc_id,
            "db_schema": table_data.get("schema", "public"),  # 변경
            "table_name": table_data.get("table", table_data.get("name", "")),
            "display_name": table_data.get("name", ""),  # 변경
            "description": table_data.get("description", ""),
            "content": content,
            "columns_text": cols_text,
            "relations_text": rels_text,
            "sample_queries_text": samples_text,
            "business_tags": business_tags,
            "tenant_id": tenant_id,
            "connection_id": connection.id,
            "table_id": table_data.get("id", ""),
        }
        
        return doc
    
    def _build_content(self, card: Dict) -> tuple:
        """ingest 스크립트의 build_content 함수 로직"""
        # 기존 기술 정보
        desc = card.get("description") or ""
        cols_text = self._summarize_columns(card.get("columns") or [])
        rels_text = self._summarize_foreign_keys(card.get("foreign_keys") or [])
        idx_text = self._summarize_indexes(card.get("indexes") or [])
        samples = card.get("sample_queries") or []
        samples_text = " | ".join(samples)
        
        # 비즈니스 컨텍스트
        business_purpose = card.get("business_purpose", "")
        common_queries = card.get("common_queries", [])
        common_queries_text = " | ".join(common_queries) if common_queries else ""
        
        # 비즈니스 용어 매핑
        business_terms = card.get("business_terms", {})
        terms_list = []
        for main_term, synonyms in business_terms.items():
            terms_list.append(f"{main_term}({', '.join(synonyms)})")
        terms_text = "; ".join(terms_list)
        
        # KPI 컬럼 강조
        kpi_columns = []
        for col in card.get("columns", []):
            if col.get("is_kpi"):
                kpi_desc = col.get("kpi_description", "")
                kpi_columns.append(f"{col['name']}: {kpi_desc}")
        kpi_text = "; ".join(kpi_columns)
        
        # 한국어 우선 content 생성
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
    
    def _summarize_columns(self, cols: List[Dict]) -> str:
        """컬럼 정보 요약"""
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
    
    def _summarize_foreign_keys(self, fks: List[Dict]) -> str:
        """외래키 정보 요약"""
        if not fks:
            return ""
        return "; ".join(
            f"{fk.get('column')} -> {fk.get('referenced_table')}({fk.get('referenced_column')})" for fk in fks
        )
    
    def _summarize_indexes(self, idxs: List[Dict]) -> str:
        """인덱스 정보 요약"""
        if not idxs:
            return ""
        items: List[str] = []
        for ix in idxs:
            uniq = "UNIQUE" if ix.get("is_unique") else "NON-UNIQUE"
            cols = ", ".join(ix.get("columns") or [])
            items.append(f"{ix.get('name')} ({uniq}) on {cols}")
        return "; ".join(items)
    
    async def search_tables(self, query: str, tenant_id: str = "default_tenant", connection_id: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """테이블 검색"""
        try:
            filters = [f"tenant_id eq '{tenant_id}'"]
            if connection_id:
                filters.append(f"connection_id eq '{connection_id}'")
            
            search_filter = " and ".join(filters) if filters else None
            
            results = self.client.search(
                search_text=query,
                filter=search_filter,
                top=top_k,
                include_total_count=True
            )
            
            tables = []
            for result in results:
                tables.append({
                    "table_id": result.get('table_id'),
                    "table_name": result.get('table_name'),
                    "db_schema": result.get('db_schema'),  # 변경
                    "display_name": result.get('display_name'),  # 변경
                    "description": result.get('description'),
                    "business_tags": result.get('business_tags', []),
                    "score": result.get('@search.score', 0)
                })
            
            return tables
            
        except Exception as e:
            print(f"검색 오류: {e}")
            return []

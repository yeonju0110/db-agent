"""
Azure AI Search 기반 스키마 검색 클라이언트
자연어 쿼리를 받아 관련 테이블 정보를 반환
"""
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv


@dataclass
class TableInfo:
    """검색된 테이블 정보"""
    name: str
    description: str
    columns_text: str
    common_queries: List[str]
    score: float
    
    def to_context_string(self) -> str:
        """프롬프트용 컨텍스트 문자열 생성"""
        return f"""
테이블: {self.name}
설명: {self.description}
컬럼: {self.columns_text}
자주 사용하는 쿼리: {', '.join(self.common_queries) if self.common_queries else '없음'}
""".strip()


class SchemaRetriever:
    """Azure AI Search 기반 스키마 검색기"""
    
    def __init__(self):
        load_dotenv()
        
        # 환경 변수 로드 및 검증
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        api_key = os.getenv("AZURE_SEARCH_API_KEY")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "dbschema-tables")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        missing = [k for k, v in {
            "AZURE_SEARCH_ENDPOINT": endpoint,
            "AZURE_SEARCH_API_KEY": api_key,
            "AZURE_OPENAI_API_KEY": azure_api_key,
            "AZURE_OPENAI_ENDPOINT": azure_endpoint,
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": self.embedding_deployment,
        }.items() if not v]
        if missing:
            raise ValueError(f"필수 환경 변수 누락: {', '.join(missing)}")

        # Azure Search 클라이언트
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )
        
        # Azure OpenAI 임베딩 클라이언트
        self.openai_client = AzureOpenAI(
            api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            api_version=azure_api_version
        )
    
    def _create_embedding(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        try:
            # dimensions는 설정/지원 시에만 전달
            emb_dim_env = os.getenv("AZURE_OPENAI_EMBEDDING_DIM") or os.getenv("EMBEDDING_DIM")
            kwargs = {"model": self.embedding_deployment, "input": text}
            if emb_dim_env is not None:
                try:
                    emb_dim = int(str(emb_dim_env).strip())
                    if emb_dim > 0:
                        kwargs["dimensions"] = emb_dim
                except (ValueError, TypeError):
                    pass
            response = self.openai_client.embeddings.create(**kwargs)
            return response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 실패: {e}")
            return []

    def search_relevant_tables(
        self, 
        query: str, 
        top_k: int = 3
    ) -> List[TableInfo]:
        """
        자연어 쿼리로 관련 테이블 검색 (순수 벡터 검색)
        
        Args:
            query: 한국어 자연어 쿼리 (예: "오늘 주문 건수")
            top_k: 반환할 테이블 개수 (기본 3개)
            
        Returns:
            검색된 테이블 정보 리스트 (유사도 높은 순)
        """
        # 1. 쿼리를 벡터로 변환
        query_vector = self._create_embedding(query)
        
        if not query_vector:
            return self._fallback_text_search(query, top_k)
        
        # 2. 순수 벡터 검색
        try:
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k * 2,
                fields="embedding"
            )
            
            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["name", "description", "columns_text", "business_tags", "content"],
                top=top_k
            )
            
            # 3. 결과 파싱
            tables = []
            for result in results:
                # content에서 common_queries 추출
                common_queries = []
                if "content" in result:
                    content = result["content"]
                    if "자주 분석하는 지표:" in content:
                        queries_section = content.split("자주 분석하는 지표:")[1].split("\n")[0]
                        common_queries = [q.strip() for q in queries_section.split("|") if q.strip()]
                
                table = TableInfo(
                    name=result["name"],
                    description=result.get("description", ""),
                    columns_text=result.get("columns_text", ""),
                    common_queries=common_queries,
                    score=result.get("@search.score", 0.0)
                )
                tables.append(table)
            
            return tables
            
        except Exception as e:
            print(f"벡터 검색 실패: {e}")
            return self._fallback_text_search(query, top_k)
    
    def _fallback_text_search(self, query: str, top_k: int) -> List[TableInfo]:
        """벡터 검색 실패 시 텍스트 검색"""
        try:
            results = self.search_client.search(
                search_text=query,
                select=["name", "description", "columns_text", "content"],
                top=top_k
            )
            
            tables = []
            for result in results:
                table = TableInfo(
                    name=result["name"],
                    description=result.get("description", ""),
                    columns_text=result.get("columns_text", ""),
                    common_queries=[],
                    score=result.get("@search.score", 0.0)
                )
                tables.append(table)
            
            return tables
        except Exception as e:
            print(f"텍스트 검색도 실패: {e}")
            return []


# 테스트 코드
if __name__ == "__main__":
    retriever = SchemaRetriever()
    
    test_queries = [
        "오늘 주문 건수",
        "결제 완료된 주문",
        "신규 회원가입 수"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"쿼리: {query}")
        print(f"{'='*60}")
        
        tables = retriever.search_relevant_tables(query, top_k=3)
        
        for i, table in enumerate(tables, 1):
            print(f"\n{i}. {table.name} (점수: {table.score:.2f})")
            print(f"   {table.description[:80]}...")
            print(f"   컬럼: {table.columns_text[:100]}...")
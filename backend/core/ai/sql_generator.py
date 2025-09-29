"""
SQL 생성기 - SchemaRetriever + Azure OpenAI
"""
import os
from typing import Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

try:
    from .schema_retriever import SchemaRetriever
    from .prompt_builder import SQLPromptBuilder
except ImportError:
    from schema_retriever import SchemaRetriever
    from prompt_builder import SQLPromptBuilder


class SQLGenerator:
    """자연어 → SQL 변환기"""
    
    def __init__(self):
        load_dotenv()
        
        self.retriever = SchemaRetriever()

        # 환경 변수 검증 및 클라이언트 초기화
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

        if not azure_api_key:
            raise RuntimeError("AZURE_OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        if not azure_endpoint:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT 환경 변수가 설정되지 않았습니다.")
        if not chat_deployment:
            raise RuntimeError(
                "Azure OpenAI 배포 이름이 없습니다. AZURE_OPENAI_DEPLOYMENT_NAME (또는 AZURE_OPENAI_CHAT_DEPLOYMENT)를 설정하세요."
            )

        self.openai_client = AzureOpenAI(
            api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            api_version=azure_api_version
        )
        self.chat_deployment = chat_deployment
    
    def generate_sql(
        self,
        user_query: str,
        top_k_tables: int = 3,
        temperature: float = 0.0
    ) -> dict:
        """
        자연어 질문을 SQL로 변환
        
        Args:
            user_query: 사용자의 자연어 질문
            top_k_tables: 검색할 테이블 개수
            temperature: 생성 다양성 (0.0 = 결정적)
            
        Returns:
            {
                "sql": "SELECT ...",
                "tables_used": ["public.orders", ...],
                "confidence_score": 0.85
            }
        """
        # 1. 관련 테이블 검색
        relevant_tables = self.retriever.search_relevant_tables(
            user_query, 
            top_k=top_k_tables
        )
        
        if not relevant_tables:
            return {
                "error": "관련 테이블을 찾을 수 없습니다",
                "sql": None,
                "tables_used": []
            }
        
        # 2. 프롬프트 생성
        messages = SQLPromptBuilder.build_messages(user_query, relevant_tables)
        
        # 3. SQL 생성
        try:
            response = self.openai_client.chat.completions.create(
                model=self.chat_deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=500
            )
            
            sql = response.choices[0].message.content.strip()
            
            # 4. 후처리: 마크다운 코드 블록 제거
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            elif sql.startswith("```"):
                sql = sql.replace("```", "").strip()
            
            # 세미콜론 추가 (없으면)
            if not sql.endswith(";"):
                sql += ";"
            
            return {
                "sql": sql,
                "tables_used": [t.name for t in relevant_tables],
                "confidence_score": relevant_tables[0].score if relevant_tables else 0.0,
                "tables_info": relevant_tables
            }
            
        except Exception as e:
            return {
                "error": (
                    "SQL 생성 실패: Azure OpenAI 호출 에러. 배포명이 올바른지 확인하세요. "
                    "(오류 세부: " + str(e) + ")"
                ) if "DeploymentNotFound" in str(e) else f"SQL 생성 실패: {str(e)}",
                "sql": None,
                "tables_used": []
            }


# 테스트
if __name__ == "__main__":
    generator = SQLGenerator()
    
    test_queries = [
        "오늘 주문 건수",
        "이번 달 총 매출액",
        "결제 완료된 주문의 평균 금액",
        "신규 가입자 수 (최근 7일)"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"질문: {query}")
        print(f"{'='*80}")
        
        result = generator.generate_sql(query)
        
        if result.get("error"):
            print(f"❌ {result['error']}")
        else:
            print(f"✅ SQL 생성 완료 (신뢰도: {result['confidence_score']:.2f})")
            print(f"\n사용된 테이블: {', '.join(result['tables_used'])}")
            print(f"\n{result['sql']}")
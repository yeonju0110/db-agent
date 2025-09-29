"""
SQL 생성용 프롬프트 빌더
"""
from typing import List

try:
    from .schema_retriever import TableInfo
except ImportError:
    from schema_retriever import TableInfo


class SQLPromptBuilder:
    """SQL 생성용 프롬프트 빌더"""
    
    SYSTEM_PROMPT = """당신은 PostgreSQL 전문가입니다.
사용자의 한국어 질문을 정확한 SQL 쿼리로 변환하는 것이 목표입니다.

## 핵심 원칙
1. **테이블 정보만 사용**: 제공된 테이블 스키마에 있는 컬럼만 사용
2. **PostgreSQL 문법**: 표준 PostgreSQL 문법 준수
3. **한국어 이해**: 비즈니스 용어를 기술 컬럼명으로 정확히 매핑
4. **현재 시간 기준**: "오늘", "이번 달" 등은 CURRENT_DATE 기준
5. **집계 함수 활용**: COUNT, SUM, AVG 등 적절히 사용
6. **JOIN 최소화**: 필요한 경우에만 JOIN 사용

## 출력 형식
- SQL 쿼리만 출력 (설명 없이)
- 세미콜론(;)으로 종료
- 주석 없이 실행 가능한 형태
"""

    @staticmethod
    def build_user_prompt(
        user_query: str,
        relevant_tables: List[TableInfo]
    ) -> str:
        """
        사용자 쿼리 + 관련 테이블 정보로 프롬프트 생성
        
        Args:
            user_query: 사용자의 자연어 질문
            relevant_tables: 검색된 관련 테이블 정보
            
        Returns:
            완성된 프롬프트 문자열
        """
        # 1. 테이블 정보 섹션
        tables_context = "\n\n".join([
            f"## {i+1}. {table.name}\n{table.to_context_string()}"
            for i, table in enumerate(relevant_tables)
        ])
        
        # 2. 전체 프롬프트 조합
        prompt = f"""# 사용 가능한 테이블 정보

{tables_context}

---

# 사용자 질문
{user_query}

# SQL 쿼리 생성
위 테이블 정보를 참고하여 사용자 질문에 답하는 PostgreSQL 쿼리를 작성하세요.
"""
        return prompt
    
    @staticmethod
    def build_messages(
        user_query: str,
        relevant_tables: List[TableInfo]
    ) -> List[dict]:
        """
        OpenAI Chat API용 메시지 형식으로 변환
        
        Returns:
            [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        """
        return [
            {
                "role": "system",
                "content": SQLPromptBuilder.SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": SQLPromptBuilder.build_user_prompt(user_query, relevant_tables)
            }
        ]


# 테스트
if __name__ == "__main__":
    from schema_retriever import SchemaRetriever
    
    retriever = SchemaRetriever()
    builder = SQLPromptBuilder()
    
    # 예시 쿼리
    test_query = "오늘 주문 건수를 알려줘"
    
    # 1. 관련 테이블 검색
    tables = retriever.search_relevant_tables(test_query, top_k=3)
    
    # 2. 프롬프트 생성
    messages = builder.build_messages(test_query, tables)
    
    # 3. 출력
    print("="*80)
    print("SYSTEM PROMPT:")
    print("="*80)
    print(messages[0]["content"])
    
    print("\n" + "="*80)
    print("USER PROMPT:")
    print("="*80)
    print(messages[1]["content"])
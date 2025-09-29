"""
AI를 활용한 비즈니스 컨텍스트 초안 생성 스크립트
"""
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from openai import AzureOpenAI

def generate_business_context_draft(table_card: dict) -> str:
    """GPT-4로 비즈니스 컨텍스트 초안 자동 생성"""
    load_dotenv()
    
    # 컬럼 정보를 더 간결하게 (토큰 절약)
    columns_summary = ', '.join([
        f"{c['name']}({c['data_type']})" 
        for c in table_card['columns'][:10]  # 최대 10개만
    ])
    if len(table_card['columns']) > 10:
        columns_summary += f" ... 외 {len(table_card['columns']) - 10}개"
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    
    prompt = f"""
다음 이커머스 데이터베이스 테이블에 대한 비즈니스 컨텍스트를 생성해주세요.

테이블명: {table_card['name']}
스키마: {table_card.get('schema', 'public')}
컬럼: {columns_summary}

아래 YAML 형식으로 작성해주세요 (YAML 마크다운 없이 순수 YAML만):

{table_card['name']}:
  description: "테이블의 업무적 의미 (한 문장)"
  purpose: "이 테이블의 주요 용도"
  tags: ["태그1", "태그2", "태그3"]
  common_queries:
    - "자주 확인하는 지표 1"
    - "자주 확인하는 지표 2"
    - "자주 확인하는 지표 3"
  business_terms:
    한국어용어1: ["영어명", "동의어1", "동의어2"]
    한국어용어2: ["영어명", "동의어1"]
  kpi_columns:
    중요컬럼명1: "이 컬럼이 나타내는 KPI"
    중요컬럼명2: "이 컬럼이 나타내는 KPI"
  column_meanings:
    컬럼명1: "이 컬럼의 업무적 의미"
    컬럼명2: "이 컬럼의 업무적 의미"
"""
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        # 마크다운 코드 블록 제거 (있을 경우)
        if content.startswith("```yaml"):
            content = content.replace("```yaml", "").replace("```", "").strip()
        
        return content
    except Exception as e:
        print(f"  ⚠️ API 호출 실패: {e}")
        # 실패 시 기본 템플릿 반환
        return f"""
{table_card['name']}:
  description: "TODO: 설명 추가 필요"
  purpose: "TODO: 용도 추가 필요"
  tags: ["미분류"]
  common_queries: []
  business_terms: {{}}
  kpi_columns: {{}}
  column_meanings: {{}}
"""

def main():
    load_dotenv()
    
    tables_dir = Path("scripts/setup/outputs/schema/postgres_ecommerce_db/tables")
    output_file = Path("scripts/data/business_context/tables_draft.yaml")
    
    if not tables_dir.exists():
        print(f"❌ 테이블 디렉토리가 없습니다: {tables_dir}")
        print("먼저 export_schema.py를 실행하세요")
        return 1
    
    draft_parts = []
    for json_file in sorted(tables_dir.glob("*.json")):
        with json_file.open() as f:
            card = json.load(f)
        print(f"처리 중: {card['name']}")
        draft = generate_business_context_draft(card)
        draft_parts.append(draft)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n\n".join(draft_parts), encoding='utf-8')
    print(f"\n✅ 초안 생성 완료: {output_file}")
    print("📝 검토 후 tables.yaml로 이름을 변경하세요")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
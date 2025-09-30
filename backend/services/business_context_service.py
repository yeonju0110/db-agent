"""
비즈니스 컨텍스트 생성 서비스
기존 generate_business_context_draft.py 로직을 서비스로 변환
"""
import json
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

from backend.models.db_connection import DbConnection


class BusinessContextService:
    """비즈니스 컨텍스트 생성 서비스"""
    
    def __init__(self):
        load_dotenv()
        self.output_dir = Path("scripts/setup/outputs")
        self.business_context_dir = Path("scripts/data/business_context")
        self.business_context_dir.mkdir(parents=True, exist_ok=True)
        
        # Azure OpenAI 클라이언트 초기화
        from backend.config.settings import settings
        
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=settings.azure_openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=settings.azure_openai_api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        )
        self.deployment_name = settings.azure_openai_deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    async def generate_business_context(self, connection: DbConnection) -> Dict:
        """비즈니스 컨텍스트 생성"""
        try:
            # 스키마 파일 경로
            schema_dir = self.output_dir / "schema" / f"postgres_{connection.database}" / "tables"
            if not schema_dir.exists():
                return {
                    "success": False,
                    "error": "스키마 파일이 없습니다. 먼저 스키마 추출을 실행하세요."
                }
            
            # 각 테이블에 대해 비즈니스 컨텍스트 생성
            draft_parts = []
            for json_file in sorted(schema_dir.glob("*.json")):
                with json_file.open() as f:
                    card = json.load(f)
                
                draft = await self._generate_table_context(card)
                draft_parts.append(draft)
            
            # YAML 파일로 저장
            output_file = self.business_context_dir / f"tables_draft_{connection.database}.yaml"
            output_file.write_text("\n\n".join(draft_parts), encoding='utf-8')
            
            return {
                "success": True,
                "message": f"{len(draft_parts)}개 테이블의 비즈니스 컨텍스트 생성 완료",
                "output_file": str(output_file)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_table_context(self, table_card: Dict) -> str:
        """개별 테이블의 비즈니스 컨텍스트 생성"""
        try:
            # 컬럼 정보 요약
            columns_summary = ', '.join([
                f"{c['name']}({c['data_type']})" 
                for c in table_card['columns'][:10]  # 최대 10개만
            ])
            if len(table_card['columns']) > 10:
                columns_summary += f" ... 외 {len(table_card['columns']) - 10}개"
            
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
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            # 마크다운 코드 블록 제거
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
    
    async def apply_business_context(self, connection: DbConnection) -> Dict:
        """비즈니스 컨텍스트를 스키마에 적용"""
        try:
            # 비즈니스 컨텍스트 파일 로드
            context_file = self.business_context_dir / f"tables_draft_{connection.database}.yaml"
            if not context_file.exists():
                return {
                    "success": False,
                    "error": "비즈니스 컨텍스트 파일이 없습니다."
                }
            
            with context_file.open('r', encoding='utf-8') as f:
                context_data = yaml.safe_load(f)
            
            # 스키마 파일들에 비즈니스 컨텍스트 적용
            schema_dir = self.output_dir / "schema" / f"postgres_{connection.database}" / "tables"
            applied_count = 0
            
            for json_file in schema_dir.glob("*.json"):
                with json_file.open('r', encoding='utf-8') as f:
                    table_data = json.load(f)
                
                table_name = table_data['name']
                if table_name in context_data:
                    # 비즈니스 컨텍스트 적용
                    table_data['business_purpose'] = context_data[table_name].get('description', '')
                    table_data['business_tags'] = context_data[table_name].get('tags', [])
                    table_data['common_queries'] = context_data[table_name].get('common_queries', [])
                    table_data['business_terms'] = context_data[table_name].get('business_terms', {})
                    table_data['kpi_columns'] = context_data[table_name].get('kpi_columns', {})
                    table_data['column_meanings'] = context_data[table_name].get('column_meanings', {})
                    
                    # 파일 저장
                    with json_file.open('w', encoding='utf-8') as f:
                        json.dump(table_data, f, ensure_ascii=False, indent=2)
                    
                    applied_count += 1
            
            return {
                "success": True,
                "message": f"{applied_count}개 테이블에 비즈니스 컨텍스트 적용 완료"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

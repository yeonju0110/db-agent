"""
비즈니스 컨텍스트 추가 스크립트

기능:
- export_schema.py로 추출한 JSON에 비즈니스 의미 추가
- 테이블/컬럼에 대한 업무 설명, 자주 사용하는 쿼리, 용어 매핑 추가

사용법:
  1. scripts/data/business_context/tables.yaml 작성
  2. uv run python scripts/setup/enrich_business_context.py
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import argparse


def load_business_mapping(mapping_file: Path) -> Dict:
    """비즈니스 컨텍스트 매핑 파일 로드"""
    with mapping_file.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def enrich_table_card(card: Dict, business_info: Dict) -> Dict:
    """테이블 카드에 비즈니스 정보 추가"""
    
    # 기본 비즈니스 정보
    card['description'] = business_info.get('description', card.get('description'))
    card['business_purpose'] = business_info.get('purpose', '')
    
    # 자주 사용하는 쿼리 패턴
    card['common_queries'] = business_info.get('common_queries', [])
    
    # 비즈니스 용어 매핑
    card['business_terms'] = business_info.get('business_terms', {})
    
    # 비즈니스 태그
    card['business_tags'] = business_info.get('tags', [])
    
    # 컬럼별 비즈니스 의미
    column_meanings = business_info.get('column_meanings', {})
    for col in card.get('columns', []):
        col_name = col['name']
        if col_name in column_meanings:
            col['description'] = column_meanings[col_name]
    
    # KPI 지표 컬럼 표시
    kpi_columns = business_info.get('kpi_columns', {})
    for col in card.get('columns', []):
        if col['name'] in kpi_columns:
            col['is_kpi'] = True
            col['kpi_description'] = kpi_columns[col['name']]
    
    return card


def create_searchable_text(card: Dict) -> str:
    """검색 최적화된 텍스트 생성 (한국어 중심)"""
    parts = []
    
    # 테이블명 + 설명
    parts.append(f"테이블: {card['name']}")
    if card.get('description'):
        parts.append(f"설명: {card['description']}")
    if card.get('business_purpose'):
        parts.append(f"용도: {card['business_purpose']}")
    
    # 컬럼 정보 (KPI 우선)
    kpi_cols = [c for c in card.get('columns', []) if c.get('is_kpi')]
    regular_cols = [c for c in card.get('columns', []) if not c.get('is_kpi')]
    
    if kpi_cols:
        parts.append("주요 지표 컬럼:")
        for col in kpi_cols:
            parts.append(f"  - {col['name']}({col['data_type']}): {col.get('kpi_description', '')}")
    
    parts.append(f"전체 컬럼: {', '.join([c['name'] for c in card.get('columns', [])])}")
    
    # 자주 사용하는 쿼리
    if card.get('common_queries'):
        parts.append("자주 분석하는 지표:")
        for q in card['common_queries']:
            parts.append(f"  - {q}")
    
    # 비즈니스 용어
    if card.get('business_terms'):
        parts.append("관련 용어:")
        for main_term, synonyms in card['business_terms'].items():
            parts.append(f"  - {main_term}: {', '.join(synonyms)}")
    
    # 샘플 쿼리
    if card.get('sample_queries'):
        parts.append("예시 SQL:")
        for sql in card['sample_queries'][:3]:  # 최대 3개
            parts.append(f"  {sql}")
    
    return '\n'.join(parts)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="비즈니스 컨텍스트 적용")
    parser.add_argument(
        "--tables-dir",
        type=Path,
        default=Path("scripts/setup/outputs/schema/postgres_ecommerce_db/tables"),
        help="테이블 JSON 디렉토리"
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=Path("scripts/data/business_context/tables.yaml"),
        help="비즈니스 매핑 YAML 파일"
    )
    return parser.parse_args()

def main():
    # 경로 설정
    args = parse_args()
    base_dir = args.tables_dir
    mapping_file = args.mapping_file
    
    # 비즈니스 매핑 로드
    if not mapping_file.exists():
        print(f"❌ 비즈니스 매핑 파일이 없습니다: {mapping_file}")
        print("📝 scripts/data/business_context/tables.yaml 파일을 먼저 작성해주세요.")
        return 1
    
    business_mapping = load_business_mapping(mapping_file)
    
    # 모든 테이블 카드 처리
    enriched_count = 0
    for json_file in base_dir.glob('*.json'):
        with json_file.open('r', encoding='utf-8') as f:
            card = json.load(f)
        
        table_name = card['name']
        
        # 비즈니스 정보가 있으면 추가
        if table_name in business_mapping:
            card = enrich_table_card(card, business_mapping[table_name])
            
            # 검색 최적화 텍스트 생성
            card['searchable_text'] = create_searchable_text(card)
            
            # 저장
            with json_file.open('w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            
            enriched_count += 1
            print(f"✅ {table_name} - 비즈니스 컨텍스트 추가 완료")
        else:
            print(f"⚠️  {table_name} - 비즈니스 매핑 정보 없음")
    
    print(f"\n✅ 총 {enriched_count}개 테이블 처리 완료")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
# DB agent

## 실행순서
```bash
# 0. 환경 변수 설정
cp .env.sample .env

# 1. 스키마 추출
uv run python scripts/setup/export_schema.py

# 2. AI로 초안 생성 (선택사항)
uv run python scripts/setup/generate_business_context_draft.py

# 3. 비즈니스 컨텍스트 수동 작성/수정
# scripts/data/business_context/tables_draft.yaml → tables.yaml

# 4. 비즈니스 컨텍스트 적용
uv run python scripts/setup/enrich_business_context.py

# 5. 파이프라인 검증
uv run python scripts/setup/validate_pipeline.py

# 6. Azure AI Search 인덱싱
uv run python scripts/setup/ingest_schema_ai_search.py

# 7. 검색 테스트
uv run python scripts/setup/test_search.py
```
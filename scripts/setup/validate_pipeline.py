# scripts/setup/validate_pipeline.py
"""
RAG 파이프라인 검증 스크립트
각 단계가 올바르게 완료되었는지 확인
"""

def main():
    from pathlib import Path
    
    checks = []
    
    # 1. 스키마 추출 확인
    schema_dir = Path("scripts/setup/outputs/schema/postgres_ecommerce_db/tables")
    if schema_dir.exists() and len(list(schema_dir.glob("*.json"))) > 0:
        checks.append(("✅", "스키마 추출 완료"))
    else:
        checks.append(("❌", "스키마 추출 필요: uv run python scripts/setup/export_schema.py"))
    
    # 2. 비즈니스 컨텍스트 파일 확인
    yaml_file = Path("scripts/data/business_context/tables.yaml")
    if yaml_file.exists():
        checks.append(("✅", "비즈니스 컨텍스트 파일 존재"))
        
        # 3. JSON에 비즈니스 정보 적용 확인
        import json
        sample_json = list(schema_dir.glob("*.json"))[0]
        with sample_json.open() as f:
            data = json.load(f)
        
        if "business_purpose" in data or "common_queries" in data:
            checks.append(("✅", "비즈니스 컨텍스트 적용 완료"))
        else:
            checks.append(("⚠️", "비즈니스 컨텍스트 미적용: uv run python scripts/setup/enrich_business_context.py"))
    else:
        checks.append(("❌", "비즈니스 컨텍스트 파일 필요"))
    
    # 결과 출력
    print("\n=== RAG 파이프라인 상태 ===\n")
    for status, message in checks:
        print(f"{status} {message}")
    
    print("\n=== 다음 단계 ===")
    if all(c[0] == "✅" for c in checks):
        print("🚀 준비 완료! Azure AI Search 인덱싱 실행:")
        print("   uv run python scripts/setup/ingest_schema_ai_search.py")
    else:
        print("위의 ❌ 또는 ⚠️ 항목을 먼저 완료하세요")

if __name__ == "__main__":
    main()
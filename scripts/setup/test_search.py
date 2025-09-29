# scripts/setup/test_search.py
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    endpoint   = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    api_key    = os.getenv("AZURE_SEARCH_API_KEY")

    missing = [k for k, v in {
        "AZURE_SEARCH_ENDPOINT": endpoint,
        "AZURE_SEARCH_INDEX_NAME": index_name,
    }.items() if not v]
    if missing:
        raise ValueError(f"필수 환경변수 누락: {', '.join(missing)} (.env.example 참고)")

    if api_key:
        credential = AzureKeyCredential(api_key)
    else:
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
        except Exception as ex:
            raise ValueError("AZURE_SEARCH_API_KEY 미설정, DefaultAzureCredential 초기화 실패: Azure 로그인 구성 또는 API 키를 설정하세요.") from ex

    client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=credential
    )

    # 테스트 쿼리들
    test_queries = [
        "오늘 주문 건수",
        "결제 완료",
        "신규 회원가입",
        "상품 재고"
    ]

    for query in test_queries:
        print(f"\n검색어: {query}")
        results = client.search(query, top=3)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name']} (점수: {result['@search.score']:.2f})")
            print(f"     {result.get('description', '')[:50]}...")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
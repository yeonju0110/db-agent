# scripts/setup/test_search.py
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()

    client = SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
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
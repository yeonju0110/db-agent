"""
Cosmos DB 데이터베이스 및 컨테이너 초기화
"""
import os
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("COSMOS_ENDPOINT")
key = os.getenv("COSMOS_KEY")
database_name = os.getenv("COSMOS_DATABASE", "db-monitoring")

client = CosmosClient(endpoint, key)

# 데이터베이스 생성
database = client.create_database_if_not_exists(id=database_name)
print(f"✓ 데이터베이스 생성: {database_name}")

# 컨테이너 생성
containers = [
    ("metrics", "/id"),
    ("histories", "/metric_id"),
    ("anomalies", "/metric_id"),
    ("connections", "/id")
]

for container_name, partition_key in containers:
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path=partition_key)
    )
    print(f"✓ 컨테이너 생성: {container_name} (파티션 키: {partition_key})")

print("\n초기화 완료!")
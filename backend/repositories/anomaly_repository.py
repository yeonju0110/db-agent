"""
이상치 데이터 리포지토리
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from azure.cosmos import CosmosClient, PartitionKey
from backend.config.settings import get_settings

class AnomalyRepository:
    def __init__(self):
        """이상치 데이터 리포지토리 초기화"""
        settings = get_settings()
        
        # Cosmos DB 연결 설정
        self.cosmos_endpoint = settings.cosmos_endpoint or os.getenv("COSMOS_ENDPOINT")
        self.cosmos_key = settings.cosmos_key or os.getenv("COSMOS_KEY")
        self.database_name = settings.cosmos_database or os.getenv("COSMOS_DATABASE", "db-monitoring")
        self.container_name = "anomalies"
        
        if not self.cosmos_endpoint or not self.cosmos_key:
            raise ValueError("Cosmos DB 연결 정보가 설정되지 않았습니다.")
        
        # Cosmos DB 클라이언트 생성
        self.client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
        
        # 데이터베이스와 컨테이너 생성/확인
        self._ensure_database_and_container()
    
    def _ensure_database_and_container(self):
        """데이터베이스와 컨테이너가 존재하는지 확인하고 없으면 생성"""
        try:
            # 데이터베이스 생성/확인
            try:
                self.database = self.client.create_database_if_not_exists(id=self.database_name)
            except Exception as e:
                print(f"데이터베이스 생성 오류: {e}")
                self.database = self.client.get_database_client(self.database_name)
            
            # 컨테이너 생성/확인 (멀티테넌트를 위해 tenant_id를 파티션 키로 사용)
            try:
                self.container = self.database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/tenant_id")
                )
            except Exception as e:
                print(f"컨테이너 생성 오류: {e}")
                self.container = self.database.get_container_client(self.container_name)
                
        except Exception as e:
            print(f"Cosmos DB 초기화 오류: {e}")
            raise
    
    def save_anomaly_detection(self, detection: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        """이상치 검사 결과 저장"""
        try:
            # ID 생성
            detection_id = str(uuid.uuid4())
            
            # 문서 생성
            document = {
                "id": detection_id,
                "type": "table_anomaly_detection",
                "tenant_id": tenant_id,
                "table_name": detection["table_name"],
                "detected_at": detection["detected_at"],
                "total_records": detection["total_records"],
                "duplicate_count": detection["duplicate_count"],
                "null_count": detection["null_count"],
                "anomaly_count": detection["anomaly_count"],
                "status": detection["status"],
                "is_acknowledged": detection.get("is_acknowledged", False),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Cosmos DB에 저장
            response = self.container.create_item(document)
            
            # 저장된 문서 반환
            return response
            
        except Exception as e:
            print(f"이상치 검사 결과 저장 오류: {e}")
            raise
    
    def get_anomalies(
        self, 
        table_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        tenant_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """이상치 목록 조회"""
        try:
            # 쿼리 구성
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detection' AND c.tenant_id = @tenant_id"
            parameters = [{"name": "@tenant_id", "value": tenant_id}]
            
            if table_name:
                query += " AND c.table_name = @table_name"
                parameters.append({"name": "@table_name", "value": table_name})
            
            if status:
                query += " AND c.status = @status"
                parameters.append({"name": "@status", "value": status})
            
            query += " ORDER BY c.detected_at DESC"
            
            # 쿼리 실행
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True  # 파티션 키를 사용하더라도 True로 설정
            )
            
            # 결과 반환
            results = []
            count = 0
            for item in items:
                if count >= limit:
                    break
                results.append(item)
                count += 1
            
            return results
            
        except Exception as e:
            print(f"이상치 목록 조회 오류: {e}")
            return []
    
    def get_anomaly_by_id(self, detection_id: str, tenant_id: str = "default") -> Optional[Dict[str, Any]]:
        """ID로 이상치 검사 결과 조회"""
        try:
            item = self.container.read_item(
                item=detection_id,
                partition_key=tenant_id
            )
            return item
        except Exception as e:
            print(f"이상치 검사 결과 조회 오류: {e}")
            return None
    
    def update_anomaly(self, detection_id: str, updates: Dict[str, Any], tenant_id: str = "default") -> Optional[Dict[str, Any]]:
        """이상치 검사 결과 업데이트"""
        try:
            # 기존 문서 조회
            existing = self.container.read_item(
                item=detection_id,
                partition_key=tenant_id
            )
            
            # 업데이트 적용
            existing.update(updates)
            existing["updated_at"] = datetime.utcnow().isoformat()
            
            # 저장
            response = self.container.replace_item(
                item=detection_id,
                body=existing
            )
            
            return response
            
        except Exception as e:
            print(f"이상치 검사 결과 업데이트 오류: {e}")
            return None
    
    def delete_anomaly(self, detection_id: str, tenant_id: str = "default") -> bool:
        """이상치 검사 결과 삭제"""
        try:
            self.container.delete_item(
                item=detection_id,
                partition_key=tenant_id
            )
            return True
        except Exception as e:
            print(f"이상치 검사 결과 삭제 오류: {e}")
            return False


def get_anomaly_repository() -> AnomalyRepository:
    """이상치 리포지토리 인스턴스 반환"""
    return AnomalyRepository()

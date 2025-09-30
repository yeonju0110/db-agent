"""
DB 연결 정보 Cosmos DB 리포지토리
"""
import os
from typing import List, Optional
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from cryptography.fernet import Fernet
import base64

from backend.models.db_connection import DbConnection
from backend.config.settings import settings


class DbConnectionRepository:
    """DB 연결 정보 Cosmos DB 리포지토리"""
    
    def __init__(self):
        # Cosmos DB 연결 설정 (기존 환경변수 키 사용)
        self.cosmos_endpoint = settings.cosmos_endpoint or os.getenv("COSMOS_ENDPOINT")
        self.cosmos_key = settings.cosmos_key or os.getenv("COSMOS_KEY")
        self.database_name = settings.cosmos_database or os.getenv("COSMOS_DATABASE", "db-monitoring")
        self.container_name = "db-connections"
        
        if not self.cosmos_endpoint or not self.cosmos_key:
            raise ValueError("Cosmos DB 설정이 필요합니다. COSMOS_ENDPOINT, COSMOS_KEY를 설정하세요.")
        
        # Cosmos DB 클라이언트 초기화
        self.client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
        
        # 데이터베이스와 컨테이너 생성/확인
        self._ensure_database_and_container()
        
        # 암호화 키 설정
        self.encryption_key = settings.db_connection_encryption_key or os.getenv("DB_CONNECTION_ENCRYPTION_KEY")
        if not self.encryption_key:
            # 개발용 키 생성 (실제로는 안전한 키 관리 필요)
            self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
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
                    # 서버리스 계정에서는 offer_throughput 제거
                )
            except Exception as e:
                print(f"컨테이너 생성 오류: {e}")
                self.container = self.database.get_container_client(self.container_name)
                
        except Exception as e:
            print(f"Cosmos DB 초기화 오류: {e}")
            raise
    
    def _encrypt_password(self, password: str) -> str:
        """비밀번호 암호화 (개발 환경에서는 비활성화)"""
        # 개발 환경에서는 암호화 비활성화
        return password
        # encrypted = self.cipher.encrypt(password.encode())
        # return base64.b64encode(encrypted).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """비밀번호 복호화 (개발 환경에서는 비활성화)"""
        # 개발 환경에서는 암호화 비활성화
        return encrypted_password
        # encrypted = base64.b64decode(encrypted_password.encode())
        # return self.cipher.decrypt(encrypted).decode()
    
    def create_connection(self, connection: DbConnection, tenant_id: str = "default_tenant") -> DbConnection:
        """DB 연결 생성"""
        # 비밀번호 암호화
        encrypted_password = self._encrypt_password(connection.password)
        
        # Cosmos DB 문서 생성 (멀티테넌트 구조)
        document = {
            "id": connection.id,
            "type": "db_connection",
            "tenant_id": tenant_id,  # 테넌트 ID로 고객사 구분
            "name": connection.name,
            "db_type": connection.db_type,
            "host": connection.host,
            "port": connection.port,
            "database": connection.database,
            "username": connection.username,
            "password": encrypted_password,
            "status": connection.status,
            "created_at": connection.created_at.isoformat(),
            "updated_at": connection.updated_at.isoformat() if connection.updated_at else None,
            "last_tested_at": connection.last_tested_at.isoformat() if connection.last_tested_at else None,
        }
        
        # Cosmos DB에 저장
        self.container.create_item(document)
        
        # 비밀번호를 제거한 객체 반환
        connection.password = "***"  # 보안을 위해 마스킹
        return connection
    
    def get_connection(self, connection_id: str, tenant_id: str = "default_tenant") -> Optional[DbConnection]:
        """DB 연결 조회"""
        try:
            document = self.container.read_item(
                item=connection_id,
                partition_key=tenant_id  # 멀티테넌트를 위해 tenant_id를 파티션 키로 사용
            )
            
            # 테넌트 ID 검증
            if document.get("tenant_id") != tenant_id:
                return None
            
            # DbConnection 객체로 변환
            connection = DbConnection(
                id=document["id"],
                name=document["name"],
                db_type=document["db_type"],
                host=document["host"],
                port=document["port"],
                database=document["database"],
                username=document["username"],
                password=self._decrypt_password(document["password"]),  # 복호화
                status=document["status"],
                created_at=datetime.fromisoformat(document["created_at"]),
                updated_at=datetime.fromisoformat(document["updated_at"]) if document.get("updated_at") else None,
                last_tested_at=datetime.fromisoformat(document["last_tested_at"]) if document.get("last_tested_at") else None,
            )
            
            return connection
            
        except CosmosResourceNotFoundError:
            return None
    
    def list_connections(self, tenant_id: str = "default_tenant") -> List[DbConnection]:
        """테넌트의 모든 DB 연결 조회"""
        query = "SELECT * FROM c WHERE c.type = 'db_connection' AND c.tenant_id = @tenant_id"
        parameters = [{"name": "@tenant_id", "value": tenant_id}]
        
        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False  # 같은 파티션(tenant_id) 내에서만 쿼리
        ))
        
        connections = []
        for item in items:
            connection = DbConnection(
                id=item["id"],
                name=item["name"],
                db_type=item["db_type"],
                host=item["host"],
                port=item["port"],
                database=item["database"],
                username=item["username"],
                password=self._decrypt_password(item["password"]),  # 복호화
                status=item["status"],
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else None,
                last_tested_at=datetime.fromisoformat(item["last_tested_at"]) if item.get("last_tested_at") else None,
            )
            connections.append(connection)
        
        return connections
    
    def update_connection(self, connection: DbConnection, tenant_id: str = "default_tenant") -> Optional[DbConnection]:
        """DB 연결 수정"""
        try:
            # 기존 문서 조회
            existing = self.container.read_item(
                item=connection.id,
                partition_key=tenant_id  # 멀티테넌트를 위해 tenant_id를 파티션 키로 사용
            )
            
            # 테넌트 ID 검증
            if existing.get("tenant_id") != tenant_id:
                return None
            
            # 비밀번호 암호화 (변경된 경우만)
            if connection.password != "***":
                encrypted_password = self._encrypt_password(connection.password)
            else:
                encrypted_password = existing["password"]  # 기존 암호화된 비밀번호 유지
            
            # 문서 업데이트
            existing.update({
                "name": connection.name,
                "host": connection.host,
                "port": connection.port,
                "database": connection.database,
                "username": connection.username,
                "password": encrypted_password,
                "status": connection.status,
                "updated_at": datetime.utcnow().isoformat(),
                "last_tested_at": connection.last_tested_at.isoformat() if connection.last_tested_at else None,
            })
            
            self.container.replace_item(
                item=existing["id"],
                body=existing
            )
            
            # 비밀번호를 제거한 객체 반환
            connection.password = "***"
            return connection
            
        except CosmosResourceNotFoundError:
            return None
    
    def delete_connection(self, connection_id: str, tenant_id: str = "default_tenant") -> bool:
        """DB 연결 삭제"""
        try:
            # 먼저 테넌트 ID 검증
            connection = self.get_connection(connection_id, tenant_id)
            if not connection:
                return False
                
            self.container.delete_item(
                item=connection_id,
                partition_key=tenant_id  # 멀티테넌트를 위해 tenant_id를 파티션 키로 사용
            )
            return True
        except CosmosResourceNotFoundError:
            return False
    
    def test_connection(self, connection_id: str, tenant_id: str = "default_tenant") -> dict:
        """DB 연결 테스트"""
        connection = self.get_connection(connection_id, tenant_id)
        if not connection:
            return {"success": False, "error": "연결을 찾을 수 없습니다"}
        
        try:
            import psycopg2
            import time
            
            start_time = time.time()
            
            # PostgreSQL 연결 테스트
            conn = psycopg2.connect(
                host=connection.host,
                port=connection.port,
                database=connection.database,
                user=connection.username,
                password=connection.password,
                connect_timeout=10
            )
            
            # 간단한 쿼리 실행
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            conn.close()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # 연결 상태 업데이트
            connection.status = "active"
            connection.last_tested_at = datetime.utcnow()
            self.update_connection(connection, tenant_id)
            
            return {
                "success": True,
                "message": "연결 성공",
                "latency_ms": latency_ms,
                "tested_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # 연결 상태 업데이트
            connection.status = "error"
            connection.last_tested_at = datetime.utcnow()
            self.update_connection(connection, tenant_id)
            
            return {
                "success": False,
                "message": f"연결 실패: {str(e)}",
                "tested_at": datetime.utcnow().isoformat()
            }


# 싱글톤 인스턴스
_repository_instance: Optional[DbConnectionRepository] = None

def get_db_connection_repository() -> DbConnectionRepository:
    """DB 연결 리포지토리 인스턴스 반환"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = DbConnectionRepository()
    return _repository_instance

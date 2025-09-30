"""
모니터링 데이터 저장소 (Azure Cosmos DB)
"""
from typing import List, Optional
from datetime import datetime, UTC
import uuid
import os
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.core.exceptions import ResourceModifiedError
from azure.core import MatchConditions
from dotenv import load_dotenv

from ..models.monitoring import (
    MonitoringMetric,
    QueryHistory,
    Anomaly,
    DBConnection,
    MetricStatus,
    QueryResultType,
)


class CosmosDBRepository:
    """Cosmos DB 기반 모니터링 저장소"""
    
    def __init__(self):
        load_dotenv()
        
        # Cosmos DB 클라이언트 초기화
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE", "db-monitoring")
        
        # 필수 환경변수 검증
        if not endpoint or not key:
            missing = [k for k, v in {"COSMOS_ENDPOINT": endpoint, "COSMOS_KEY": key}.items() if not v]
            raise RuntimeError(
                f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing)}\n"
                "README의 환경변수 설정 단계를 먼저 수행하거나 배포 환경변수를 확인하세요."
            )
        
        self.client = CosmosClient(endpoint, key)
        self.database = self.client.get_database_client(database_name)
        
        # 컨테이너 (테이블과 유사)
        self.metrics_container = self.database.get_container_client("metrics")
        self.histories_container = self.database.get_container_client("histories")
        self.anomalies_container = self.database.get_container_client("anomalies")
        self.connections_container = self.database.get_container_client("connections")
    
    # ===== MonitoringMetric CRUD =====
    
    def create_metric(self, metric: MonitoringMetric) -> MonitoringMetric:
        """지표 생성"""
        metric.id = str(uuid.uuid4())
        metric.created_at = datetime.now(UTC)
        metric.updated_at = datetime.now(UTC)
        
        item = metric.model_dump()
        
        # ISO 형식 변환
        item['created_at'] = metric.created_at.isoformat()
        item['updated_at'] = metric.updated_at.isoformat()
        if metric.sql_generated_at:  # ← 추가
            item['sql_generated_at'] = metric.sql_generated_at.isoformat()
        
        self.metrics_container.create_item(body=item)
        return metric
    
    def get_metric(self, metric_id: str) -> Optional[MonitoringMetric]:
        """지표 조회"""
        try:
            item = self.metrics_container.read_item(
                item=metric_id,
                partition_key=metric_id
            )
            return self._item_to_metric(item)
        except CosmosResourceNotFoundError:
            return None
    
    def list_metrics(
        self,
        status: Optional[MetricStatus] = None,
        tenant_id: Optional[str] = None
    ) -> List[MonitoringMetric]:
        """지표 목록"""
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        parameters = []
        
        if status:
            query = "SELECT * FROM c WHERE c.status = @status ORDER BY c.created_at DESC"
            parameters = [{"name": "@status", "value": status.value}]
        
        if tenant_id:
            if parameters:
                query = query.replace("WHERE", "WHERE c.tenant_id = @tenant_id AND")
                parameters.append({"name": "@tenant_id", "value": tenant_id})
            else:
                query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id ORDER BY c.created_at DESC"
                parameters = [{"name": "@tenant_id", "value": tenant_id}]
        
        items = list(self.metrics_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return [self._item_to_metric(item) for item in items]

    def get_history(self, history_id: str) -> Optional[QueryHistory]:
        """히스토리 조회"""
        try:
            # history는 metric_id로 파티션되어 있으므로
            # 파티션 키를 모르면 cross-partition 쿼리 필요
            query = "SELECT * FROM c WHERE c.id = @history_id"
            parameters = [{"name": "@history_id", "value": history_id}]
            
            items = list(self.histories_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                return self._item_to_history(items[0])
            return None
        except CosmosResourceNotFoundError:
            return None
    
    def update_metric(self, metric_id: str, metric: MonitoringMetric) -> Optional[MonitoringMetric]:
        """지표 수정"""
        try:
            # 기존 아이템 조회 (ETag 포함)
            existing_item = self.metrics_container.read_item(
                item=metric_id,
                partition_key=metric_id
            )
        except CosmosResourceNotFoundError:
            return None
        
        existing = self._item_to_metric(existing_item)
        
        metric.id = metric_id
        metric.created_at = existing.created_at
        metric.updated_at = datetime.now(UTC)
        
        # None 값 제외하고 모델 덤프
        item = metric.model_dump(exclude_none=True)
        item['created_at'] = metric.created_at.isoformat()
        item['updated_at'] = metric.updated_at.isoformat()
        if metric.sql_generated_at:
            item['sql_generated_at'] = metric.sql_generated_at.isoformat()
        
        # ETag를 사용한 동시성 제어와 파티션 키 전달
        try:
            self.metrics_container.replace_item(
                item=metric_id,
                body=item,
                etag=existing_item.get('_etag'),
                match_condition=MatchConditions.IfNotModified
            )
            return metric
        except ResourceModifiedError:
            # 동시성 충돌 발생 시 None 반환
            return None
    
    def delete_metric(self, metric_id: str) -> bool:
        """지표 삭제"""
        try:
            self.metrics_container.delete_item(
                item=metric_id,
                partition_key=metric_id
            )
            return True
        except CosmosResourceNotFoundError:
            return False
    
    # ===== QueryHistory CRUD =====
    
    def create_history(self, history: QueryHistory) -> QueryHistory:
        """히스토리 생성"""
        history.id = str(uuid.uuid4())
        history.executed_at = datetime.now(UTC)
        
        item = history.model_dump()
        item['executed_at'] = history.executed_at.isoformat()
        
        self.histories_container.create_item(body=item)
        return history
    
    def list_histories(
        self,
        metric_id: Optional[str] = None,
        limit: int = 100
    ) -> List[QueryHistory]:
        """히스토리 목록"""
        if metric_id:
            query = f"SELECT TOP {limit} * FROM c WHERE c.metric_id = @metric_id ORDER BY c.executed_at DESC"
            parameters = [{"name": "@metric_id", "value": metric_id}]
        else:
            query = f"SELECT TOP {limit} * FROM c ORDER BY c.executed_at DESC"
            parameters = []
        
        items = list(self.histories_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return [self._item_to_history(item) for item in items]
    
    def get_latest_history(self, metric_id: str) -> Optional[QueryHistory]:
        """최신 히스토리 조회"""
        histories = self.list_histories(metric_id=metric_id, limit=1)
        return histories[0] if histories else None
    
    # ===== Anomaly CRUD =====
    
    def create_anomaly(self, anomaly: Anomaly) -> Anomaly:
        """이상 내역 생성"""
        anomaly.id = str(uuid.uuid4())
        anomaly.detected_at = datetime.now(UTC)
        
        item = anomaly.model_dump()
        item['detected_at'] = anomaly.detected_at.isoformat()
        if anomaly.resolved_at:
            item['resolved_at'] = anomaly.resolved_at.isoformat()
        
        self.anomalies_container.create_item(body=item)
        return anomaly
    
    def list_anomalies(
        self,
        metric_id: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
        tenant_id: Optional[str] = None
    ) -> List[Anomaly]:
        """이상 내역 목록"""
        conditions = []
        parameters = []
        
        if metric_id:
            conditions.append("c.metric_id = @metric_id")
            parameters.append({"name": "@metric_id", "value": metric_id})
        
        if resolved is not None:
            conditions.append("c.resolved = @resolved")
            parameters.append({"name": "@resolved", "value": resolved})
        
        if tenant_id:
            conditions.append("c.tenant_id = @tenant_id")
            parameters.append({"name": "@tenant_id", "value": tenant_id})
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT TOP {limit} * FROM c {where_clause} ORDER BY c.detected_at DESC"
        
        items = list(self.anomalies_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return [self._item_to_anomaly(item) for item in items]
    
    def count_anomalies(
        self,
        metric_id: Optional[str] = None,
        resolved: Optional[bool] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        """이상 내역 개수 조회 (효율적인 COUNT 쿼리)"""
        conditions = []
        parameters = []
        
        if metric_id:
            conditions.append("c.metric_id = @metric_id")
            parameters.append({"name": "@metric_id", "value": metric_id})
        
        if resolved is not None:
            conditions.append("c.resolved = @resolved")
            parameters.append({"name": "@resolved", "value": resolved})
        
        if tenant_id:
            conditions.append("c.tenant_id = @tenant_id")
            parameters.append({"name": "@tenant_id", "value": tenant_id})
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT VALUE COUNT(1) FROM c {where_clause}"
        
        items = list(self.anomalies_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return items[0] if items else 0
    
    # ===== DBConnection CRUD =====
    
    def create_connection(self, connection: DBConnection) -> DBConnection:
        """DB 연결 생성"""
        connection.id = str(uuid.uuid4())
        connection.created_at = datetime.now(UTC)
        
        item = connection.model_dump()
        item['created_at'] = connection.created_at.isoformat()
        if connection.last_tested_at:
            item['last_tested_at'] = connection.last_tested_at.isoformat()
        
        self.connections_container.create_item(body=item)
        return connection
    
    def get_connection(self, connection_id: str) -> Optional[DBConnection]:
        """DB 연결 조회"""
        try:
            item = self.connections_container.read_item(
                item=connection_id,
                partition_key=connection_id
            )
            return self._item_to_connection(item)
        except CosmosResourceNotFoundError:
            return None
    
    def list_connections(self) -> List[DBConnection]:
        """DB 연결 목록"""
        items = list(self.connections_container.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True
        ))
        return [self._item_to_connection(item) for item in items]
    
    # ===== 변환 헬퍼 메서드 =====
    
    def _item_to_metric(self, item: dict) -> MonitoringMetric:
        """Cosmos DB item → MonitoringMetric"""
        item['created_at'] = datetime.fromisoformat(item['created_at']).astimezone(UTC)
        item['updated_at'] = datetime.fromisoformat(item['updated_at']).astimezone(UTC)
        
        # 새 필드 호환성 처리
        if 'sql_generated_at' in item and item['sql_generated_at']:
            item['sql_generated_at'] = datetime.fromisoformat(item['sql_generated_at']).astimezone(UTC)
        if 'use_cached_sql' not in item:
            item['use_cached_sql'] = True
            
        return MonitoringMetric(**item)
    
    def _item_to_history(self, item: dict) -> QueryHistory:
        """Cosmos DB item → QueryHistory"""
        item['executed_at'] = datetime.fromisoformat(item['executed_at']).astimezone(UTC)
        
        # result_type이 없는 기존 데이터 호환성
        if 'result_type' not in item:
            item['result_type'] = QueryResultType.SINGLE_VALUE
        
        return QueryHistory(**item)
    
    def _item_to_anomaly(self, item: dict) -> Anomaly:
        """Cosmos DB item → Anomaly"""
        item['detected_at'] = datetime.fromisoformat(item['detected_at']).astimezone(UTC)
        if item.get('resolved_at'):
            item['resolved_at'] = datetime.fromisoformat(item['resolved_at']).astimezone(UTC)
        return Anomaly(**item)
    
    def _item_to_connection(self, item: dict) -> DBConnection:
        """Cosmos DB item → DBConnection"""
        item['created_at'] = datetime.fromisoformat(item['created_at']).astimezone(UTC)
        if item.get('last_tested_at'):
            item['last_tested_at'] = datetime.fromisoformat(item['last_tested_at']).astimezone(UTC)
        return DBConnection(**item)


# 싱글톤 인스턴스
_repository = None


def get_repository() -> CosmosDBRepository:
    """Repository 인스턴스 가져오기"""
    global _repository
    if _repository is None:
        _repository = CosmosDBRepository()
    return _repository
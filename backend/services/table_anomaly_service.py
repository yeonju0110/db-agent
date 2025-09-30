import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path
import psycopg2

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.repositories.db_connection_repository import get_db_connection_repository
from backend.repositories.anomaly_repository import get_anomaly_repository


class TableAnomalyService:
    def __init__(self):
        self.db_repository = get_db_connection_repository()
        self.anomaly_repository = get_anomaly_repository()

    async def get_anomalies(
        self, 
        table_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        tenant_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """테이블 이상치 목록 조회"""
        try:
            # 이상치 리포지토리에서 데이터 조회
            return self.anomaly_repository.get_anomalies(
                table_name=table_name,
                status=status,
                limit=limit,
                tenant_id=tenant_id
            )
            
        except Exception as e:
            print(f"Error getting anomalies: {e}")
            return []

    async def scan_table_anomalies(self, table_name: str, tenant_id: str = "default") -> Dict[str, Any]:
        """테이블 이상치 수동 검사"""
        try:
            # 이상치 검사 실행
            detector = TableAnomalyDetector()
            result = await detector.detect_anomalies(table_name)
            
            # 이상치 리포지토리에 저장
            saved_result = self.anomaly_repository.save_anomaly_detection(result, tenant_id)
            
            return saved_result
                
        except Exception as e:
            print(f"Error scanning table anomalies: {e}")
            # 오류 시 기본 데이터 반환
            return {
                "id": str(uuid.uuid4()),
                "table_name": table_name,
                "detected_at": datetime.utcnow().isoformat(),
                "total_records": 0,
                "duplicate_count": 0,
                "null_count": 0,
                "anomaly_count": 0,
                "status": "normal",
                "is_acknowledged": False,
                "type": "table_anomaly_detection",
                "tenant_id": tenant_id
            }

    async def get_anomaly_details(self, detection_id: str, tenant_id: str = "default") -> List[Dict[str, Any]]:
        """이상치 상세 정보 조회"""
        try:
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detail' AND c.anomaly_detection_id = @detection_id"
            parameters = [{"name": "@detection_id", "value": detection_id}]
            
            items = self.db_repository.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )
            
            return list(items)
        except Exception as e:
            print(f"Error getting anomaly details: {e}")
            return []

    async def acknowledge_anomaly(self, detection_id: str, tenant_id: str = "default") -> Dict[str, Any]:
        """이상치 확인 처리"""
        try:
            # 이상치 검사 결과 업데이트
            query = "SELECT * FROM c WHERE c.id = @detection_id AND c.type = 'table_anomaly_detection'"
            parameters = [{"name": "@detection_id", "value": detection_id}]
            
            items = list(self.db_repository.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                raise ValueError(f"Anomaly detection with id {detection_id} not found")
            
            item = items[0]
            item["is_acknowledged"] = True
            item["updated_at"] = datetime.utcnow().isoformat()
            
            # Cosmos DB에서 업데이트
            self.db_repository.container.replace_item(item["id"], item)
            
            return item
        except Exception as e:
            print(f"Error acknowledging anomaly: {e}")
            raise

    async def get_anomaly_summary(self, tenant_id: str = "default") -> Dict[str, Any]:
        """이상치 요약 정보"""
        try:
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detection'"
            items = list(self.db_repository.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            total_detections = len(items)
            total_anomalies = sum(item.get("anomaly_count", 0) for item in items)
            
            # 상태별 통계
            status_breakdown = {}
            table_breakdown = []
            
            for item in items:
                status = item.get("status", "normal")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                table_breakdown.append({
                    "table_name": item.get("table_name", "unknown"),
                    "detection_count": 1,
                    "anomaly_count": item.get("anomaly_count", 0)
                })
            
            return {
                "total_detections": total_detections,
                "total_anomalies": total_anomalies,
                "status_breakdown": status_breakdown,
                "table_breakdown": table_breakdown
            }
        except Exception as e:
            print(f"Error getting anomaly summary: {e}")
            return {
                "total_detections": 0,
                "total_anomalies": 0,
                "status_breakdown": {},
                "table_breakdown": []
            }

    async def _create_sample_data(self, tenant_id: str = "default"):
        """샘플 이상치 데이터 생성"""
        try:
            sample_tables = [
                {
                    "table_name": "users",
                    "total_records": 15420,
                    "duplicate_count": 0,
                    "null_count": 2,
                    "anomaly_count": 3,
                    "status": "normal"
                },
                {
                    "table_name": "orders", 
                    "total_records": 8934,
                    "duplicate_count": 3,
                    "null_count": 12,
                    "anomaly_count": 29,
                    "status": "warning"
                },
                {
                    "table_name": "products",
                    "total_records": 2341,
                    "duplicate_count": 0,
                    "null_count": 45,
                    "anomaly_count": 55,
                    "status": "error"
                },
                {
                    "table_name": "logs",
                    "total_records": 50000,
                    "duplicate_count": 0,
                    "null_count": 0,
                    "anomaly_count": 0,
                    "status": "normal"
                }
            ]
            
            for table_data in sample_tables:
                # 기존 데이터가 있는지 확인
                query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detection' AND c.table_name = @table_name"
                parameters = [{"name": "@table_name", "value": table_data["table_name"]}]
                
                existing_items = list(self.db_repository.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                # 기존 데이터가 없으면 생성
                if not existing_items:
                    sample_item = {
                        "id": str(uuid.uuid4()),
                        "type": "table_anomaly_detection",
                        "tenant_id": tenant_id,
                        "table_name": table_data["table_name"],
                        "detected_at": datetime.utcnow().isoformat(),
                        "total_records": table_data["total_records"],
                        "duplicate_count": table_data["duplicate_count"],
                        "null_count": table_data["null_count"],
                        "anomaly_count": table_data["anomaly_count"],
                        "status": table_data["status"],
                        "is_acknowledged": False,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    self.db_repository.container.create_item(sample_item)
                    print(f"Created sample data for table: {table_data['table_name']}")
                    
        except Exception as e:
            print(f"Error creating sample data: {e}")

    async def delete_anomaly_detection(self, detection_id: str, tenant_id: str = "default") -> bool:
        """특정 이상치 검사 결과 삭제"""
        try:
            # Cosmos DB에서 삭제
            self.db_repository.container.delete_item(item=detection_id, partition_key=tenant_id)
            return True
        except Exception as e:
            print(f"Error deleting anomaly detection {detection_id}: {e}")
            return False

    async def delete_table_anomalies(self, table_name: str, tenant_id: str = "default") -> int:
        """특정 테이블의 모든 이상치 검사 결과 삭제"""
        try:
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detection' AND c.table_name = @table_name"
            parameters = [{"name": "@table_name", "value": table_name}]
            
            items = list(self.db_repository.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            deleted_count = 0
            for item in items:
                try:
                    self.db_repository.container.delete_item(item=item["id"], partition_key=tenant_id)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting item {item['id']}: {e}")
            
            return deleted_count
        except Exception as e:
            print(f"Error deleting table anomalies for {table_name}: {e}")
            return 0


class TableAnomalyDetector:
    """테이블 이상치 탐지기"""
    
    def __init__(self):
        self.db_repository = get_db_connection_repository()

    async def detect_anomalies(self, table_name: str) -> Dict[str, Any]:
        """테이블 이상치 종합 검사"""
        try:
            # DB 연결 정보 가져오기 (첫 번째 연결 사용)
            connections = list(self.db_repository.container.query_items(
                query="SELECT * FROM c WHERE c.type = 'db_connection'",
                enable_cross_partition_query=True
            ))
            
            if not connections:
                # DB 연결이 없으면 기본값 반환
                return self._get_default_detection(table_name)
            
            connection = connections[0]
            print(f"[DEBUG] Connecting to database: {connection['database']} on {connection['host']}:{connection['port']}")
            
            # PostgreSQL 연결
            conn = psycopg2.connect(
                host=connection['host'],
                port=connection['port'],
                database=connection['database'],
                user=connection['username'],
                password=connection['password'],
                connect_timeout=10
            )
            
            try:
                # 실제 테이블 정보 조회
                total_records = await self._get_total_records(conn, table_name)
                null_count = await self._detect_null_values(conn, table_name)
                duplicate_count = await self._detect_duplicates(conn, table_name)
                
                # 전체 이상치 수 계산
                total_anomalies = null_count + duplicate_count
                
                # 상태 결정
                status = self._determine_status(total_anomalies, total_records)
                
                # 결과 생성
                detection = {
                    "table_name": table_name,
                    "detected_at": datetime.utcnow().isoformat(),
                    "total_records": total_records,
                    "duplicate_count": duplicate_count,
                    "null_count": null_count,
                    "anomaly_count": total_anomalies,
                    "status": status,
                    "is_acknowledged": False
                }
                
                return detection
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error detecting anomalies for table {table_name}: {e}")
            return self._get_default_detection(table_name)

    def _get_default_detection(self, table_name: str) -> Dict[str, Any]:
        """기본 검사 결과 반환"""
        return {
            "table_name": table_name,
            "detected_at": datetime.utcnow().isoformat(),
            "total_records": 0,
            "duplicate_count": 0,
            "null_count": 0,
            "anomaly_count": 0,
            "status": "normal",
            "is_acknowledged": False
        }

    async def _get_total_records(self, conn, table_name: str) -> int:
        """총 레코드 수 조회"""
        try:
            with conn.cursor() as cursor:
                # 스키마명이 포함된 테이블명 사용 (예: public.orders)
                query = f"SELECT COUNT(*) FROM public.{table_name}"
                print(f"[DEBUG] Executing query: {query}")
                cursor.execute(query)
                result = cursor.fetchone()
                count = result[0] if result else 0
                print(f"[DEBUG] Table {table_name} has {count} records")
                return count
        except Exception as e:
            print(f"Error getting total records for {table_name}: {e}")
            return 0

    async def _detect_null_values(self, conn, table_name: str) -> int:
        """NULL 값 검사"""
        try:
            with conn.cursor() as cursor:
                # 테이블의 컬럼 정보 조회
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table_name,))
                columns = cursor.fetchall()
                
                if not columns:
                    return 0
                
                # NOT NULL 컬럼들에 대해 NULL 값 검사
                null_count = 0
                for column_name, data_type, is_nullable in columns:
                    if is_nullable == 'NO':  # NOT NULL 컬럼
                        cursor.execute(f"SELECT COUNT(*) FROM public.{table_name} WHERE {column_name} IS NULL")
                        result = cursor.fetchone()
                        if result:
                            null_count += result[0]
                
                return null_count
        except Exception as e:
            print(f"Error detecting null values for {table_name}: {e}")
            return 0

    async def _detect_duplicates(self, conn, table_name: str) -> int:
        """중복 데이터 검사"""
        try:
            with conn.cursor() as cursor:
                # Primary Key 컬럼들 조회
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = %s 
                    AND tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                """, (table_name,))
                pk_columns = [row[0] for row in cursor.fetchall()]
                
                if not pk_columns:
                    return 0
                
                # Primary Key 기준으로 중복 검사
                pk_columns_str = ', '.join(pk_columns)
                cursor.execute(f"""
                    SELECT COUNT(*) - COUNT(DISTINCT {pk_columns_str}) 
                    FROM public.{table_name}
                """)
                result = cursor.fetchone()
                return max(0, result[0]) if result else 0
                
        except Exception as e:
            print(f"Error detecting duplicates for {table_name}: {e}")
            return 0

    def _determine_status(self, anomaly_count: int, total_records: int) -> str:
        """전체 상태 결정"""
        if total_records == 0:
            return "normal"
        
        anomaly_rate = anomaly_count / total_records
        
        if anomaly_rate >= 0.1:  # 10% 이상
            return "error"
        elif anomaly_rate >= 0.05:  # 5% 이상
            return "warning"
        else:
            return "normal"

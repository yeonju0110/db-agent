import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.repositories.db_connection_repository import get_db_connection_repository
from backend.repositories.anomaly_repository import get_anomaly_repository
from backend.config.settings import get_settings

settings = get_settings()


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
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detail' AND c.anomaly_detection_id = @detection_id AND c.tenant_id = @tenant_id"
            parameters = [
                {"name": "@detection_id", "value": detection_id},
                {"name": "@tenant_id", "value": tenant_id}
            ]
            
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
            query = "SELECT * FROM c WHERE c.id = @detection_id AND c.type = 'table_anomaly_detection' AND c.tenant_id = @tenant_id"
            parameters = [
                {"name": "@detection_id", "value": detection_id},
                {"name": "@tenant_id", "value": tenant_id}
            ]
            
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
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detection' AND c.tenant_id = @tenant_id"
            parameters = [{"name": "@tenant_id", "value": tenant_id}]
            
            items = list(self.db_repository.container.query_items(
                query=query,
                parameters=parameters,
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
            query = "SELECT * FROM c WHERE c.type = 'table_anomaly_detection' AND c.table_name = @table_name AND c.tenant_id = @tenant_id"
            parameters = [
                {"name": "@table_name", "value": table_name},
                {"name": "@tenant_id", "value": tenant_id}
            ]
            
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
                distribution_anomalies = await self._detect_distribution_anomalies(conn, table_name)
                
                # 전체 이상치 수 계산
                total_anomalies = null_count + duplicate_count + distribution_anomalies
                
                # 상태 결정
                status = self._determine_status(total_anomalies, total_records)
                
                # 상세 이상치 정보 수집
                anomaly_details = await self._collect_anomaly_details(conn, table_name, total_records)
                
                # 결과 생성
                detection = {
                    "table_name": table_name,
                    "detected_at": datetime.utcnow().isoformat(),
                    "total_records": total_records,
                    "duplicate_count": duplicate_count,
                    "null_count": null_count,
                    "distribution_anomaly_count": distribution_anomalies,
                    "anomaly_count": total_anomalies,
                    "status": status,
                    "is_acknowledged": False,
                    "anomaly_details": anomaly_details  # 상세 정보 추가
                }
                
                return detection
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error detecting anomalies for table {table_name}: {e}")
            # 에러 정보를 포함한 기본값 반환
            default_detection = self._get_default_detection(table_name)
            default_detection["error"] = str(e)
            default_detection["status"] = "error"
            return default_detection

    def _get_default_detection(self, table_name: str) -> Dict[str, Any]:
        """기본 검사 결과 반환"""
        return {
            "table_name": table_name,
            "detected_at": datetime.utcnow().isoformat(),
            "total_records": 0,
            "duplicate_count": 0,
            "null_count": 0,
            "distribution_anomaly_count": 0,
            "anomaly_count": 0,
            "status": "normal",
            "is_acknowledged": False,
            "anomaly_details": []  # 빈 배열로 초기화
        }

    async def _get_total_records(self, conn, table_name: str) -> int:
        """총 레코드 수 조회"""
        try:
            with conn.cursor() as cursor:
                # SQL 인젝션 방지를 위해 psycopg2.sql 사용
                query = sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier("public"), sql.Identifier(table_name)
                )
                cursor.execute(query)
                result = cursor.fetchone()
                count = result[0] if result else 0
                return count
        except Exception as e:
            print(f"Error getting total records for {table_name}: {e}")
            return 0

    async def _detect_null_values(self, conn, table_name: str) -> int:
        """상대적 NULL 분포 이상치 감지 (15개 중 1개만 NULL이어도 감지)"""
        try:
            with conn.cursor() as cursor:
                # 총 레코드 수 조회
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier("public"), sql.Identifier(table_name)
                ))
                total_records = cursor.fetchone()[0]
                
                if total_records == 0:
                    return 0
                
                # 테이블의 컬럼 정보 조회
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table_name,))
                columns = cursor.fetchall()
                
                if not columns:
                    return 0
                
                null_anomaly_count = 0
                
                # 모든 컬럼에 대해 상대적 NULL 분포 검사
                for column_name, data_type, is_nullable in columns:
                    try:
                        # 각 컬럼의 NULL 개수 조회
                        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.{} WHERE {} IS NULL").format(
                            sql.Identifier("public"),
                            sql.Identifier(table_name),
                            sql.Identifier(column_name)
                        ))
                        null_count = cursor.fetchone()[0]
                        
                        if null_count > 0:
                            null_percentage = (null_count / total_records) * 100
                            
                            # 1. NOT NULL 컬럼에 NULL 값 존재 (심각)
                            if is_nullable == 'NO':
                                null_anomaly_count += null_count
                                print(f"  🚨 NOT NULL 컬럼에 NULL: {column_name} ({null_count}개, {null_percentage:.1f}%)")
                            
                            # 2. 상대적 소수 NULL (5% 미만) - 20개 중 1개 미만
                            elif null_percentage < 5.0 and null_count >= 1:
                                null_anomaly_count += 1  # 이상치 카테고리로 카운트
                                print(f"  ⚠ 소수 NULL 감지: {column_name} ({null_count}개, {null_percentage:.1f}%)")
                            
                            # 3. 극소 NULL (1% 미만) - 100개 중 1개 미만
                            elif null_percentage < 1.0 and null_count >= 1:
                                null_anomaly_count += 1
                                print(f"  🚨 극소 NULL 감지: {column_name} ({null_count}개, {null_percentage:.1f}%)")
                            
                            # 4. 다수 NULL (20% 이상) - 데이터 품질 문제
                            elif null_percentage >= 20.0:
                                null_anomaly_count += 1
                                print(f"  📊 다수 NULL 감지: {column_name} ({null_count}개, {null_percentage:.1f}%)")
                    
                    except Exception as e:
                        print(f"Error checking NULL in {column_name}: {e}")
                        continue
                
                return null_anomaly_count
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
                cols = sql.SQL(", ").join(sql.Identifier(c) for c in pk_columns)
                q = sql.SQL("SELECT COUNT(*) - COUNT(DISTINCT ({})) FROM {}.{}").format(
                    cols, sql.Identifier("public"), sql.Identifier(table_name)
                )
                cursor.execute(q)
                result = cursor.fetchone()
                return max(0, result[0]) if result else 0
                
        except Exception as e:
            print(f"Error detecting duplicates for {table_name}: {e}")
            return 0

    async def _detect_distribution_anomalies(self, conn, table_name: str) -> int:
        """카테고리형 데이터 분포 이상치 감지 (20개 중 1개도 감지)"""
        try:
            with conn.cursor() as cursor:
                # 카테고리형 컬럼 찾기
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    AND data_type IN ('character varying', 'text', 'USER-DEFINED')
                """, (table_name,))
                
                columns = cursor.fetchall()
                total_anomalies = 0
                
                for column_name, data_type in columns:
                    try:
                        # 각 값의 분포 조회
                        query = sql.SQL("""
                            SELECT 
                                CAST({} AS TEXT) as value,
                                COUNT(*) as count,
                                COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM {}), 0) as percentage
                            FROM {} 
                            GROUP BY CAST({} AS TEXT)
                            ORDER BY count DESC
                        """).format(
                            sql.Identifier(column_name),
                            sql.Identifier(table_name),
                            sql.Identifier(table_name),
                            sql.Identifier(column_name)
                        )
                        
                        cursor.execute(query)
                        results = cursor.fetchall()
                        
                        if not results:
                            continue
                        
                        total_records = sum(row[1] for row in results)
                        
                        # 분포 이상치 감지 (중복 카운팅 방지)
                        anomaly_categories = 0
                        for value, count, percentage in results:
                            # NULL 값 제외
                            if value is None:
                                continue
                            
                            # 1. 극소 카테고리 (1% 미만) - 100개 중 1개
                            if percentage < 1.0 and count >= 1:
                                anomaly_categories += 1
                                print(f"  🚨 극소 카테고리 감지: {column_name}='{value}' ({count}개, {percentage:.2f}%)")
                            
                            # 2. 소수 카테고리 (5% 미만) - 20개 중 1개
                            elif percentage < 5.0 and count >= 1:
                                anomaly_categories += 1
                                print(f"  ⚠ 소수 카테고리 감지: {column_name}='{value}' ({count}개, {percentage:.2f}%)")
                        
                        # 이상치 카테고리 수만 카운트 (실제 레코드 수가 아닌)
                        total_anomalies += anomaly_categories
                        
                        # 3. 분포 불균형 (한 값이 90% 이상)
                        if len(results) > 1 and results[0][2] >= 90.0:
                            dominant_value, dominant_count, dominant_pct = results[0]
                            print(f"  📊 분포 불균형 감지: {column_name}에서 '{dominant_value}'가 {dominant_pct:.2f}%")
                            # 불균형 자체는 이상치로 카운트하지 않음 (데이터 특성일 수 있음)
                    
                    except Exception as e:
                        print(f"Error analyzing distribution for {column_name}: {e}")
                        continue
                
                return total_anomalies
                
        except Exception as e:
            print(f"Error detecting distribution anomalies for {table_name}: {e}")
            return 0

    async def _collect_anomaly_details(self, conn, table_name: str, total_records: int) -> List[Dict[str, Any]]:
        """상세 이상치 정보 수집"""
        details = []
        print(f"  🔍 상세 정보 수집 시작: {table_name} (총 {total_records}개 레코드)")
        
        try:
            with conn.cursor() as cursor:
                # 1. NULL 값 상세 정보
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table_name,))
                columns = cursor.fetchall()
                
                for column_name, data_type, is_nullable in columns:
                    try:
                        # NULL 개수 조회
                        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.{} WHERE {} IS NULL").format(
                            sql.Identifier("public"),
                            sql.Identifier(table_name),
                            sql.Identifier(column_name)
                        ))
                        null_count = cursor.fetchone()[0]
                        
                        if null_count > 0:
                            null_percentage = (null_count / total_records) * 100
                            
                            # NULL 값 샘플 데이터 조회 (최대 5개)
                            cursor.execute(sql.SQL("""
                                SELECT * FROM {}.{} 
                                WHERE {} IS NULL 
                                LIMIT 5
                            """).format(
                                sql.Identifier("public"),
                                sql.Identifier(table_name),
                                sql.Identifier(column_name)
                            ))
                            sample_data = cursor.fetchall()
                            
                            # 컬럼명 매핑
                            column_names = [desc[0] for desc in cursor.description]
                            sample_records = [dict(zip(column_names, row)) for row in sample_data]
                            
                            details.append({
                                "type": "null_values",
                                "column": column_name,
                                "data_type": data_type,
                                "is_nullable": is_nullable == 'NO',
                                "count": null_count,
                                "percentage": round(null_percentage, 2),
                                "severity": self._get_null_severity(null_percentage, is_nullable == 'NO'),
                                "description": self._get_null_description(null_percentage, is_nullable == 'NO'),
                                "sample_data": sample_records
                            })
                    except Exception as e:
                        print(f"Error collecting NULL details for {column_name}: {e}")
                        continue
                
                # 2. 중복 데이터 상세 정보
                cursor.execute(sql.SQL("""
                    SELECT *, COUNT(*) as duplicate_count
                    FROM {}.{}
                    GROUP BY *
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                    LIMIT 5
                """).format(
                    sql.Identifier("public"),
                    sql.Identifier(table_name)
                ))
                duplicate_data = cursor.fetchall()
                
                if duplicate_data:
                    column_names = [desc[0] for desc in cursor.description]
                    for row in duplicate_data:
                        record = dict(zip(column_names, row))
                        duplicate_count = record.pop('duplicate_count', 0)
                        
                        details.append({
                            "type": "duplicates",
                            "count": duplicate_count,
                            "severity": "medium" if duplicate_count <= 3 else "high",
                            "description": f"동일한 레코드가 {duplicate_count}번 중복됨",
                            "sample_data": [record]
                        })
                
                # 3. 분포 이상치 상세 정보
                for column_name, data_type, is_nullable in columns:
                    if data_type in ['character varying', 'text', 'character']:
                        try:
                            cursor.execute(sql.SQL("""
                                SELECT {}, COUNT(*) as count
                                FROM {}.{}
                                WHERE {} IS NOT NULL
                                GROUP BY {}
                                ORDER BY count ASC
                                LIMIT 10
                            """).format(
                                sql.Identifier(column_name),
                                sql.Identifier("public"),
                                sql.Identifier(table_name),
                                sql.Identifier(column_name),
                                sql.Identifier(column_name)
                            ))
                            distribution_data = cursor.fetchall()
                            
                            for value, count in distribution_data:
                                percentage = (count / total_records) * 100
                                
                                if percentage < 5.0 and count >= 1:  # 소수 카테고리
                                    details.append({
                                        "type": "distribution_anomaly",
                                        "column": column_name,
                                        "value": value,
                                        "count": count,
                                        "percentage": round(percentage, 2),
                                        "severity": "high" if percentage < 1.0 else "medium",
                                        "description": f"'{value}' 값이 {count}개({percentage:.1f}%)로 소수 카테고리"
                                    })
                        except Exception as e:
                            print(f"Error collecting distribution details for {column_name}: {e}")
                            continue
                            
        except Exception as e:
            print(f"Error collecting anomaly details: {e}")
        
        print(f"  ✅ 상세 정보 수집 완료: {len(details)}개 항목")
        return details

    def _get_null_severity(self, percentage: float, is_not_null: bool) -> str:
        """NULL 값 심각도 결정"""
        if is_not_null:
            return "high"  # NOT NULL 컬럼에 NULL
        elif percentage < 1.0:
            return "high"  # 극소 NULL
        elif percentage < 5.0:
            return "medium"  # 소수 NULL
        else:
            return "low"  # 다수 NULL

    def _get_null_description(self, percentage: float, is_not_null: bool) -> str:
        """NULL 값 설명 생성"""
        if is_not_null:
            return f"NOT NULL 컬럼에 NULL 값 존재 ({percentage:.1f}%)"
        elif percentage < 1.0:
            return f"극소 NULL 감지 ({percentage:.1f}%)"
        elif percentage < 5.0:
            return f"소수 NULL 감지 ({percentage:.1f}%)"
        else:
            return f"다수 NULL 감지 ({percentage:.1f}%)"

    def _determine_status(self, anomaly_count: int, total_records: int) -> str:
        """전체 상태 결정 - 상대적 비율 기반"""
        if total_records == 0:
            return "normal"
        
        anomaly_rate = anomaly_count / total_records
        
        # 고도화된 상대적 비율 기준
        if anomaly_rate >= 0.1:  # 10% 이상
            return "error"
        elif anomaly_rate >= 0.05:  # 5% 이상 (20개 중 1개)
            return "warning"
        elif anomaly_rate >= 0.01:  # 1% 이상 (100개 중 1개)
            return "info"
        else:
            return "normal"

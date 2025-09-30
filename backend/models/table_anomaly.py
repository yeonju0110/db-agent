from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TableAnomalyDetection(Base):
    """테이블 이상치 감지 결과"""
    __tablename__ = "table_anomaly_detections"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    table_name = Column(String, nullable=False, index=True)
    detected_at = Column(DateTime, default=func.now(), nullable=False)
    total_records = Column(Integer, nullable=False, default=0)
    duplicate_count = Column(Integer, nullable=False, default=0)
    null_count = Column(Integer, nullable=False, default=0)
    anomaly_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="normal")  # normal, warning, error
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_tad_table_name", "table_name"),
        Index("ix_tad_detected_at", "detected_at"),
        Index("ix_tad_status", "status"),
    )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "table_name": self.table_name,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "total_records": self.total_records,
            "duplicate_count": self.duplicate_count,
            "null_count": self.null_count,
            "anomaly_count": self.anomaly_count,
            "status": self.status,
            "is_acknowledged": self.is_acknowledged,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TableAnomalyDetail(Base):
    """테이블 이상치 상세 정보"""
    __tablename__ = "table_anomaly_details"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    anomaly_detection_id = Column(
        String,
        ForeignKey("table_anomaly_detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anomaly_type = Column(String, nullable=False)  # null_values, duplicates, data_quality, business_logic
    severity = Column(String, nullable=False, default="low")  # low, medium, high
    count = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    affected_columns = Column(JSON, nullable=True)  # List of column names
    sample_data = Column(JSON, nullable=True)  # Sample problematic records
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "anomaly_detection_id": self.anomaly_detection_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "count": self.count,
            "description": self.description,
            "affected_columns": self.affected_columns or [],
            "sample_data": self.sample_data or {},
            "is_acknowledged": self.is_acknowledged,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

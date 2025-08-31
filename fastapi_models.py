"""
Enhanced Database Models for LivePrecisionCalculator Ultimate Edition
Comprehensive data layer with audit trails, metrics, and multi-currency support
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.sqlite import DECIMAL
from pydantic import BaseModel, Field, validator
import json
import uuid

Base = declarative_base()

class CalculationStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success" 
    ERROR = "error"
    HEALING = "healing"

class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HealingAction(str, Enum):
    DETECTION = "detection"
    MITIGATION = "mitigation"
    PROCESSING = "processing"
    CORRECTION = "correction"
    MANAGEMENT = "management"
    SUPPORT = "support"
    HEALING = "healing"

# Database Models

class CalculationRecord(Base):
    """Audit trail for all calculations with quantum-level precision"""
    __tablename__ = "calculations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    calculation_id = Column(String(100), unique=True, nullable=False, index=True)
    operation = Column(String(50), nullable=False)
    operand1 = Column(Text, nullable=False)  # Store as string to preserve precision
    operand2 = Column(Text, nullable=True)
    result = Column(Text, nullable=True)  # Store as string to preserve precision
    result_decimal = Column(Float, nullable=True)  # For numeric operations
    currency_from = Column(String(10), nullable=True)
    currency_to = Column(String(10), nullable=True)
    exchange_rate = Column(Text, nullable=True)  # High precision exchange rate
    precision_used = Column(Integer, default=60)
    status = Column(String(20), default=CalculationStatus.PENDING)
    execution_time_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(100), nullable=True)  # For future user tracking
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    healing_applied = Column(Boolean, default=False)
    healing_steps = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    quality_score = Column(Float, default=1.0)
    confidence_level = Column(Float, default=1.0)
    
    # Relationships
    healing_records = relationship("HealingRecord", back_populates="calculation")

class SystemMetrics(Base):
    """Real-time system performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    calculations_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, default=100.0)
    avg_response_time_ms = Column(Float, default=0.0)
    calculations_per_second = Column(Float, default=0.0)
    active_websocket_connections = Column(Integer, default=0)
    memory_usage_mb = Column(Float, default=0.0)
    cpu_usage_percent = Column(Float, default=0.0)
    redis_status = Column(String(20), default="unknown")
    database_status = Column(String(20), default="unknown")
    healing_suite_status = Column(String(20), default="active")
    uptime_seconds = Column(Float, default=0.0)

class CurrencyRate(Base):
    """Exchange rate cache with historical tracking"""
    __tablename__ = "currency_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_currency = Column(String(10), nullable=False, index=True)
    to_currency = Column(String(10), nullable=False, index=True)
    rate = Column(Text, nullable=False)  # High precision rate as string
    rate_decimal = Column(Float, nullable=False)  # For quick numeric operations
    source = Column(String(50), nullable=False)  # API source
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    is_current = Column(Boolean, default=True, index=True)
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_currency_pair_current', 'from_currency', 'to_currency', 'is_current'),
    )

class HealingRecord(Base):
    """The Healing Suite™ - Error detection, mitigation, and recovery tracking"""
    __tablename__ = "healing_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    healing_id = Column(String(100), unique=True, nullable=False, index=True)
    calculation_id = Column(String(100), nullable=True, index=True)
    action_type = Column(String(20), nullable=False)  # HealingAction enum
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    severity = Column(String(20), default=ErrorSeverity.MEDIUM)
    detection_method = Column(String(50), nullable=True)
    mitigation_steps = Column(JSON, nullable=True)
    correction_applied = Column(Text, nullable=True)
    auto_fix_successful = Column(Boolean, default=False)
    learning_data = Column(JSON, nullable=True)
    prevention_pattern = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)
    resolution_time_ms = Column(Float, nullable=True)
    
    # Relationships
    calculation = relationship("CalculationRecord", back_populates="healing_records")

class AuditLog(Base):
    """Comprehensive audit trail for all system activities"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(200), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, nullable=True)

class UserSession(Base):
    """Track user sessions and activity"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    calculations_count = Column(Integer, default=0)
    websocket_connections = Column(Integer, default=0)

# Pydantic Models for API

class CalculationRequest(BaseModel):
    """Request model for calculations"""
    operation: str = Field(..., description="Mathematical operation to perform")
    operand1: str = Field(..., description="First operand (high precision string)")
    operand2: Optional[str] = Field(None, description="Second operand (if required)")
    currency_from: Optional[str] = Field("USD", description="Source currency")
    currency_to: Optional[str] = Field("USD", description="Target currency")
    precision_override: Optional[int] = Field(None, ge=1, le=100, description="Override default precision")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_operations = [
            'add', 'subtract', 'multiply', 'divide', 'power', 'sqrt', 
            'abs', 'negate', '+', '-', '*', '/', '**', '^'
        ]
        if v.lower() not in valid_operations:
            raise ValueError(f'Operation must be one of: {valid_operations}')
        return v.lower()

class CalculationResponse(BaseModel):
    """Response model for calculations"""
    success: bool
    calculation_id: str
    result: Optional[str] = None
    result_decimal: Optional[float] = None
    operation: str
    operand1: str
    operand2: Optional[str] = None
    currency_from: Optional[str] = None
    currency_to: Optional[str] = None
    exchange_rate: Optional[str] = None
    precision_used: int
    execution_time_ms: float
    timestamp: datetime
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    healing_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    quality_score: float = 1.0
    confidence_level: float = 1.0

class MetricsResponse(BaseModel):
    """System metrics response"""
    calculations_performed: int
    errors_encountered: int
    success_rate: float
    uptime_seconds: float
    calculations_per_second: float
    avg_response_time_ms: float
    precision_level: int
    active_connections: int
    memory_usage_mb: float
    cpu_usage_percent: float
    status: str
    healing_suite_active: bool
    redis_status: str
    database_status: str
    timestamp: datetime

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    components: Dict[str, str]
    metrics: Optional[Dict[str, Any]] = None

class CurrencyRateResponse(BaseModel):
    """Currency exchange rate response"""
    from_currency: str
    to_currency: str
    rate: str
    rate_decimal: float
    source: str
    timestamp: datetime
    is_current: bool

class HealingStatusResponse(BaseModel):
    """The Healing Suite™ status response"""
    healing_suite_active: bool
    total_healing_actions: int
    errors_detected: int
    mitigations_applied: int
    corrections_made: int
    auto_fixes_successful: int
    learning_patterns_created: int
    average_resolution_time_ms: float
    success_rate: float
    last_healing_action: Optional[datetime] = None

class AuditLogResponse(BaseModel):
    """Audit log response"""
    event_id: str
    event_type: str
    action: str
    resource: Optional[str] = None
    success: bool
    timestamp: datetime
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    error_message: Optional[str] = None

# Database utility functions

def create_database_engine(database_url: str = "sqlite:///live_precision_calculator.db"):
    """Create database engine with optimized settings"""
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=30
        )
    return engine

def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

def get_session_maker(engine):
    """Get SQLAlchemy session maker"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Example usage and initialization
if __name__ == "__main__":
    # Create database and tables
    engine = create_database_engine()
    create_tables(engine)
    print("Database tables created successfully!")
    
    # Create session for testing
    SessionLocal = get_session_maker(engine)
    session = SessionLocal()
    
    # Test calculation record
    calc_record = CalculationRecord(
        calculation_id=str(uuid.uuid4()),
        operation="add",
        operand1="123.456789012345678901234567890",
        operand2="987.654321098765432109876543210",
        result="1111.111110111111111011111111100",
        precision_used=60,
        status=CalculationStatus.SUCCESS,
        execution_time_ms=15.5
    )
    
    session.add(calc_record)
    session.commit()
    session.close()
    
    print("Test calculation record created successfully!")
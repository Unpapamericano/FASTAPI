# app/models/client.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    databases = relationship("DatabaseInstance", back_populates="client")
    incidents = relationship("Incident", back_populates="client")

# app/models/database_instance.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class DatabaseType(str, enum.Enum):
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"

class Environment(str, enum.Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class HAConfig(str, enum.Enum):
    STANDALONE = "standalone"
    RAC = "rac"  # Oracle RAC
    DATA_GUARD = "data_guard"  # Oracle Data Guard
    ALWAYS_ON = "always_on"  # SQL Server Always On
    FAILOVER_CLUSTER = "failover_cluster"  # Windows Failover Cluster

class DatabaseInstance(Base):
    __tablename__ = "database_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    db_type = Column(Enum(DatabaseType), nullable=False)
    version = Column(String(50), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    service_name = Column(String(255))  # Oracle service name or SQL Server database name
    environment = Column(Enum(Environment), nullable=False)
    ha_config = Column(Enum(HAConfig), default=HAConfig.STANDALONE)
    backup_retention_days = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    last_backup = Column(DateTime(timezone=True))
    last_health_check = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="databases")
    backups = relationship("Backup", back_populates="database")
    monitoring_records = relationship("MonitoringRecord", back_populates="database")
    incidents = relationship("Incident", back_populates="database")

# app/models/backup.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class BackupType(str, enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    LOG = "log"

class BackupStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Backup(Base):
    __tablename__ = "backups"
    
    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("database_instances.id"), nullable=False)
    backup_type = Column(Enum(BackupType), nullable=False)
    status = Column(Enum(BackupStatus), default=BackupStatus.SCHEDULED)
    backup_path = Column(String(500))
    backup_size_bytes = Column(BigInteger)
    compression_ratio = Column(String(10))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    error_message = Column(Text)
    rman_output = Column(Text)  # For Oracle RMAN output
    is_restorable = Column(Boolean, default=True)
    retention_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    database = relationship("DatabaseInstance", back_populates="backups")

# app/models/incident.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IncidentCategory(str, enum.Enum):
    PERFORMANCE = "performance"
    CONNECTIVITY = "connectivity"
    BACKUP_FAILURE = "backup_failure"
    SPACE_ISSUE = "space_issue"
    SECURITY = "security"
    CORRUPTION = "corruption"
    HARDWARE = "hardware"
    OTHER = "other"

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    database_id = Column(Integer, ForeignKey("database_instances.id"))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(IncidentCategory), nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN)
    assigned_to = Column(String(255))
    resolution = Column(Text)
    reported_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    client = relationship("Client", back_populates="incidents")
    database = relationship("DatabaseInstance", back_populates="incidents")

# app/models/monitoring.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class MonitoringRecord(Base):
    __tablename__ = "monitoring_records"
    
    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("database_instances.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Performance Metrics
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)
    active_connections = Column(Integer)
    response_time_ms = Column(Float)
    
    # Oracle specific
    sga_usage_percent = Column(Float)
    pga_usage_percent = Column(Float)
    tablespace_usage_percent = Column(Float)
    redo_log_switches_per_hour = Column(Integer)
    
    # SQL Server specific
    buffer_cache_hit_ratio = Column(Float)
    page_life_expectancy = Column(Integer)
    deadlocks_per_second = Column(Float)
    batch_requests_per_second = Column(Float)
    
    # General health indicators
    is_available = Column(Boolean, default=True)
    alert_message = Column(Text)
    
    # Relationships
    database = relationship("DatabaseInstance", back_populates="monitoring_records")

# app/models/maintenance.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class MaintenanceType(str, enum.Enum):
    PATCH = "patch"
    UPDATE = "update"
    UPGRADE = "upgrade"
    REINDEX = "reindex"
    STATISTICS_UPDATE = "statistics_update"
    CONFIGURATION_CHANGE = "configuration_change"

class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"
    
    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("database_instances.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    maintenance_type = Column(Enum(MaintenanceType), nullable=False)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    performed_by = Column(String(255))
    requires_downtime = Column(Boolean, default=False)
    backup_before_maintenance = Column(Boolean, default=True)
    rollback_plan = Column(Text)
    execution_log = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    database = relationship("DatabaseInstance")

# app/models/__init__.py
from .client import Client
from .database_instance import DatabaseInstance, DatabaseType, Environment, HAConfig
from .backup import Backup, BackupType, BackupStatus
from .incident import Incident, IncidentSeverity, IncidentStatus, IncidentCategory
from .monitoring import MonitoringRecord
from .maintenance import MaintenanceWindow, MaintenanceType, MaintenanceStatus
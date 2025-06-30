# app/crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

# app/crud/client.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate

class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Client]:
        return db.query(Client).filter(Client.name == name).first()
    
    def get_by_industry(self, db: Session, *, industry: str) -> List[Client]:
        return db.query(Client).filter(Client.industry == industry).all()
    
    def get_active(self, db: Session) -> List[Client]:
        return db.query(Client).filter(Client.is_active == True).all()

client_crud = CRUDClient(Client)

# app/crud/database.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.database_instance import DatabaseInstance
from app.schemas.database import DatabaseInstanceCreate, DatabaseInstanceUpdate

class CRUDDatabaseInstance(CRUDBase[DatabaseInstance, DatabaseInstanceCreate, DatabaseInstanceUpdate]):
    def get_by_client(self, db: Session, *, client_id: int) -> List[DatabaseInstance]:
        return db.query(DatabaseInstance).filter(DatabaseInstance.client_id == client_id).all()
    
    def get_by_type(self, db: Session, *, db_type: str) -> List[DatabaseInstance]:
        return db.query(DatabaseInstance).filter(DatabaseInstance.db_type == db_type).all()
    
    def get_by_environment(self, db: Session, *, environment: str) -> List[DatabaseInstance]:
        return db.query(DatabaseInstance).filter(DatabaseInstance.environment == environment).all()
    
    def get_active(self, db: Session) -> List[DatabaseInstance]:
        return db.query(DatabaseInstance).filter(DatabaseInstance.is_active == True).all()

database_crud = CRUDDatabaseInstance(DatabaseInstance)

# app/api/clients.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.client import Client, ClientCreate, ClientUpdate
from app.crud.client import client_crud

router = APIRouter()

@router.get("/", response_model=List[Client])
def get_clients(
    skip: int = 0, 
    limit: int = 100, 
    industry: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get list of clients with optional filtering"""
    if industry:
        clients = client_crud.get_by_industry(db, industry=industry)
    elif active_only:
        clients = client_crud.get_active(db)
    else:
        clients = client_crud.get_multi(db, skip=skip, limit=limit)
    return clients

@router.post("/", response_model=Client)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Create new client"""
    # Check if client with same name already exists
    existing_client = client_crud.get_by_name(db, name=client.name)
    if existing_client:
        raise HTTPException(status_code=400, detail="Client with this name already exists")
    return client_crud.create(db=db, obj_in=client)

@router.get("/{client_id}", response_model=Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Get client by ID"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=Client)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    """Update client"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_crud.update(db, db_obj=client, obj_in=client_update)

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Delete client"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_crud.remove(db, id=client_id)

@router.get("/{client_id}/databases")
def get_client_databases(client_id: int, db: Session = Depends(get_db)):
    """Get all databases for a specific client"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    from app.crud.database import database_crud
    return database_crud.get_by_client(db, client_id=client_id)

# app/api/databases.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.schemas.database import DatabaseInstance, DatabaseInstanceCreate, DatabaseInstanceUpdate, DatabaseStatus
from app.crud.database import database_crud
from app.utils.oracle_manager import OracleManager
from app.utils.sqlserver_manager import SQLServerManager

router = APIRouter()

@router.get("/", response_model=List[DatabaseInstance])
def get_databases(
    skip: int = 0,
    limit: int = 100,
    db_type: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of databases with optional filtering"""
    if client_id:
        databases = database_crud.get_by_client(db, client_id=client_id)
    elif db_type:
        databases = database_crud.get_by_type(db, db_type=db_type)
    elif environment:
        databases = database_crud.get_by_environment(db, environment=environment)
    else:
        databases = database_crud.get_multi(db, skip=skip, limit=limit)
    return databases

@router.post("/", response_model=DatabaseInstance)
def create_database(database: DatabaseInstanceCreate, db: Session = Depends(get_db)):
    """Register new database"""
    return database_crud.create(db=db, obj_in=database)

@router.get("/{database_id}", response_model=DatabaseInstance)
def get_database(database_id: int, db: Session = Depends(get_db)):
    """Get database by ID"""
    database = database_crud.get(db, id=database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    return database

@router.put("/{database_id}", response_model=DatabaseInstance)
def update_database(database_id: int, database_update: DatabaseInstanceUpdate, db: Session = Depends(get_db)):
    """Update database"""
    database = database_crud.get(db, id=database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    return database_crud.update(db, db_obj=database, obj_in=database_update)

@router.delete("/{database_id}")
def delete_database(database_id: int, db: Session = Depends(get_db)):
    """Delete database"""
    database = database_crud.get(db, id=database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    return database_crud.remove(db, id=database_id)

@router.get("/{database_id}/status", response_model=DatabaseStatus)
def get_database_status(database_id: int, db: Session = Depends(get_db)):
    """Get current database status and performance metrics"""
    database = database_crud.get(db, id=database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    
    # Get database manager based on type
    if database.db_type == "oracle":
        manager = OracleManager(database)
    else:
        manager = SQLServerManager(database)
    
    try:
        status = manager.get_status()
        return DatabaseStatus(
            database_id=database_id,
            is_available=status['is_available'],
            response_time_ms=status['response_time_ms'],
            cpu_usage_percent=status['cpu_usage_percent'],
            memory_usage_percent=status['memory_usage_percent'],
            active_connections=status['active_connections'],
            last_check=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database status: {str(e)}")

@router.post("/{database_id}/backup")
def start_backup(database_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Start backup for database"""
    database = database_crud.get(db, id=database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    
    # Add backup task to background tasks
    background_tasks.add_task(perform_backup, database_id, db)
    
    return {"message": f"Backup started for database {database.name}", "database_id": database_id}

@router.get("/{database_id}/performance")
def get_performance_metrics(database_id: int, hours: int = Query(24), db: Session = Depends(get_db)):
    """Get performance metrics for the last N hours"""
    database = database_crud.get(db, id=database_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    
    # Get monitoring records for the specified time period
    from app.models.monitoring import MonitoringRecord
    from datetime import datetime, timedelta
    
    start_time = datetime.now() - timedelta(hours=hours)
    metrics = db.query(MonitoringRecord).filter(
        MonitoringRecord.database_id == database_id,
        MonitoringRecord.timestamp >= start_time
    ).order_by(MonitoringRecord.timestamp.desc()).all()
    
    return {"database_id": database_id, "metrics": metrics, "period_hours": hours}

def perform_backup(database_id: int, db: Session):
    """Background task to perform database backup"""
    database = database_crud.get(db, id=database_id)
    if not database:
        return
    
    if database.db_type == "oracle":
        manager = OracleManager(database)
    else:
        manager = SQLServerManager(database)
    
    try:
        backup_result = manager.perform_backup()
        # Save backup record to database
        from app.models.backup import Backup, BackupType, BackupStatus
        backup_record = Backup(
            database_id=database_id,
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED if backup_result['success'] else BackupStatus.FAILED,
            backup_path=backup_result.get('backup_path'),
            backup_size_bytes=backup_result.get('size_bytes'),
            start_time=backup_result.get('start_time'),
            end_time=backup_result.get('end_time'),
            error_message=backup_result.get('error_message')
        )
        db.add(backup_record)
        db.commit()
    except Exception as e:
        print(f"Backup failed for database {database_id}: {str(e)}")

# app/utils/oracle_manager.py
import cx_Oracle
import subprocess
import os
from datetime import datetime
from typing import Dict, Any

class OracleManager:
    def __init__(self, database_instance):
        self.database = database_instance
        self.connection_string = f"{database_instance.host}:{database_instance.port}/{database_instance.service_name}"
    
    def get_connection(self):
        """Get Oracle database connection"""
        try:
            # In a real environment, you would use proper credentials
            connection = cx_Oracle.connect(
                user="system",  # This should come from secure config
                password="password",  # This should come from secure config
                dsn=self.connection_string
            )
            return connection
        except Exception as e:
            raise Exception(f"Failed to connect to Oracle database: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current database status and performance metrics"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Check if database is available
            start_time = datetime.now()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Get performance metrics
            cursor.execute("""
                SELECT 
                    (SELECT value FROM v$sysstat WHERE name = 'CPU used by this session') as cpu_usage,
                    (SELECT round((1-(pr.value/(bg.value+pr.value)))*100,2) 
                     FROM v$sysstat pr, v$sysstat bg 
                     WHERE pr.name='physical reads' AND bg.name='db block gets') as buffer_cache_hit_ratio,
                    (SELECT count(*) FROM v$session WHERE status = 'ACTIVE') as active_sessions
                FROM dual
            """)
            
            metrics = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return {
                'is_available': True,
                'response_time_ms': response_time,
                'cpu_usage_percent': float(metrics[0]) if metrics[0] else 0,
                'memory_usage_percent': float(metrics[1]) if metrics[1] else 0,
                'active_connections': int(metrics[2]) if metrics[2] else 0
            }
        except Exception as e:
            return {
                'is_available': False,
                'response_time_ms': 0,
                'cpu_usage_percent': 0,
                'memory_usage_percent': 0,
                'active_connections': 0,
                'error': str(e)
            }
    
    def perform_backup(self) -> Dict[str, Any]:
        """Perform RMAN backup"""
        try:
            rman_script = f"""
                CONNECT TARGET /
                RUN {{
                    ALLOCATE CHANNEL ch1 TYPE DISK;
                    BACKUP DATABASE PLUS ARCHIVELOG;
                    BACKUP CURRENT CONTROLFILE;
                    RELEASE CHANNEL ch1;
                }}
            """
            
            # Execute RMAN backup
            rman_path = os.getenv('ORACLE_RMAN_PATH', '/opt/oracle/product/19c/dbhome_1/bin/rman')
            start_time = datetime.now()
            
            process = subprocess.run(
                [rman_path, 'target', '/'],
                input=rman_script,
                text=True,
                capture_output=True,
                timeout=3600  # 1 hour timeout
            )
            
            end_time = datetime.now()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'start_time': start_time,
                    'end_time': end_time,
                    'rman_output': process.stdout,
                    'backup_path': '/backup/oracle/'  # This would be dynamic
                }
            else:
                return {
                    'success': False,
                    'start_time': start_time,
                    'end_time': end_time,
                    'error_message': process.stderr,
                    'rman_output': process.stdout
                }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'start_time': datetime.now(),
                'end_time': datetime.now()
            }

# app/utils/sqlserver_manager.py
import pyodbc
import subprocess
from datetime import datetime
from typing import Dict, Any

class SQLServerManager:
    def __init__(self, database_instance):
        self.database = database_instance
        self.connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={database_instance.host},{database_instance.port};DATABASE={database_instance.service_name};Trusted_Connection=yes;"
    
    def get_connection(self):
        """Get SQL Server database connection"""
        try:
            connection = pyodbc.connect(self.connection_string)
            return connection
        except Exception as e:
            raise Exception(f"Failed to connect to SQL Server database: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current database status and performance metrics"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Check if database is available
            start_time = datetime.now()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Get performance metrics
            cursor.execute("""
                SELECT 
                    (SELECT cntr_value FROM sys.dm_os_performance_counters 
                     WHERE counter_name = 'Processor Time %' AND instance_name = '_Total') as cpu_usage,
                    (SELECT cntr_value FROM sys.dm_os_performance_counters 
                     WHERE counter_name = 'Buffer cache hit ratio') as buffer_cache_hit_ratio,
                    (SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE is_user_process = 1) as active_sessions
            """)
            
            metrics = cursor.fetchone()
            
            cursor.close()
            connection.close()
        except Exception as e:
            # Handle or log the exception as needed
            return {
                'is_available': False,
                'response_time_ms': 0,
                'cpu_usage_percent': 0,
                'memory_usage_percent': 0,
                'active_connections': 0,
                'error': str(e)
            }
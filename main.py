
# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.database import engine, Base
from app.api import clients, databases, backups, incidents, monitoring

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting SVA Database Administration System...")
    yield
    # Shutdown
    print("Shutting down SVA Database Administration System...")

app = FastAPI(
    title="SVA Database Administration System",
    description="Sistema de administración de bases de datos para SVA System Vertrieb Alexander GmbH",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(databases.router, prefix="/api/v1/databases", tags=["databases"])
app.include_router(backups.router, prefix="/api/v1/backups", tags=["backups"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])

@app.get("/")
async def root():
    return {
        "message": "SVA Database Administration System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sva-db-admin"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/sva_db_admin")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# app/schemas/client.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    name: str
    industry: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class Client(ClientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# app/schemas/database.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.database_instance import DatabaseType, Environment, HAConfig

class DatabaseInstanceBase(BaseModel):
    name: str
    db_type: DatabaseType
    version: str
    host: str
    port: int
    service_name: Optional[str] = None
    environment: Environment
    ha_config: HAConfig = HAConfig.STANDALONE
    backup_retention_days: int = 30
    is_active: bool = True

class DatabaseInstanceCreate(DatabaseInstanceBase):
    client_id: int

class DatabaseInstanceUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    service_name: Optional[str] = None
    environment: Optional[Environment] = None
    ha_config: Optional[HAConfig] = None
    backup_retention_days: Optional[int] = None
    is_active: Optional[bool] = None

class DatabaseInstance(DatabaseInstanceBase):
    id: int
    client_id: int
    last_backup: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DatabaseStatus(BaseModel):
    database_id: int
    is_available: bool
    response_time_ms: float
    cpu_usage_percent: float
    memory_usage_percent: float
    active_connections: int
    last_check: datetime

# app/api/clients.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.client import Client, ClientCreate, ClientUpdate
from app.crud.client import client_crud

router = APIRouter()

@router.get("/", response_model=List[Client])
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtener lista de clientes"""
    clients = client_crud.get_multi(db, skip=skip, limit=limit)
    return clients

@router.post("/", response_model=Client)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Crear nuevo cliente"""
    return client_crud.create(db=db, obj_in=client)

@router.get("/{client_id}", response_model=Client)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Obtener cliente por ID"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client

@router.put("/{client_id}", response_model=Client)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    """Actualizar cliente"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client_crud.update(db, db_obj=client, obj_in=client_update)

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Eliminar cliente"""
    client = client_crud.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    client_crud.remove
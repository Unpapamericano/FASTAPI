# Database Administration System for SVA System Vertrieb Alexander GmbH

## Project Description

This project simulates a database administration system designed for the specific needs of the Database Administrator position at SVA System Vertrieb Alexander GmbH. The system manages over 1,000 clients from various industries with Oracle and Microsoft SQL Server databases.

## Key Features

- **Multi-Client Management**: Database administration for multiple clients
- **Dual Support**: Oracle Database (11g+) and Microsoft SQL Server (2012+)
- **Monitoring and Performance**: Integrated monitoring system
- **Backup and Recovery**: Automated backup management
- **Incident Management**: Ticketing system and problem management
- **High Availability**: High availability configurations (RAC, Always On)

## System Architecture

### Main Components

1. **Client Management System**: Client and database management
2. **Database Monitoring**: Performance and availability monitoring
3. **Backup & Recovery Manager**: Backup and recovery management
4. **Incident Tracking**: Ticket system and problem resolution
5. **Maintenance Scheduler**: Maintenance and patch scheduling

### Technologies Used

- **Backend**: Python 3.9+
- **Database**: PostgreSQL (for system metadata)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Monitoring**: Integration with Nagios/CheckMK
- **Containerization**: Docker & Docker Compose

## Project Structure

```
database-admin-system/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── database_instance.py
│   │   ├── backup.py
│   │   ├── incident.py
│   │   └── monitoring.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── database.py
│   │   ├── backup.py
│   │   └── incident.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── database.py
│   │   ├── backup.py
│   │   └── incident.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── clients.py
│   │   ├── databases.py
│   │   ├── backups.py
│   │   ├── incidents.py
│   │   └── monitoring.py
│   └── utils/
│       ├── __init__.py
│       ├── oracle_manager.py
│       ├── sqlserver_manager.py
│       └── monitoring_tools.py
├── scripts/
│   ├── backup_scheduler.py
│   ├── health_checker.py
│   └── patch_manager.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Installation and Configuration

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL 13+
- Access to Oracle Database and SQL Server (for real testing)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd database-admin-system
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your specific configurations
   ```

3. **Build and run with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Run migrations**
   ```bash
   docker-compose exec app python -m alembic upgrade head
   ```

5. **Load sample data**
   ```bash
   docker-compose exec app python scripts/load_sample_data.py
   ```

## Environment Variables Configuration

Create `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/sva_db_admin

# Oracle Configuration
ORACLE_CONNECTION_STRING=oracle://user:password@localhost:1521/xe
ORACLE_RMAN_PATH=/opt/oracle/product/19c/dbhome_1/bin/rman

# SQL Server Configuration
SQLSERVER_CONNECTION_STRING=mssql+pyodbc://user:password@localhost/master?driver=ODBC+Driver+17+for+SQL+Server

# Monitoring
NAGIOS_API_URL=http://nagios-server:5667/nagiosxi/api/v1
CHECKMK_API_URL=http://checkmk-server:5000/api/1.0

# Email Configuration
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=alerts@sva.de
SMTP_PASSWORD=your_password

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## System Usage

### API Endpoints

#### Client Management
- `GET /api/v1/clients/` - List all clients
- `POST /api/v1/clients/` - Create new client
- `GET /api/v1/clients/{client_id}` - Get client details
- `PUT /api/v1/clients/{client_id}` - Update client
- `DELETE /api/v1/clients/{client_id}` - Delete client

#### Database Management
- `GET /api/v1/databases/` - List all databases
- `POST /api/v1/databases/` - Register new database
- `GET /api/v1/databases/{db_id}/status` - Database status
- `POST /api/v1/databases/{db_id}/backup` - Start backup
- `GET /api/v1/databases/{db_id}/performance` - Performance metrics

#### Backup Management
- `GET /api/v1/backups/` - List backups
- `POST /api/v1/backups/schedule` - Schedule backup
- `GET /api/v1/backups/{backup_id}/status` - Backup status
- `POST /api/v1/backups/{backup_id}/restore` - Restore backup

#### Incident Management
- `GET /api/v1/incidents/` - List incidents
- `POST /api/v1/incidents/` - Create new incident
- `PUT /api/v1/incidents/{incident_id}/resolve` - Resolve incident
- `GET /api/v1/incidents/stats` - Incident statistics

### Usage Examples

#### Create a New Client
```bash
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Automotive Corp GmbH",
    "industry": "Automotive",
    "contact_email": "it-admin@automotive-corp.de",
    "contact_phone": "+49 69 123456789",
    "is_active": true
  }'
```

#### Register Oracle Database
```bash
curl -X POST "http://localhost:8000/api/v1/databases/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "name": "PROD_ERP_DB",
    "db_type": "oracle",
    "version": "19c",
    "host": "oracle-prod-01.automotive-corp.local",
    "port": 1521,
    "service_name": "ERPDB",
    "environment": "production",
    "ha_config": "rac",
    "backup_retention_days": 30
  }'
```

## Position-Specific Features

### 1. Oracle Administration
- Support for versions 11g+ including Multi-Tenant
- RMAN integration for backups
- Data Guard and RAC configuration
- Oracle Enterprise Manager monitoring

### 2. SQL Server Administration
- Support for versions 2012+ 
- Always On Availability Groups configuration
- Windows Failover Cluster management
- Automated backup and restore

### 3. Monitoring and Alerts
- CheckMK and Nagios integration
- Automatic email/SMS alerts
- Real-time performance dashboard
- Availability reports

### 4. Incident Management
- Integrated ticketing system
- Automatic escalation (Second/Third Level)
- SLA tracking and reporting
- Integrated knowledge base

### 5. Maintenance Scheduling
- Patch and update scheduler
- Configurable maintenance windows
- Automatic rollback on failures
- Client notifications

## Monitoring and Alerts

The system includes proactive monitoring for:

- **Performance**: CPU, memory, I/O, disk space
- **Availability**: Connectivity, active services
- **Backups**: Success/failure of scheduled backups
- **Security**: Unauthorized access attempts
- **Maintenance**: Patch and update status

## Security

- JWT authentication for API access
- Database credential encryption
- Audit trail for all operations
- Role-based access control (RBAC)
- Active Directory integration

## Testing

Run tests:

```bash
# Unit tests
docker-compose exec app python -m pytest tests/unit/

# Integration tests
docker-compose exec app python -m pytest tests/integration/

# Coverage report
docker-compose exec app python -m pytest --cov=app tests/
```

## Deployment

### Production with Docker

```bash
# Build for production
docker build -t sva-db-admin:latest .

# Deploy
docker run -d \
  --name sva-db-admin \
  -p 8000:8000 \
  --env-file .env.prod \
  sva-db-admin:latest
```

### Kubernetes Deployment

Configuration files available in `/k8s/`

```bash
kubectl apply -f k8s/
```

## Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is under the MIT License - see [LICENSE](LICENSE) file for details.

## Contact

For technical support or inquiries:
- Email: db-admin-support@sva.de
- Documentation: [Internal Wiki](http://wiki.sva.local/db-admin-system)
- Tickets: [JIRA Project](http://jira.sva.local/projects/DBADMIN)

## Roadmap

### Upcoming Features
- [ ] Ansible integration for automation
- [ ] React web dashboard
- [ ] Machine Learning for failure prediction
- [ ] Terraform integration for IaC
- [ ] Mobile app for critical alerts
- [ ] Additional GraphQL API

---

**Note**: This system is specifically designed to meet the requirements of the Database Administrator position at SVA System Vertrieb Alexander GmbH, including management of over 1,000 clients and 24/7 support with on-call system.
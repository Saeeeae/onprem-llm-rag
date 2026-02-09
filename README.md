# On-Premise LLM & RAG System

Enterprise-grade, air-gapped LLM & RAG system for biotech companies with strict security requirements. Features Department + Role based RBAC, complete audit logging, and automated document processing.

## 🏗️ Architecture

```
Next.js Frontend (3000) 
    ↓
FastAPI Backend (8000) - [RBAC Middleware] - [Audit Logging]
    ↓
    ├─→ vLLM (8001) - LLM Inference (L40S GPUs)
    ├─→ Qdrant (6333) - Vector DB with RBAC Filters
    ├─→ PostgreSQL (5432) - Users, Audit Logs, Metadata
    └─→ Redis (6379) - Cache & Task Queue
         ↓
    Celery Workers - Document Processing (OCR, Chunking, Embedding)
         ↓
    Celery Beat - Daily NAS Sync (02:00 AM)
```

## 📋 Key Features

### 1. Security & RBAC
- **Department + Role Based Access Control**: Only users with matching department AND role can access documents
- **No Security Level Grades**: Simplified to Department + Role only
- **Complete Audit Trail**: Every query, document access, and action logged to PostgreSQL
- **Air-Gapped Environment**: No external internet access required

### 2. Document Processing Pipeline
- **Supported Formats**: PDF, Word, Excel, PowerPoint, Images (TIF, PNG, JPG)
- **Automated OCR**: Tesseract OCR for image documents (Korean + English)
- **Daily NAS Sync**: Scheduled at 02:00 AM to detect new/modified files
- **Chunking & Embedding**: Sentence-Transformers for vector embeddings
- **Qdrant Storage**: Vector database with RBAC metadata filtering

### 3. High Performance
- **50 Concurrent Requests**: FastAPI async/await + vLLM continuous batching
- **GPU Scenarios**:
  - **1 GPU (TP=1)**: Development, single-user (15-20 req/s)
  - **2 GPUs (TP=2)**: Production, larger models (30-40 req/s)
  - **4 GPUs (TP=4)**: Enterprise, maximum throughput (50+ req/s)

### 4. Admin Dashboard
- System health monitoring (GPU, services)
- User activity statistics
- Document statistics by department/type
- Audit log viewer
- RAG pipeline status

## 🚀 Quick Start

### Prerequisites
- Ubuntu 24.04 LTS
- NVIDIA L40S GPU(s) with 48GB VRAM
- CUDA 13.1
- Docker & Docker Compose v2
- NAS mounted at `/mnt/nas` (or configure path)
- Pre-downloaded LLM model at `/mnt/models`

### 1. Configuration

Copy and edit environment variables:
```bash
cp .env.example .env
nano .env
```

Key variables to configure:
```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Security
JWT_SECRET_KEY=your-secret-key-min-32-chars

# Paths
NAS_MOUNT_PATH=/mnt/nas
MODEL_DIR=/mnt/models
MODEL_NAME=meta-llama/Llama-2-70b-chat-hf

# NAS Sync Schedule (Cron format)
NAS_SYNC_SCHEDULE=0 2 * * *  # Daily at 02:00 AM
```

### 2. Choose GPU Scenario

Edit `docker-compose.yml` and uncomment your scenario:

**Scenario A (1 GPU)** - Default, already active
**Scenario B (2 GPUs)** - Uncomment lines 122-161, comment out Scenario A
**Scenario C (4 GPUs)** - Uncomment lines 163-202, comment out Scenario A

### 3. Start Services

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Check service health
docker compose ps
```

### 4. Initialize Database

The PostgreSQL schema is automatically initialized on first run.

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123` (⚠️ CHANGE IN PRODUCTION!)

### 5. Access Services

- **Frontend (Chat)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery Monitor)**: http://localhost:5555 (dev profile only)

## 💻 Development Setup

### For Developers: Hot-Reload Environment

This project supports a complete development workflow with hot-reload, debugging, and real-time code changes without rebuilding containers.

#### 1. Set Up Development Environment

```bash
# Copy environment file
cp .env.example .env

# Copy development override file
cp docker-compose.override.example.yml docker-compose.override.yml

# (Optional) Customize your local override file
nano docker-compose.override.yml
```

#### 2. Start Development Services

```bash
# Build and start all services in development mode
docker compose up -d

# Watch logs (hot-reload messages will appear here)
docker compose logs -f backend frontend
```

#### 3. Development Features

**Hot-Reload Enabled:**
- ✅ **Backend**: Code changes in `backend/app/` automatically reload uvicorn
- ✅ **Frontend**: Next.js Fast Refresh for instant updates
- ✅ **Worker**: Celery tasks reload on restart
- ✅ **AI Services**: Python services reload on file changes

**Debug Ports Exposed:**
| Service | Debug Port | Purpose |
|---------|-----------|---------|
| Backend | 5678 | debugpy remote debugging |
| OCR Service | 5679 | debugpy remote debugging |
| Embedding Service | 5680 | debugpy remote debugging |
| Chunking Service | 5681 | debugpy remote debugging |

**Volume Mounts:**
- Source code is mounted from host → changes reflect immediately
- Dependencies remain in container → fast startup

#### 4. Attach Debugger (VSCode)

Add to `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend Remote Debug",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/backend/app",
          "remoteRoot": "/app/app"
        }
      ]
    }
  ]
}
```

**Usage:**
1. Set breakpoint in `backend/app/main.py`
2. Press F5 in VSCode
3. Make API request → debugger pauses at breakpoint

#### 5. Run Tests Inside Containers

```bash
# Backend tests
docker compose exec backend pytest

# Frontend tests
docker compose exec frontend npm test

# Worker tests
docker compose exec celery_worker pytest
```

#### 6. Rebuild After Dependency Changes

```bash
# Only rebuild when requirements.txt or package.json changes
docker compose build backend
docker compose up -d backend

# Or rebuild all services
docker compose build
docker compose up -d
```

#### 7. Switch to Production Mode

```bash
# Remove development override
rm docker-compose.override.yml

# Production build (default)
docker compose up -d
```

### Development vs Production

| Aspect | Development | Production |
|--------|------------|-----------|
| **Target** | `development` stage | `production` stage |
| **Hot-Reload** | ✅ Enabled | ❌ Disabled |
| **Debug Tools** | ✅ debugpy, pytest, ipdb | ❌ Not included |
| **Workers** | 1 (easier debugging) | 4 (performance) |
| **Logging** | DEBUG level | INFO level |
| **User** | root (flexibility) | non-root (security) |
| **Image Size** | Larger (+200MB) | Optimized |

## 📁 Project Structure

```
onprem_llm/
├── ARCHITECTURE.md           # Detailed architecture documentation
├── docker-compose.yml        # Multi-container orchestration
├── .env.example              # Environment variables template
│
├── backend/                  # FastAPI Backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Configuration settings
│   │   ├── database.py      # PostgreSQL connection
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── middleware/
│   │   │   ├── auth.py      # RBAC middleware
│   │   │   └── logging.py   # Audit logging
│   │   ├── services/
│   │   │   ├── qdrant_service.py   # Vector search with RBAC
│   │   │   ├── llm_service.py      # vLLM communication
│   │   │   └── rag_service.py      # RAG orchestration
│   │   └── api/endpoints/
│   │       ├── chat.py      # Chat/RAG endpoints
│   │       └── admin.py     # Admin endpoints
│   ├── Dockerfile
│   └── requirements.txt
│
├── worker/                   # Celery Workers
│   ├── celery_app.py        # Celery configuration
│   ├── tasks/
│   │   ├── nas_sync.py      # Daily NAS sync (02:00 AM)
│   │   └── document_processing.py  # OCR, chunking, embedding
│   ├── Dockerfile
│   └── requirements.txt
│
├── vllm/                     # vLLM Serving
│   ├── Dockerfile.1gpu      # 1 GPU scenario
│   ├── Dockerfile.2gpu      # 2 GPUs scenario
│   ├── Dockerfile.4gpu      # 4 GPUs scenario
│   └── entrypoint.sh        # vLLM startup script
│
├── frontend/                 # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx     # Chat interface
│   │   │   └── admin/       # Admin dashboard
│   │   └── components/
│   ├── Dockerfile
│   └── package.json
│
├── database/
│   └── init.sql             # PostgreSQL schema
│
└── config/
    ├── redis.conf           # Redis configuration (optional)
    └── qdrant.yaml          # Qdrant configuration (optional)
```

## 🔐 RBAC Example

### Document Metadata (Qdrant Payload)
```json
{
  "content": "Clinical trial protocol...",
  "filename": "trial_protocol.pdf",
  "department": "Clinical_Team",
  "role": "Manager"
}
```

### User Profile
```json
{
  "username": "john.doe",
  "department": "Clinical_Team",
  "role": "Manager"
}
```

### Search Filter Applied
```python
{
  "must": [
    {
      "should": [
        {"match": {"key": "department", "value": "Clinical_Team"}},
        {"match": {"key": "department", "value": "All"}}
      ]
    },
    {
      "should": [
        {"match": {"key": "role", "value": "Manager"}},
        {"match": {"key": "role", "value": "All"}}
      ]
    }
  ]
}
```

**Result**: User can only access documents where:
- Department = "Clinical_Team" OR "All"
- AND Role = "Manager" OR "All"

## 📊 Daily NAS Sync Workflow

**Scheduled Time**: 02:00 AM (configurable via `NAS_SYNC_SCHEDULE`)

**Process**:
1. **Scan NAS**: Walk through `/mnt/nas` recursively
2. **Detect Changes**: Calculate SHA-256 hash, compare with database
3. **Queue Processing**: Send new/modified files to Celery workers
4. **Extract Text**: 
   - PDF → PyPDF2
   - Word → python-docx
   - Excel → openpyxl
   - Images → Tesseract OCR (Korean + English)
5. **Chunk Text**: Overlapping chunks (500 words, 50 overlap)
6. **Generate Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
7. **Upsert to Qdrant**: With RBAC metadata (department, role)
8. **Log to PostgreSQL**: Track processing status

## 🛠️ Useful Commands

### Docker Compose
```bash
# Start services
docker compose up -d

# Start with dev profile (includes Flower monitoring)
docker compose --profile dev up -d

# View logs
docker compose logs -f backend
docker compose logs -f celery_worker

# Restart service
docker compose restart backend

# Stop services
docker compose down

# Stop and remove volumes (⚠️ deletes data)
docker compose down -v
```

### Database Access
```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U admin -d onprem_llm

# Run query
docker compose exec postgres psql -U admin -d onprem_llm -c "SELECT COUNT(*) FROM documents;"
```

### Celery Management
```bash
# Check worker status
docker compose exec celery_worker celery -A celery_app inspect active

# Trigger NAS sync manually
docker compose exec celery_worker celery -A celery_app call tasks.nas_sync.sync_nas_documents
```

### GPU Monitoring
```bash
# Check GPU usage
watch -n 1 nvidia-smi
```

## 📈 Performance Tuning

### FastAPI
- **Workers**: 4 (adjust based on CPU cores)
- **Event Loop**: uvloop (faster than asyncio)
- **HTTP Parser**: httptools (faster than default)

### vLLM
- **Continuous Batching**: Automatically enabled
- **GPU Memory Utilization**: 0.90 (1-2 GPUs), 0.95 (4 GPUs)
- **Max Sequences**: 256 (1 GPU), 512 (2 GPUs), 1024 (4 GPUs)

### PostgreSQL
- **Connection Pool**: 20 connections (min 10, max 50)
- **Indexes**: On user_id, department, role, created_at

### Redis
- **Max Memory**: 4GB
- **Eviction Policy**: allkeys-lru

## 🔒 Security Best Practices

1. **Change Default Passwords**:
   - PostgreSQL admin password
   - JWT secret key
   - Flower admin credentials

2. **Enable Air-Gapped Mode**:
   ```yaml
   networks:
     onprem_network:
       internal: true  # Uncomment in docker-compose.yml
   ```

3. **Use HTTPS**:
   - Set up reverse proxy (Nginx/Traefik) with TLS certificates

4. **Backup Strategy**:
   - Daily PostgreSQL dumps
   - Weekly Qdrant snapshots
   - NAS is source of truth for documents

5. **Monitor Audit Logs**:
   ```sql
   -- Recent failed queries
   SELECT * FROM audit_logs 
   WHERE success = false 
   ORDER BY created_at DESC 
   LIMIT 50;
   ```

## 🐛 Troubleshooting

### Issue: vLLM OOM (Out of Memory)
**Solution**: Reduce `GPU_MEMORY_UTILIZATION` or `MAX_MODEL_LEN`

### Issue: Slow RAG responses
**Solution**:
- Check GPU utilization (`nvidia-smi`)
- Increase vLLM `MAX_NUM_SEQS`
- Enable caching in Redis

### Issue: NAS sync not running
**Solution**:
```bash
# Check Celery Beat status
docker compose logs celery_beat

# Manually trigger sync
docker compose exec celery_worker celery -A celery_app call tasks.nas_sync.sync_nas_documents
```

### Issue: Database connection errors
**Solution**:
```bash
# Check PostgreSQL health
docker compose exec postgres pg_isready

# Restart database
docker compose restart postgres
```

### Development: Hot-reload not working
**Solution**:
```bash
# 1. Check volume mounts are correct
docker compose config | grep volumes -A 5

# 2. Verify file permissions
ls -la backend/app/

# 3. Force recreate container
docker compose up -d --force-recreate backend

# 4. Check logs for reload messages
docker compose logs backend | grep -i reload
```

### Development: Debugger won't connect
**Solution**:
```bash
# 1. Verify debug port is exposed
docker compose ps | grep backend

# 2. Check if debugpy is running
docker compose logs backend | grep debugpy

# 3. Ensure development target is used
docker compose config | grep target

# 4. Rebuild with development target
docker compose build --no-cache backend
docker compose up -d backend
```

### Development: Port conflicts
**Solution**:
```bash
# Edit docker-compose.override.yml to change ports
services:
  backend:
    ports:
      - "8001:8000"  # Change host port to 8001
      - "5679:5678"  # Change debugpy port to 5679
```

### Development: Out of disk space
**Solution**:
```bash
# Remove unused Docker images
docker system prune -a --volumes

# Remove only development images
docker images | grep development | awk '{print $3}' | xargs docker rmi

# Check disk usage
docker system df
```

## 📚 API Documentation

Interactive API docs available at: http://localhost:8000/docs

### Key Endpoints

**Authentication**:
- `POST /api/v1/auth/login` - Login and get JWT token

**Chat**:
- `POST /api/v1/chat/` - Send query, get RAG answer
- `GET /api/v1/chat/history` - Get user's chat history

**Admin** (superuser only):
- `GET /api/v1/admin/health` - System health status
- `GET /api/v1/admin/stats/users` - User activity statistics
- `GET /api/v1/admin/stats/documents` - Document statistics
- `GET /api/v1/admin/logs/audit` - Audit logs (paginated)

## 🧪 Testing

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# vLLM
curl http://localhost:8001/health

# Qdrant
curl http://localhost:6333/health
```

### Sample Query
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the clinical trial protocol for XYZ?",
    "top_k": 5,
    "temperature": 0.7
  }'
```

## 📝 License

Proprietary - Internal Use Only

## 👥 Support

For issues and questions, contact the MLOps team.

---

**Built with**: FastAPI, vLLM, Qdrant, PostgreSQL, Redis, Celery, Next.js, Docker
**Target**: Biotech Enterprise, Air-Gapped Environments
**GPU**: NVIDIA L40S (48GB VRAM)

# On-Premise LLM & RAG System Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Air-Gapped Environment                          │
│                                                                           │
│  ┌──────────────┐         ┌──────────────────────────────────────────┐  │
│  │   End Users  │────────▶│       Next.js Frontend (3000)            │  │
│  └──────────────┘         │  - Chat Interface                        │  │
│                           │  - Admin Dashboard                       │  │
│                           │  - System Monitoring                     │  │
│                           └──────────────┬───────────────────────────┘  │
│                                          │                               │
│                                          │ HTTP/REST                     │
│                                          ▼                               │
│                           ┌──────────────────────────────────────────┐  │
│                           │    FastAPI Backend (8000)                │  │
│                           │  ┌────────────────────────────────────┐  │  │
│                           │  │  Middleware Layer                  │  │  │
│                           │  │  - RBAC (Dept + Role)              │  │  │
│                           │  │  - Audit Logging                   │  │  │
│                           │  │  - Request Throttling              │  │  │
│                           │  └────────────────────────────────────┘  │  │
│                           │  ┌────────────────────────────────────┐  │  │
│                           │  │  API Endpoints                     │  │  │
│                           │  │  - /chat (async, 50 concurrent)    │  │  │
│                           │  │  - /documents                      │  │  │
│                           │  │  - /admin/*                        │  │  │
│                           │  └────────────────────────────────────┘  │  │
│                           └─────┬──────────┬─────────┬─────────────┘  │
│                                 │          │         │                 │
│              ┌──────────────────┘          │         └────────────┐    │
│              │                             │                      │    │
│              ▼                             ▼                      ▼    │
│  ┌───────────────────┐        ┌────────────────────┐  ┌──────────────┐│
│  │  vLLM Service     │        │  Qdrant Vector DB  │  │ PostgreSQL   ││
│  │  (Port: 8001)     │        │  (Port: 6333)      │  │ (Port: 5432) ││
│  │                   │        │                    │  │              ││
│  │  GPU Scenarios:   │        │  - Embeddings      │  │  - Users     ││
│  │  A: 1 GPU (TP=1)  │        │  - Metadata        │  │  - Audit Logs││
│  │  B: 2 GPU (TP=2)  │        │  - RBAC Filters    │  │  - Documents ││
│  │  C: 4 GPU (TP=4)  │        │                    │  │              ││
│  │                   │        └────────────────────┘  └──────────────┘│
│  │  - Continuous     │                                                 │
│  │    Batching       │                                                 │
│  │  - PagedAttention │                                                 │
│  └───────────────────┘                                                 │
│              ▲                                                          │
│              │                                                          │
│              │                                                          │
│  ┌───────────┴──────────────────────────────────────────────────────┐  │
│  │                    Redis + Celery Workers                         │  │
│  │                                                                    │  │
│  │  ┌──────────────┐    ┌─────────────────────────────────────┐    │  │
│  │  │   Redis      │◀───│  Celery Beat Scheduler              │    │  │
│  │  │  (Port:6379) │    │  - Daily NAS Sync (02:00 AM)        │    │  │
│  │  │              │    │  - Periodic Health Checks           │    │  │
│  │  │  - Queue     │    └─────────────────────────────────────┘    │  │
│  │  │  - Cache     │                                                │  │
│  │  └──────┬───────┘                                                │  │
│  │         │                                                         │  │
│  │         ▼                                                         │  │
│  │  ┌──────────────────────────────────────────────────────────┐   │  │
│  │  │  Celery Workers                                           │   │  │
│  │  │  - Document Processing (OCR, Chunking, Embedding)        │   │  │
│  │  │  - NAS File Sync                                          │   │  │
│  │  │  - Batch Embedding Jobs                                   │   │  │
│  │  └──────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│              ▲                                                          │
│              │                                                          │
│  ┌───────────┴──────────┐                                              │
│  │    NAS Storage       │                                              │
│  │  /mnt/nas/documents  │                                              │
│  │  - PDF, DOCX, XLSX   │                                              │
│  │  - PPT, TIF, PNG, JPG│                                              │
│  └──────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. Data Flow

### 2.1 User Query Flow (RAG)
```
User → Next.js → FastAPI → [RBAC Check] → Qdrant (Vector Search + Filter)
                                        ↓
                                   [Retrieved Docs]
                                        ↓
                               vLLM (LLM Generation)
                                        ↓
                               [Response + Citations]
                                        ↓
                            PostgreSQL (Audit Log) → User
```

### 2.2 Document Processing Flow
```
NAS Directory → Celery Beat (Scheduled) → Celery Worker
                                              ↓
                                      [File Change Detection]
                                              ↓
                                      [OCR + Text Extraction]
                                              ↓
                                      [Chunking + Embedding]
                                              ↓
                                      Qdrant (Upsert with Metadata)
                                              ↓
                                      PostgreSQL (Log Entry)
```

## 3. GPU Deployment Strategies (NVIDIA L40S 48GB)

### Scenario A: 1 GPU
```yaml
vllm_service:
  environment:
    - CUDA_VISIBLE_DEVICES=0
    - VLLM_TENSOR_PARALLEL_SIZE=1
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```
**Use Case**: Development, Testing, or Single-User scenarios.
**Model**: LLaMA-2-70B, Mixtral-8x7B (with quantization).
**Expected Throughput**: 15-20 req/s (with continuous batching).

### Scenario B: 2 GPUs
**Option 1: Tensor Parallelism (TP=2)**
```yaml
vllm_service:
  environment:
    - CUDA_VISIBLE_DEVICES=0,1
    - VLLM_TENSOR_PARALLEL_SIZE=2
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 2
            capabilities: [gpu]
```
**Use Case**: Larger models (LLaMA-2-70B, Falcon-180B with quantization).
**Latency**: Lower latency per request (model split across GPUs).

**Option 2: Replica Load Balancing**
```yaml
vllm_service_replica1:
  environment:
    - CUDA_VISIBLE_DEVICES=0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            device_ids: ['0']

vllm_service_replica2:
  environment:
    - CUDA_VISIBLE_DEVICES=1
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            device_ids: ['1']
```
**Use Case**: High throughput (50+ concurrent requests).
**Setup**: Nginx/Traefik load balancer in front.
**Throughput**: ~30-40 req/s (2x single GPU).

### Scenario C: 4 GPUs
**Option 1: Tensor Parallelism (TP=4)**
```yaml
vllm_service:
  environment:
    - CUDA_VISIBLE_DEVICES=0,1,2,3
    - VLLM_TENSOR_PARALLEL_SIZE=4
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 4
            capabilities: [gpu]
```
**Use Case**: Very large models (LLaMA-2-405B, GPT-3.5 scale).
**Latency**: Minimal per-request latency.

**Option 2: High Availability (2x TP=2)**
```yaml
vllm_service_ha1:
  environment:
    - CUDA_VISIBLE_DEVICES=0,1
    - VLLM_TENSOR_PARALLEL_SIZE=2
  deploy:
    replicas: 1

vllm_service_ha2:
  environment:
    - CUDA_VISIBLE_DEVICES=2,3
    - VLLM_TENSOR_PARALLEL_SIZE=2
  deploy:
    replicas: 1
```
**Use Case**: Production with failover capability.
**Benefits**: Zero-downtime upgrades, A/B model testing.

## 4. Security & RBAC Implementation

### 4.1 Access Control Logic
```python
# User attributes
user = {
    "id": "user123",
    "department": "Clinical_Team",
    "role": "Manager"
}

# Qdrant filter (applied to all searches)
filter = {
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

### 4.2 Document Metadata Schema
```json
{
  "id": "doc_12345",
  "vector": [0.123, 0.456, ...],
  "payload": {
    "filename": "clinical_trial_protocol.pdf",
    "department": "Clinical_Team",
    "role": "Manager",
    "created_at": "2026-02-08T10:00:00Z",
    "file_type": "pdf",
    "source_path": "/mnt/nas/documents/clinical/..."
  }
}
```

## 5. Performance Optimization

### 5.1 Concurrency Handling (50 Requests Target)
1. **FastAPI**: `uvicorn --workers 4 --loop uvloop --http httptools`
2. **vLLM Continuous Batching**: Automatically batches requests to maximize GPU utilization.
3. **Redis Queue**: Overflow requests queued and processed asynchronously.
4. **Connection Pooling**: PostgreSQL and Qdrant connection pools (min=10, max=50).

### 5.2 Caching Strategy
- **Redis**: Cache frequent queries (TTL: 1 hour).
- **Qdrant**: In-memory quantized vectors for faster search.
- **PostgreSQL**: Indexed queries on `user_id`, `timestamp`, `document_id`.

## 6. Monitoring & Observability

### 6.1 Metrics to Track
- **GPU**: Utilization (%), Memory (GB), Temperature (°C).
- **API**: Request rate (req/s), Latency (P50, P95, P99).
- **Queue**: Redis queue depth, Celery worker status.
- **Database**: Query performance, Connection pool usage.

### 6.2 Health Check Endpoints
- `GET /health`: Overall system health.
- `GET /health/gpu`: GPU availability and stats.
- `GET /health/qdrant`: Vector DB connection status.
- `GET /health/workers`: Celery worker availability.

## 7. Backup & Disaster Recovery

### 7.1 Data Persistence
- **PostgreSQL**: Daily automated backups via `pg_dump`.
- **Qdrant**: Snapshot API for vector data backup.
- **NAS**: Primary source of truth (RAID-configured).

### 7.2 Recovery Strategy
1. Restore PostgreSQL from latest backup.
2. Rebuild Qdrant index from NAS source files (Celery task).
3. Estimated recovery time: 4-8 hours (depending on data volume).

## 8. Technology Versions (Recommended)

| Component   | Version    | Notes                          |
|-------------|------------|--------------------------------|
| Python      | 3.11       | Performance improvements       |
| FastAPI     | 0.109+     | Latest async features          |
| vLLM        | 0.3.0+     | Continuous batching support    |
| Qdrant      | 1.7+       | Improved filtering             |
| PostgreSQL  | 16         | Better indexing                |
| Redis       | 7.2        | Stable, well-tested            |
| Celery      | 5.3+       | Python 3.11 compatibility      |
| Next.js     | 14+        | App Router, Server Components  |
| CUDA        | 13.1       | Compatible with L40S           |

## 9. Security Considerations (Air-Gapped)

1. **No Internet Access**: All dependencies pre-downloaded.
2. **Certificate Management**: Internal CA for HTTPS.
3. **Secret Management**: Environment variables (not hardcoded).
4. **Audit Trail**: Immutable logs in PostgreSQL (append-only).
5. **Data Encryption**: At-rest (disk encryption), In-transit (TLS).

# Microservices Architecture - Service Testing Guide

## 🏗️ 새로운 서비스 구조

각 AI 기능이 독립 컨테이너로 분리되어 개별 테스트 및 확장이 가능합니다.

```
┌─────────────────────────────────────────────────────────────┐
│  GLM-OCR Service (8001)         [GPU Required]              │
│  - Model: zai-org/GLM-OCR                                   │
│  - Function: Image OCR (TIF, PNG, JPG)                     │
│  - Languages: English, Korean, Chinese, Japanese            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Hybrid Chunking Service (8003)  [No GPU]                  │
│  - Method: Semantic + Recursive                             │
│  - Function: Intelligent text splitting                     │
│  - Features: Context-aware, paragraph boundaries            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  E5 Embedding Service (8002)     [GPU Required]            │
│  - Model: intfloat/multilingual-e5-large                   │
│  - Dimension: 1024                                          │
│  - Function: Text to vector embeddings                      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 개별 서비스 시작 및 테스트

### 옵션 1: 한 번에 모든 서비스 시작

```bash
# 모든 AI 서비스 시작
./start_service.sh all

# 모든 서비스 테스트
./test_all_services.sh
```

### 옵션 2: 개별 서비스 시작 및 테스트

#### 1. GLM-OCR Service

```bash
# 서비스 시작 (GPU 필요)
./start_service.sh ocr

# 또는 docker compose 직접 사용
docker compose up -d ocr_service

# 로그 확인
docker compose logs -f ocr_service

# 서비스 테스트
bash services/ocr/tests/test_ocr.sh

# 수동 테스트
curl http://localhost:8001/health
curl -X POST http://localhost:8001/test
```

**테스트 이미지로 OCR 테스트:**
```bash
cd services/ocr/tests

# 테스트 이미지 생성 (Python 필요)
python3 -c "from PIL import Image, ImageDraw; img=Image.new('RGB',(400,100),'white'); draw=ImageDraw.Draw(img); draw.text((10,40),'Test OCR Text',fill='black'); img.save('test_image.png')"

# OCR 실행
curl -X POST http://localhost:8001/ocr \
  -F "file=@test_image.png" \
  -F "language=en" | jq '.'
```

#### 2. E5 Embedding Service

```bash
# 서비스 시작 (GPU 필요)
./start_service.sh embedding

# 또는
docker compose up -d embedding_service

# 로그 확인
docker compose logs -f embedding_service

# 서비스 테스트
bash services/embedding/tests/test_embedding.sh

# 수동 테스트
curl http://localhost:8002/health
curl -X POST http://localhost:8002/test
```

**텍스트 임베딩 생성:**
```bash
# 단일 텍스트
curl -X POST http://localhost:8002/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": "Hello, this is a test sentence.",
    "normalize": true
  }' | jq '.dimension, .count'

# 여러 텍스트
curl -X POST http://localhost:8002/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "First sentence",
      "Second sentence",
      "한국어 문장"
    ]
  }' | jq '.embeddings | length'

# 유사도 계산
curl -X POST "http://localhost:8002/similarity?text1=Hello%20world&text2=Hi%20there" | jq '.'
```

#### 3. Hybrid Chunking Service

```bash
# 서비스 시작 (GPU 불필요)
./start_service.sh chunking

# 또는
docker compose up -d chunking_service

# 로그 확인
docker compose logs -f chunking_service

# 서비스 테스트
bash services/chunking/tests/test_chunking.sh

# 수동 테스트
curl http://localhost:8003/health
curl -X POST http://localhost:8003/test
```

**텍스트 청킹:**
```bash
# Hybrid 방식 (추천)
curl -X POST http://localhost:8003/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long document text here...",
    "method": "hybrid",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }' | jq '.chunk_count, .chunks[0]'

# Recursive 방식
curl -X POST http://localhost:8003/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long document text here...",
    "method": "recursive",
    "chunk_size": 500,
    "chunk_overlap": 100
  }' | jq '.'
```

## 📊 서비스 상태 확인

### Health Check (모든 서비스)

```bash
# 개별 서비스
curl http://localhost:8001/health  # OCR
curl http://localhost:8002/health  # Embedding
curl http://localhost:8003/health  # Chunking

# 한 번에 확인
for port in 8001 8002 8003; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq '.status'
done
```

### Docker Compose 상태

```bash
# 모든 서비스 상태
docker compose ps

# 특정 서비스 로그
docker compose logs ocr_service
docker compose logs embedding_service
docker compose logs chunking_service

# 실시간 로그
docker compose logs -f ocr_service
```

## 🔧 모델 설정

### GLM-OCR 모델 경로 변경

`.env` 파일:
```bash
# Hugging Face에서 자동 다운로드
OCR_MODEL_PATH=zai-org/GLM-OCR

# 로컬 경로 사용 (미리 다운로드한 경우)
OCR_MODEL_PATH=/path/to/local/glm-ocr
```

### E5 Embedding 모델 변경

`.env` 파일:
```bash
# 다국어 대형 모델 (1024차원)
EMBEDDING_MODEL_PATH=intfloat/multilingual-e5-large

# 영어 전용 (더 작음, 512차원)
EMBEDDING_MODEL_PATH=intfloat/e5-large-v2

# 한국어 특화
EMBEDDING_MODEL_PATH=jhgan/ko-sroberta-multitask
```

## 🐛 트러블슈팅

### OCR Service가 시작되지 않음

```bash
# GPU 확인
nvidia-smi

# 로그 확인
docker compose logs ocr_service

# 컨테이너 재시작
docker compose restart ocr_service
```

### Embedding Service OOM (Out of Memory)

```bash
# 배치 크기 줄이기 (API 호출 시)
curl -X POST http://localhost:8002/embed \
  -d '{"texts": [...], "batch_size": 16}'  # 기본값 32에서 16으로

# GPU 메모리 확인
nvidia-smi
```

### Chunking Service 느림

```bash
# Chunk 크기 증가 (처리량 증가)
curl -X POST http://localhost:8003/chunk \
  -d '{
    "text": "...",
    "chunk_size": 2000,  # 기본값 1000에서 증가
    "chunk_overlap": 100
  }'
```

## 📈 성능 최적화

### GPU 메모리 최적화

**docker-compose.yml** 수정:
```yaml
ocr_service:
  environment:
    - CUDA_VISIBLE_DEVICES=0  # GPU 0 사용
    
embedding_service:
  environment:
    - CUDA_VISIBLE_DEVICES=1  # GPU 1 사용 (2개 이상 있는 경우)
```

### 동시 처리 증가

```bash
# Worker 동시성 증가
docker compose up -d --scale celery_worker=4
```

## 🔗 Worker 통합

새로운 서비스를 사용하는 업데이트된 document processing:

```python
# worker/tasks/document_processing_v2.py 사용
from tasks.document_processing_v2 import process_document

# 비동기로 모든 서비스 호출
result = process_document.delay(
    file_path="/mnt/nas/test.pdf",
    file_hash="abc123",
    department="Clinical_Team",
    role="Manager"
)
```

## 📝 API 문서

각 서비스의 상세 API 문서:

- **OCR**: http://localhost:8001/docs
- **Embedding**: http://localhost:8002/docs
- **Chunking**: http://localhost:8003/docs

## 🎯 Production 배포 체크리스트

- [ ] GPU 메모리 충분한지 확인 (OCR: 8GB+, Embedding: 8GB+)
- [ ] 모델 사전 다운로드 완료
- [ ] Health check 모두 통과
- [ ] 각 서비스 독립 테스트 완료
- [ ] Worker 통합 테스트 완료
- [ ] 성능 벤치마크 완료

---

**Created**: 2026-02-08  
**Version**: 2.0.0  
**Services**: GLM-OCR, E5 Embedding, Hybrid Chunking

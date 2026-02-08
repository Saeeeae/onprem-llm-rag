# 🎉 시스템 업그레이드 완료!

## ✅ 완료된 작업

### 1. **GLM-OCR Service** (독립 컨테이너, GPU)
- **Model**: `zai-org/GLM-OCR` (VLM 기반 OCR)
- **Port**: 8001
- **기능**: 이미지 → 텍스트 (TIF, PNG, JPG, JPEG)
- **언어**: 영어, 한국어, 중국어, 일본어
- **파일**: 
  - `services/ocr/ocr_service.py`
  - `services/ocr/Dockerfile`
  - `services/ocr/tests/test_ocr.sh`

### 2. **E5 Embedding Service** (독립 컨테이너, GPU)
- **Model**: `intfloat/multilingual-e5-large`
- **Dimension**: 1024 (기존 384에서 업그레이드)
- **Port**: 8002
- **기능**: 텍스트 → 벡터 임베딩
- **특징**: 다국어 지원, 높은 정확도
- **파일**:
  - `services/embedding/embedding_service.py`
  - `services/embedding/Dockerfile`
  - `services/embedding/tests/test_embedding.sh`

### 3. **Hybrid Chunking Service** (독립 컨테이너, No GPU)
- **Method**: Semantic + Recursive
- **Port**: 8003
- **기능**: 지능형 텍스트 분할
- **특징**: 문맥 인식, 문단/문장 경계 보존
- **파일**:
  - `services/chunking/chunking_service.py`
  - `services/chunking/Dockerfile`
  - `services/chunking/tests/test_chunking.sh`

### 4. **Docker Compose 업데이트**
- 3개 신규 서비스 추가
- 각 서비스 독립 실행 가능
- Health check 구성
- GPU 리소스 할당

### 5. **테스트 스크립트**
- `./start_service.sh` - 개별 서비스 시작
- `./test_all_services.sh` - 전체 서비스 테스트
- 각 서비스별 독립 테스트 스크립트

### 6. **Worker 통합**
- `worker/tasks/document_processing_v2.py`
- 비동기 서비스 호출 (httpx)
- GLM-OCR, E5, Hybrid Chunking 통합

## 🚀 빠른 시작

### 개별 서비스 테스트

```bash
# 1. OCR Service 시작 및 테스트
./start_service.sh ocr
bash services/ocr/tests/test_ocr.sh

# 2. Embedding Service 시작 및 테스트
./start_service.sh embedding
bash services/embedding/tests/test_embedding.sh

# 3. Chunking Service 시작 및 테스트
./start_service.sh chunking
bash services/chunking/tests/test_chunking.sh
```

### 전체 시스템 시작

```bash
# 모든 AI 서비스 시작
./start_service.sh all

# 전체 테스트
./test_all_services.sh

# 또는 전체 시스템 시작
docker compose up -d
```

## 📊 서비스 포트

| Service | Port | GPU | Model |
|---------|------|-----|-------|
| GLM-OCR | 8001 | ✅ Required | zai-org/GLM-OCR |
| E5 Embedding | 8002 | ✅ Required | intfloat/multilingual-e5-large |
| Hybrid Chunking | 8003 | ❌ Not Required | LangChain |
| Backend API | 8000 | - | - |
| Frontend | 3000 | - | - |

## 🔧 환경 변수 (.env)

```bash
# OCR Model
OCR_MODEL_PATH=zai-org/GLM-OCR
OCR_SERVICE_URL=http://ocr_service:8001

# Embedding Model
EMBEDDING_MODEL_PATH=intfloat/multilingual-e5-large
EMBEDDING_SERVICE_URL=http://embedding_service:8002

# Chunking Service
CHUNKING_SERVICE_URL=http://chunking_service:8003

# Model Cache Directory (로컬에 모델 저장)
MODEL_CACHE_DIR=./model_cache
```

## 📚 문서

- **[SERVICES_README.md](SERVICES_README.md)** - 서비스 사용 가이드
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - 전체 아키텍처
- **[README.md](README.md)** - 프로젝트 개요

## 🔄 기존 대비 변경 사항

| 기능 | 이전 | 현재 (업그레이드) |
|------|------|-------------------|
| **OCR** | Tesseract | **GLM-OCR (VLM 기반)** |
| **Chunking** | 단순 단어 분할 | **Hybrid (Semantic + Recursive)** |
| **Embedding** | all-MiniLM-L6-v2 (384d) | **multilingual-e5-large (1024d)** |
| **구조** | 모놀리식 | **마이크로서비스 (독립 컨테이너)** |
| **테스트** | 통합 테스트만 | **개별 + 통합 테스트** |

## 💡 주요 개선점

1. **더 정확한 OCR**: VLM 기반 GLM-OCR로 복잡한 문서 처리 개선
2. **더 나은 임베딩**: 1024차원 E5 모델로 검색 정확도 향상
3. **지능형 청킹**: 문맥 인식 Hybrid Chunking으로 의미 보존
4. **독립 확장**: 각 서비스를 개별적으로 확장 가능
5. **쉬운 테스트**: 각 서비스를 독립적으로 테스트 가능

## 🎯 다음 단계

1. **모델 다운로드** (처음 실행 시 자동 다운로드, 시간 소요)
   ```bash
   # 사전 다운로드 (optional)
   docker compose up -d ocr_service embedding_service
   docker compose logs -f ocr_service
   docker compose logs -f embedding_service
   ```

2. **서비스 테스트**
   ```bash
   ./test_all_services.sh
   ```

3. **Worker 통합 테스트**
   ```bash
   # Celery worker 시작
   docker compose up -d celery_worker
   
   # 문서 처리 작업 실행
   docker compose exec celery_worker python -c "
   from tasks.document_processing_v2 import process_document
   result = process_document.delay('/path/to/test.pdf', 'hash123', 'Clinical_Team', 'Manager')
   print(result.get())
   "
   ```

4. **프로덕션 배포**
   ```bash
   # 전체 시스템 시작
   docker compose up -d
   
   # 상태 확인
   docker compose ps
   ```

## 📈 성능 예상

- **OCR 처리**: 페이지당 2-5초 (GPU 의존)
- **Embedding 생성**: 배치 32개 기준 1-3초
- **Chunking**: 1000 단어당 < 1초
- **전체 파이프라인**: 문서당 10-30초 (크기 및 복잡도에 따라)

## 🐛 문제 해결

### 서비스가 시작되지 않으면
```bash
# 로그 확인
docker compose logs [service_name]

# 재시작
docker compose restart [service_name]

# 재빌드
docker compose build [service_name]
docker compose up -d [service_name]
```

### GPU 메모리 부족
```bash
# GPU 사용량 확인
nvidia-smi

# 서비스별 GPU 분리 (docker-compose.yml)
# OCR: GPU 0
# Embedding: GPU 1
```

---

**업그레이드 완료일**: 2026-02-08  
**시스템 버전**: 2.0.0  
**새로운 모델**: GLM-OCR, E5-Large, Hybrid Chunking

# =============================================================================
# On-Premise LLM & RAG System - Makefile
# Usage: make mac | make prod | make down
# =============================================================================

.PHONY: mac prod down logs status clean build help

# Default target
help:
	@echo ""
	@echo "  On-Premise LLM & RAG System"
	@echo "  ──────────────────────────────────────────"
	@echo ""
	@echo "  Development (Mac M1/M2):"
	@echo "    make mac           Start with Ollama (lightweight)"
	@echo "    make mac-build     Build & start for Mac"
	@echo ""
	@echo "  Production (NVIDIA A100):"
	@echo "    make prod          Start with vLLM (full GPU)"
	@echo "    make prod-build    Build & start for production"
	@echo ""
	@echo "  Common:"
	@echo "    make down          Stop all services"
	@echo "    make logs          Follow all logs"
	@echo "    make logs-backend  Follow backend logs"
	@echo "    make status        Show service status"
	@echo "    make clean         Remove volumes and containers"
	@echo "    make test-login    Test login endpoint"
	@echo ""

# ─────────────────────────────────────────────
# Mac M1/M2 Development
# ─────────────────────────────────────────────
mac:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.mac.yml \
		--env-file env/mac.env \
		up -d
	@echo ""
	@echo "  ✓ Mac environment started"
	@echo "  Frontend:  http://localhost:8501"
	@echo "  Backend:   http://localhost:8000/docs"
	@echo "  Ollama:    http://localhost:11434"
	@echo ""

mac-build:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.mac.yml \
		--env-file env/mac.env \
		up -d --build

# ─────────────────────────────────────────────
# Production (NVIDIA A100)
# ─────────────────────────────────────────────
prod:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.prod.yml \
		--env-file env/prod.env \
		up -d
	@echo ""
	@echo "  ✓ Production environment started"
	@echo "  Frontend:  http://localhost:8501"
	@echo "  Backend:   http://localhost:8000/docs"
	@echo "  Milvus UI: http://localhost:3001"
	@echo ""

prod-build:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.prod.yml \
		--env-file env/prod.env \
		up -d --build

# ─────────────────────────────────────────────
# Common Operations
# ─────────────────────────────────────────────
down:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.mac.yml \
		-f docker-compose.prod.yml \
		down 2>/dev/null; true

logs:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.mac.yml \
		logs -f

logs-backend:
	docker logs -f backend

logs-ollama:
	docker logs -f ollama

status:
	@echo "=== Container Status ==="
	@docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.mac.yml \
		ps 2>/dev/null || docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.prod.yml \
		ps 2>/dev/null
	@echo ""
	@echo "=== Resource Usage ==="
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || true

clean:
	docker compose \
		-f docker-compose.base.yml \
		-f docker-compose.mac.yml \
		-f docker-compose.prod.yml \
		down -v --remove-orphans 2>/dev/null; true
	@echo "  ✓ All containers, volumes, and networks removed"

# ─────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────
test-login:
	@echo "Testing login with researcher account..."
	@curl -s -X POST http://localhost:8000/api/v1/auth/login \
		-H "Content-Type: application/json" \
		-d '{"username": "researcher", "password": "research123"}' | python3 -m json.tool

test-health:
	@curl -s http://localhost:8000/health | python3 -m json.tool

test-ollama:
	@curl -s http://localhost:11434/api/tags | python3 -m json.tool

# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────
setup-dirs:
	mkdir -p sample_docs/{level_1,level_2,level_3,level_4}
	echo "1등급 기밀 문서 샘플" > sample_docs/level_1/sample_topsecret.txt
	echo "2등급 기밀 문서 샘플" > sample_docs/level_2/sample_secret.txt
	echo "3등급 대외비 문서 샘플" > sample_docs/level_3/sample_confidential.txt
	echo "4등급 공개 문서 샘플" > sample_docs/level_4/sample_public.txt
	@echo "  ✓ Sample documents created"

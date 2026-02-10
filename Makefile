# =============================================================================
# On-Premise LLM & RAG System - Makefile
# =============================================================================

.PHONY: help dev dev-build dev-down dev-logs prod prod-build prod-down prod-logs \
        test test-docker ps clean

# Compose file references
DEV_COMPOSE  := docker compose -f docker-compose.dev.yml
PROD_COMPOSE := docker compose -f docker-compose.prod.yml

# Colors
RED    := \033[0;31m
GREEN  := \033[0;32m
YELLOW := \033[0;33m
BLUE   := \033[0;34m
NC     := \033[0m

# =============================================================================
# Help
# =============================================================================

help:
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  On-Premise LLM & RAG System$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev               Start development environment"
	@echo "  make dev-build         Build development images"
	@echo "  make dev-down          Stop development environment"
	@echo "  make dev-logs          Follow development logs"
	@echo "  make dev-restart       Restart development environment"
	@echo ""
	@echo "$(GREEN)Production:$(NC)"
	@echo "  make prod              Start production environment"
	@echo "  make prod-build        Build production images"
	@echo "  make prod-down         Stop production environment"
	@echo "  make prod-logs         Follow production logs"
	@echo "  make prod-restart      Restart production environment"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test              Run pytest locally"
	@echo "  make test-docker       Run pytest inside dev container"
	@echo "  make test-health       Test all health endpoints"
	@echo "  make test-services     Test AI service endpoints"
	@echo ""
	@echo "$(GREEN)Individual Services (dev):$(NC)"
	@echo "  make <service>-build   Build: backend, worker, ocr, embedding, chunking, reranker"
	@echo "  make <service>-logs    Follow logs for a service"
	@echo "  make <service>-restart Restart a service"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make ps                Show running containers"
	@echo "  make clean             Remove all containers and volumes"
	@echo ""

# =============================================================================
# Development Environment
# =============================================================================

dev:
	@$(DEV_COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)Development environment started$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Flower:    http://localhost:5555"
	@echo "  Qdrant:    http://localhost:6333/dashboard"
	@echo ""
	@echo "$(YELLOW)Debug ports:$(NC)"
	@echo "  Backend:   5678"
	@echo "  OCR:       5679"
	@echo "  Embedding: 5680"
	@echo "  Chunking:  5681"
	@echo "  Reranker:  5682"

dev-build:
	@echo "$(BLUE)Building development images...$(NC)"
	@$(DEV_COMPOSE) build
	@echo "$(GREEN)Development images built$(NC)"

dev-down:
	@$(DEV_COMPOSE) down
	@echo "$(GREEN)Development environment stopped$(NC)"

dev-logs:
	@$(DEV_COMPOSE) logs -f

dev-restart:
	@$(DEV_COMPOSE) restart
	@echo "$(GREEN)Development environment restarted$(NC)"

dev-ps:
	@$(DEV_COMPOSE) ps

# =============================================================================
# Production Environment
# =============================================================================

prod:
	@$(PROD_COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)Production environment started$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"

prod-build:
	@echo "$(BLUE)Building production images...$(NC)"
	@$(PROD_COMPOSE) build
	@echo "$(GREEN)Production images built$(NC)"

prod-down:
	@$(PROD_COMPOSE) down
	@echo "$(GREEN)Production environment stopped$(NC)"

prod-logs:
	@$(PROD_COMPOSE) logs -f

prod-restart:
	@$(PROD_COMPOSE) restart
	@echo "$(GREEN)Production environment restarted$(NC)"

prod-ps:
	@$(PROD_COMPOSE) ps

# =============================================================================
# Individual Service Control (Development)
# =============================================================================

backend-build:
	@$(DEV_COMPOSE) build backend
	@echo "$(GREEN)Backend built$(NC)"

backend-logs:
	@$(DEV_COMPOSE) logs -f backend

backend-restart:
	@$(DEV_COMPOSE) restart backend
	@echo "$(GREEN)Backend restarted$(NC)"

worker-build:
	@$(DEV_COMPOSE) build celery_worker
	@echo "$(GREEN)Worker built$(NC)"

worker-logs:
	@$(DEV_COMPOSE) logs -f celery_worker

worker-restart:
	@$(DEV_COMPOSE) restart celery_worker
	@echo "$(GREEN)Worker restarted$(NC)"

ocr-build:
	@$(DEV_COMPOSE) build ocr_service
	@echo "$(GREEN)OCR service built$(NC)"

ocr-logs:
	@$(DEV_COMPOSE) logs -f ocr_service

ocr-restart:
	@$(DEV_COMPOSE) restart ocr_service
	@echo "$(GREEN)OCR service restarted$(NC)"

embedding-build:
	@$(DEV_COMPOSE) build embedding_service
	@echo "$(GREEN)Embedding service built$(NC)"

embedding-logs:
	@$(DEV_COMPOSE) logs -f embedding_service

embedding-restart:
	@$(DEV_COMPOSE) restart embedding_service
	@echo "$(GREEN)Embedding service restarted$(NC)"

chunking-build:
	@$(DEV_COMPOSE) build chunking_service
	@echo "$(GREEN)Chunking service built$(NC)"

chunking-logs:
	@$(DEV_COMPOSE) logs -f chunking_service

chunking-restart:
	@$(DEV_COMPOSE) restart chunking_service
	@echo "$(GREEN)Chunking service restarted$(NC)"

reranker-build:
	@$(DEV_COMPOSE) build reranker_service
	@echo "$(GREEN)Reranker service built$(NC)"

reranker-logs:
	@$(DEV_COMPOSE) logs -f reranker_service

reranker-restart:
	@$(DEV_COMPOSE) restart reranker_service
	@echo "$(GREEN)Reranker service restarted$(NC)"

frontend-build:
	@$(DEV_COMPOSE) build frontend
	@echo "$(GREEN)Frontend built$(NC)"

frontend-logs:
	@$(DEV_COMPOSE) logs -f frontend

frontend-restart:
	@$(DEV_COMPOSE) restart frontend
	@echo "$(GREEN)Frontend restarted$(NC)"

vllm-build:
	@$(DEV_COMPOSE) build vllm_service
	@echo "$(GREEN)vLLM service built$(NC)"

vllm-logs:
	@$(DEV_COMPOSE) logs -f vllm_service

vllm-restart:
	@$(DEV_COMPOSE) restart vllm_service
	@echo "$(GREEN)vLLM service restarted$(NC)"

# =============================================================================
# Testing
# =============================================================================

test:
	@python -m pytest tests/ -v

test-docker:
	@$(DEV_COMPOSE) exec backend pytest tests/ -v

test-health:
	@echo "$(BLUE)Testing health endpoints...$(NC)"
	@echo ""
	@echo "Backend:"
	@curl -sf http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "$(RED)  Not responding$(NC)"
	@echo "OCR Service:"
	@curl -sf http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "$(RED)  Not responding$(NC)"
	@echo "Embedding Service:"
	@curl -sf http://localhost:8002/health | python3 -m json.tool 2>/dev/null || echo "$(RED)  Not responding$(NC)"
	@echo "Chunking Service:"
	@curl -sf http://localhost:8003/health | python3 -m json.tool 2>/dev/null || echo "$(RED)  Not responding$(NC)"
	@echo "Reranker Service:"
	@curl -sf http://localhost:8004/health | python3 -m json.tool 2>/dev/null || echo "$(RED)  Not responding$(NC)"
	@echo "Qdrant:"
	@curl -sf http://localhost:6333/health | python3 -m json.tool 2>/dev/null || echo "$(RED)  Not responding$(NC)"

test-services:
	@echo "$(BLUE)Testing AI service endpoints...$(NC)"
	@echo ""
	@echo "OCR Service /test:"
	@curl -sf http://localhost:8001/test | python3 -m json.tool 2>/dev/null || echo "$(RED)  Test failed$(NC)"
	@echo ""
	@echo "Embedding Service /test:"
	@curl -sf http://localhost:8002/test | python3 -m json.tool 2>/dev/null || echo "$(RED)  Test failed$(NC)"
	@echo ""
	@echo "Chunking Service /test:"
	@curl -sf http://localhost:8003/test | python3 -m json.tool 2>/dev/null || echo "$(RED)  Test failed$(NC)"
	@echo ""
	@echo "Reranker Service /test:"
	@curl -sf http://localhost:8004/test | python3 -m json.tool 2>/dev/null || echo "$(RED)  Test failed$(NC)"

# =============================================================================
# Utilities
# =============================================================================

ps:
	@$(DEV_COMPOSE) ps 2>/dev/null; $(PROD_COMPOSE) ps 2>/dev/null

clean:
	@echo "$(RED)WARNING: This will remove all containers and volumes!$(NC)"
	@echo "$(RED)All data (PostgreSQL, Redis, Qdrant) will be lost!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(DEV_COMPOSE) down -v --remove-orphans 2>/dev/null; \
		$(PROD_COMPOSE) down -v --remove-orphans 2>/dev/null; \
		echo "$(GREEN)All containers and volumes removed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

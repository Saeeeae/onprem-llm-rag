# =============================================================================
# On-Premise LLM & RAG System - Service Management Makefile
# Usage: make <service>-<action> (e.g., make backend-build)
# =============================================================================

.PHONY: help dev-setup prod-setup

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
help:
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  On-Premise LLM & RAG System - Service Management$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Environment Setup:$(NC)"
	@echo "  make dev-setup         Copy override file for development"
	@echo "  make prod-setup        Remove override file for production"
	@echo ""
	@echo "$(GREEN)All Services:$(NC)"
	@echo "  make up                Start all services (dev mode if override exists)"
	@echo "  make down              Stop all services"
	@echo "  make build-all         Build all service images"
	@echo "  make restart-all       Restart all services"
	@echo "  make logs              Follow logs for all services"
	@echo "  make ps                Show service status"
	@echo "  make clean             Remove containers and volumes (⚠️ data loss)"
	@echo ""
	@echo "$(GREEN)Individual Service Control:$(NC)"
	@echo "  make <service>-build   Build service image"
	@echo "  make <service>-run     Start service"
	@echo "  make <service>-stop    Stop service"
	@echo "  make <service>-remove  Remove service container"
	@echo "  make <service>-restart Restart service"
	@echo "  make <service>-logs    Follow service logs"
	@echo ""
	@echo "$(GREEN)Available Services:$(NC)"
	@echo "  $(YELLOW)Core Services:$(NC)     backend, frontend, worker"
	@echo "  $(YELLOW)AI Services:$(NC)      ocr, embedding, chunking"
	@echo "  $(YELLOW)Infrastructure:$(NC)   postgres, redis, qdrant, vllm"
	@echo "  $(YELLOW)Monitoring:$(NC)       flower (dev only)"
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make backend-build     # Build backend image"
	@echo "  make backend-run       # Start backend service"
	@echo "  make backend-logs      # Follow backend logs"
	@echo "  make ocr-restart       # Restart OCR service"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test-health       Test all health endpoints"
	@echo "  make test-backend      Test backend API"
	@echo "  make test-services     Test AI services"
	@echo ""

# =============================================================================
# Environment Setup
# =============================================================================

dev-setup:
	@if [ ! -f docker-compose.override.yml ]; then \
		cp docker-compose.override.example.yml docker-compose.override.yml; \
		echo "$(GREEN)✓$(NC) Development environment configured"; \
		echo "$(YELLOW)→$(NC) Run 'make up' to start in development mode"; \
	else \
		echo "$(YELLOW)⚠$(NC) docker-compose.override.yml already exists"; \
	fi

prod-setup:
	@if [ -f docker-compose.override.yml ]; then \
		rm docker-compose.override.yml; \
		echo "$(GREEN)✓$(NC) Production environment configured"; \
		echo "$(YELLOW)→$(NC) Run 'make up' to start in production mode"; \
	else \
		echo "$(GREEN)✓$(NC) Already in production mode"; \
	fi

# =============================================================================
# All Services Management
# =============================================================================

up:
	@docker compose up -d
	@echo ""
	@echo "$(GREEN)✓$(NC) Services started"
	@echo ""
	@make ps
	@echo ""
	@echo "$(YELLOW)→$(NC) Frontend:  http://localhost:3000"
	@echo "$(YELLOW)→$(NC) Backend:   http://localhost:8000"
	@echo "$(YELLOW)→$(NC) API Docs:  http://localhost:8000/docs"

down:
	@docker compose down
	@echo "$(GREEN)✓$(NC) All services stopped"

build-all:
	@echo "$(BLUE)Building all services...$(NC)"
	@docker compose build
	@echo "$(GREEN)✓$(NC) All services built"

restart-all:
	@echo "$(BLUE)Restarting all services...$(NC)"
	@docker compose restart
	@echo "$(GREEN)✓$(NC) All services restarted"

logs:
	@docker compose logs -f

ps:
	@docker compose ps

clean:
	@echo "$(RED)⚠ WARNING: This will remove all containers and volumes!$(NC)"
	@echo "$(RED)⚠ All data will be lost!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v --remove-orphans; \
		echo "$(GREEN)✓$(NC) All containers and volumes removed"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# =============================================================================
# Backend Service
# =============================================================================

backend-build:
	@docker compose build backend
	@echo "$(GREEN)✓$(NC) Backend built"

backend-run:
	@docker compose up -d backend
	@echo "$(GREEN)✓$(NC) Backend started"

backend-stop:
	@docker compose stop backend
	@echo "$(GREEN)✓$(NC) Backend stopped"

backend-remove:
	@docker compose rm -f backend
	@echo "$(GREEN)✓$(NC) Backend container removed"

backend-restart:
	@docker compose restart backend
	@echo "$(GREEN)✓$(NC) Backend restarted"

backend-logs:
	@docker compose logs -f backend

# =============================================================================
# Frontend Service
# =============================================================================

frontend-build:
	@docker compose build frontend
	@echo "$(GREEN)✓$(NC) Frontend built"

frontend-run:
	@docker compose up -d frontend
	@echo "$(GREEN)✓$(NC) Frontend started"

frontend-stop:
	@docker compose stop frontend
	@echo "$(GREEN)✓$(NC) Frontend stopped"

frontend-remove:
	@docker compose rm -f frontend
	@echo "$(GREEN)✓$(NC) Frontend container removed"

frontend-restart:
	@docker compose restart frontend
	@echo "$(GREEN)✓$(NC) Frontend restarted"

frontend-logs:
	@docker compose logs -f frontend

# =============================================================================
# Worker Service (Celery)
# =============================================================================

worker-build:
	@docker compose build celery_worker
	@echo "$(GREEN)✓$(NC) Worker built"

worker-run:
	@docker compose up -d celery_worker
	@echo "$(GREEN)✓$(NC) Worker started"

worker-stop:
	@docker compose stop celery_worker
	@echo "$(GREEN)✓$(NC) Worker stopped"

worker-remove:
	@docker compose rm -f celery_worker
	@echo "$(GREEN)✓$(NC) Worker container removed"

worker-restart:
	@docker compose restart celery_worker
	@echo "$(GREEN)✓$(NC) Worker restarted"

worker-logs:
	@docker compose logs -f celery_worker

# =============================================================================
# OCR Service
# =============================================================================

ocr-build:
	@docker compose build ocr_service
	@echo "$(GREEN)✓$(NC) OCR service built"

ocr-run:
	@docker compose up -d ocr_service
	@echo "$(GREEN)✓$(NC) OCR service started"

ocr-stop:
	@docker compose stop ocr_service
	@echo "$(GREEN)✓$(NC) OCR service stopped"

ocr-remove:
	@docker compose rm -f ocr_service
	@echo "$(GREEN)✓$(NC) OCR service container removed"

ocr-restart:
	@docker compose restart ocr_service
	@echo "$(GREEN)✓$(NC) OCR service restarted"

ocr-logs:
	@docker compose logs -f ocr_service

# =============================================================================
# Embedding Service
# =============================================================================

embedding-build:
	@docker compose build embedding_service
	@echo "$(GREEN)✓$(NC) Embedding service built"

embedding-run:
	@docker compose up -d embedding_service
	@echo "$(GREEN)✓$(NC) Embedding service started"

embedding-stop:
	@docker compose stop embedding_service
	@echo "$(GREEN)✓$(NC) Embedding service stopped"

embedding-remove:
	@docker compose rm -f embedding_service
	@echo "$(GREEN)✓$(NC) Embedding service container removed"

embedding-restart:
	@docker compose restart embedding_service
	@echo "$(GREEN)✓$(NC) Embedding service restarted"

embedding-logs:
	@docker compose logs -f embedding_service

# =============================================================================
# Chunking Service
# =============================================================================

chunking-build:
	@docker compose build chunking_service
	@echo "$(GREEN)✓$(NC) Chunking service built"

chunking-run:
	@docker compose up -d chunking_service
	@echo "$(GREEN)✓$(NC) Chunking service started"

chunking-stop:
	@docker compose stop chunking_service
	@echo "$(GREEN)✓$(NC) Chunking service stopped"

chunking-remove:
	@docker compose rm -f chunking_service
	@echo "$(GREEN)✓$(NC) Chunking service container removed"

chunking-restart:
	@docker compose restart chunking_service
	@echo "$(GREEN)✓$(NC) Chunking service restarted"

chunking-logs:
	@docker compose logs -f chunking_service

# =============================================================================
# vLLM Service
# =============================================================================

vllm-build:
	@docker compose build vllm_service
	@echo "$(GREEN)✓$(NC) vLLM service built"

vllm-run:
	@docker compose up -d vllm_service
	@echo "$(GREEN)✓$(NC) vLLM service started"

vllm-stop:
	@docker compose stop vllm_service
	@echo "$(GREEN)✓$(NC) vLLM service stopped"

vllm-remove:
	@docker compose rm -f vllm_service
	@echo "$(GREEN)✓$(NC) vLLM service container removed"

vllm-restart:
	@docker compose restart vllm_service
	@echo "$(GREEN)✓$(NC) vLLM service restarted"

vllm-logs:
	@docker compose logs -f vllm_service

# =============================================================================
# Database Services
# =============================================================================

postgres-run:
	@docker compose up -d postgres
	@echo "$(GREEN)✓$(NC) PostgreSQL started"

postgres-stop:
	@docker compose stop postgres
	@echo "$(GREEN)✓$(NC) PostgreSQL stopped"

postgres-restart:
	@docker compose restart postgres
	@echo "$(GREEN)✓$(NC) PostgreSQL restarted"

postgres-logs:
	@docker compose logs -f postgres

redis-run:
	@docker compose up -d redis
	@echo "$(GREEN)✓$(NC) Redis started"

redis-stop:
	@docker compose stop redis
	@echo "$(GREEN)✓$(NC) Redis stopped"

redis-restart:
	@docker compose restart redis
	@echo "$(GREEN)✓$(NC) Redis restarted"

redis-logs:
	@docker compose logs -f redis

qdrant-run:
	@docker compose up -d qdrant
	@echo "$(GREEN)✓$(NC) Qdrant started"

qdrant-stop:
	@docker compose stop qdrant
	@echo "$(GREEN)✓$(NC) Qdrant stopped"

qdrant-restart:
	@docker compose restart qdrant
	@echo "$(GREEN)✓$(NC) Qdrant restarted"

qdrant-logs:
	@docker compose logs -f qdrant

# =============================================================================
# Monitoring (Flower)
# =============================================================================

flower-run:
	@docker compose --profile dev up -d flower
	@echo "$(GREEN)✓$(NC) Flower started at http://localhost:5555"

flower-stop:
	@docker compose stop flower
	@echo "$(GREEN)✓$(NC) Flower stopped"

flower-logs:
	@docker compose logs -f flower

# =============================================================================
# Testing
# =============================================================================

test-health:
	@echo "$(BLUE)Testing service health endpoints...$(NC)"
	@echo ""
	@echo "Backend:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "$(RED)✗ Backend not responding$(NC)"
	@echo ""
	@echo "OCR Service:"
	@curl -s http://localhost:8001/health | python3 -m json.tool || echo "$(RED)✗ OCR not responding$(NC)"
	@echo ""
	@echo "Embedding Service:"
	@curl -s http://localhost:8002/health | python3 -m json.tool || echo "$(RED)✗ Embedding not responding$(NC)"
	@echo ""
	@echo "Chunking Service:"
	@curl -s http://localhost:8003/health | python3 -m json.tool || echo "$(RED)✗ Chunking not responding$(NC)"
	@echo ""
	@echo "Qdrant:"
	@curl -s http://localhost:6333/health | python3 -m json.tool || echo "$(RED)✗ Qdrant not responding$(NC)"

test-backend:
	@echo "$(BLUE)Testing backend API...$(NC)"
	@curl -s http://localhost:8000/docs > /dev/null && echo "$(GREEN)✓$(NC) API docs available" || echo "$(RED)✗$(NC) API docs not available"

test-services:
	@echo "$(BLUE)Testing AI services...$(NC)"
	@echo "OCR Service:"
	@curl -s http://localhost:8001/test | python3 -m json.tool || echo "$(RED)✗ OCR test failed$(NC)"
	@echo ""
	@echo "Embedding Service:"
	@curl -s http://localhost:8002/test | python3 -m json.tool || echo "$(RED)✗ Embedding test failed$(NC)"
	@echo ""
	@echo "Chunking Service:"
	@curl -s http://localhost:8003/test | python3 -m json.tool || echo "$(RED)✗ Chunking test failed$(NC)"

# =============================================================================
# Quick Development Commands
# =============================================================================

dev: dev-setup up
	@echo "$(GREEN)✓$(NC) Development environment ready"

prod: prod-setup up
	@echo "$(GREEN)✓$(NC) Production environment ready"

rebuild:
	@echo "$(BLUE)Rebuilding and restarting all services...$(NC)"
	@docker compose build
	@docker compose up -d
	@echo "$(GREEN)✓$(NC) All services rebuilt and restarted"

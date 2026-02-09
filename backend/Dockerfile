# =============================================================================
# Base Stage - Shared Dependencies
# =============================================================================
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Development Stage - Hot-Reload + Debugging
# =============================================================================
FROM base AS development

# Install development tools
RUN pip install --no-cache-dir \
    debugpy \
    pytest \
    pytest-asyncio \
    pytest-cov \
    ipdb

# Copy application code
COPY ./app /app/app

# Create logs directory
RUN mkdir -p /app/logs

# Expose application port + debugpy port
EXPOSE 8000 5678

# Run with hot-reload (single worker for debugging)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# =============================================================================
# Production Stage - Optimized & Secure
# =============================================================================
FROM base AS production

# Copy application code
COPY ./app /app/app

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with production settings (4 workers, uvloop, httptools)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]

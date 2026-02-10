# =============================================================================
# E5 Embedding Service - Base Stage
# =============================================================================
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS base

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install shared module
COPY shared/ /tmp/shared/
RUN pip3 install --no-cache-dir /tmp/shared/ && rm -rf /tmp/shared

# Copy and install requirements
COPY services/embedding/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# =============================================================================
# Development Stage - Debugging Tools
# =============================================================================
FROM base AS development

# Install development tools
RUN pip3 install --no-cache-dir \
    debugpy \
    pytest \
    pytest-asyncio \
    ipdb

# Copy service code
COPY services/embedding/embedding_service.py .

# Expose application port + debugpy port
EXPOSE 8002 5680

# Set environment variables
ENV EMBEDDING_MODEL=intfloat/multilingual-e5-large \
    EMBEDDING_SERVICE_PORT=8002 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=DEBUG

# Run service
CMD ["python3", "-u", "embedding_service.py"]

# =============================================================================
# Production Stage - Optimized & Secure
# =============================================================================
FROM base AS production

# Copy service code
COPY services/embedding/embedding_service.py .

# Create non-root user
RUN useradd -m -u 1000 embeduser && chown -R embeduser:embeduser /app
USER embeduser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Set environment variables
ENV EMBEDDING_MODEL=intfloat/multilingual-e5-large \
    EMBEDDING_SERVICE_PORT=8002 \
    PYTHONUNBUFFERED=1

# Run service
CMD ["python3", "embedding_service.py"]

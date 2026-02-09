# =============================================================================
# Hybrid Chunking Service - Base Stage
# =============================================================================
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Development Stage - Debugging Tools
# =============================================================================
FROM base AS development

# Install development tools
RUN pip install --no-cache-dir \
    debugpy \
    pytest \
    pytest-asyncio \
    ipdb

# Copy service code
COPY chunking_service.py .

# Expose application port + debugpy port
EXPOSE 8003 5681

# Set environment variables
ENV CHUNKING_SERVICE_PORT=8003 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=DEBUG

# Run service
CMD ["python", "-u", "chunking_service.py"]

# =============================================================================
# Production Stage - Optimized & Secure
# =============================================================================
FROM base AS production

# Copy service code
COPY chunking_service.py .

# Create non-root user
RUN useradd -m -u 1000 chunkuser && chown -R chunkuser:chunkuser /app
USER chunkuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Set environment variables
ENV CHUNKING_SERVICE_PORT=8003 \
    PYTHONUNBUFFERED=1

# Run service
CMD ["python", "chunking_service.py"]

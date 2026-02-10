# =============================================================================
# Base Stage - Shared Dependencies
# =============================================================================
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies for OCR and document processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-kor \
    poppler-utils \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install shared module
COPY shared/ /tmp/shared/
RUN pip install --no-cache-dir /tmp/shared/ && rm -rf /tmp/shared

# Copy and install requirements
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Development Stage - Debugging + Single Worker
# =============================================================================
FROM base AS development

# Install development tools
RUN pip install --no-cache-dir \
    debugpy \
    pytest \
    pytest-celery \
    ipdb \
    watchdog

# Copy worker code
COPY worker/ /app/

# Create logs directory
RUN mkdir -p /app/logs

# Run with debug logging, single worker for easier debugging
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=debug", "--concurrency=1", "--pool=solo"]

# =============================================================================
# Production Stage - Optimized & Secure
# =============================================================================
FROM base AS production

# Copy worker code
COPY worker/ /app/

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN useradd -m -u 1000 celeryuser && chown -R celeryuser:celeryuser /app
USER celeryuser

# Run with production settings (prefork pool, 4 workers)
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=4", "--pool=prefork"]

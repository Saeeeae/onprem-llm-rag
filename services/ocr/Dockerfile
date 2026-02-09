# =============================================================================
# GLM-OCR Service - Base Stage
# =============================================================================
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS base

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
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
COPY ocr_service.py .

# Expose application port + debugpy port
EXPOSE 8001 5679

# Set environment variables
ENV OCR_MODEL=zai-org/GLM-OCR \
    OCR_SERVICE_PORT=8001 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=DEBUG

# Run service
CMD ["python3", "-u", "ocr_service.py"]

# =============================================================================
# Production Stage - Optimized & Secure
# =============================================================================
FROM base AS production

# Copy service code
COPY ocr_service.py .

# Create non-root user
RUN useradd -m -u 1000 ocruser && chown -R ocruser:ocruser /app
USER ocruser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Set environment variables
ENV OCR_MODEL=zai-org/GLM-OCR \
    OCR_SERVICE_PORT=8001 \
    PYTHONUNBUFFERED=1

# Run service
CMD ["python3", "ocr_service.py"]

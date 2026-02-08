# E5 Embedding Service Dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy service code
COPY embedding_service.py .

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Environment variables
ENV EMBEDDING_MODEL=intfloat/multilingual-e5-large
ENV EMBEDDING_SERVICE_PORT=8002
ENV PYTHONUNBUFFERED=1

# Run service
CMD ["python3", "embedding_service.py"]

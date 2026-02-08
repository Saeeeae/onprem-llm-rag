# GLM-OCR Service Dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy service code
COPY ocr_service.py .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Environment variables
ENV OCR_MODEL=zai-org/GLM-OCR
ENV OCR_SERVICE_PORT=8001
ENV PYTHONUNBUFFERED=1

# Run service
CMD ["python3", "ocr_service.py"]

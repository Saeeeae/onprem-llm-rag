FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-kor \
    poppler-utils \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . /app

# Create logs directory
RUN mkdir -p /app/logs

# Default command (override in docker-compose)
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]

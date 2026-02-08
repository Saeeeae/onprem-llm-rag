#!/bin/bash
# Start Individual Service for Testing

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Usage: ./start_service.sh <service_name>"
    echo ""
    echo "Available services:"
    echo "  ocr        - GLM-OCR Service (Port 8001)"
    echo "  embedding  - E5 Embedding Service (Port 8002)"
    echo "  chunking   - Hybrid Chunking Service (Port 8003)"
    echo "  all        - All services"
    echo ""
    echo "Examples:"
    echo "  ./start_service.sh ocr"
    echo "  ./start_service.sh embedding"
    echo "  ./start_service.sh all"
    exit 1
fi

case $SERVICE in
    ocr)
        echo "🚀 Starting GLM-OCR Service..."
        docker compose up -d ocr_service
        echo "✅ Service started at http://localhost:8001"
        echo "   Test: bash services/ocr/tests/test_ocr.sh"
        ;;
    embedding)
        echo "🚀 Starting E5 Embedding Service..."
        docker compose up -d embedding_service
        echo "✅ Service started at http://localhost:8002"
        echo "   Test: bash services/embedding/tests/test_embedding.sh"
        ;;
    chunking)
        echo "🚀 Starting Hybrid Chunking Service..."
        docker compose up -d chunking_service
        echo "✅ Service started at http://localhost:8003"
        echo "   Test: bash services/chunking/tests/test_chunking.sh"
        ;;
    all)
        echo "🚀 Starting all AI services..."
        docker compose up -d ocr_service embedding_service chunking_service
        echo "✅ All services started"
        echo "   OCR:       http://localhost:8001"
        echo "   Embedding: http://localhost:8002"
        echo "   Chunking:  http://localhost:8003"
        echo ""
        echo "   Run tests: ./test_all_services.sh"
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        exit 1
        ;;
esac

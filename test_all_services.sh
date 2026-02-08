#!/bin/bash
# Test All Services Script

echo "═══════════════════════════════════════════════════════"
echo "  Testing All On-Premise LLM Services"
echo "═══════════════════════════════════════════════════════"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Test OCR Service
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  GLM-OCR Service (Port 8001)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash services/ocr/tests/test_ocr.sh

# Test Embedding Service
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  E5 Embedding Service (Port 8002)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash services/embedding/tests/test_embedding.sh

# Test Chunking Service
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Hybrid Chunking Service (Port 8003)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash services/chunking/tests/test_chunking.sh

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  All Service Tests Completed!"
echo "═══════════════════════════════════════════════════════"

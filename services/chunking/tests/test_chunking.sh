#!/bin/bash
# Hybrid Chunking Service Test Script

echo "🧪 Testing Hybrid Chunking Service..."
echo ""

CHUNKING_URL="${CHUNKING_URL:-http://localhost:8003}"

# Test 1: Health Check
echo "1️⃣ Health Check"
curl -X GET "$CHUNKING_URL/health" | jq '.'
echo ""
echo ""

# Test 2: Service Info
echo "2️⃣ Service Info"
curl -X GET "$CHUNKING_URL/" | jq '.'
echo ""
echo ""

# Test 3: Built-in test
echo "3️⃣ Internal Test (All Methods)"
curl -X POST "$CHUNKING_URL/test" | jq '.'
echo ""
echo ""

# Test 4: Recursive chunking
echo "4️⃣ Recursive Chunking"
curl -X POST "$CHUNKING_URL/chunk" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "This is a long document with multiple sentences. We want to split it intelligently. The first paragraph discusses the introduction. It sets the context for everything that follows.\n\nThe second paragraph goes into more detail. Here we explore the main concepts and provide examples. This is crucial for understanding.\n\nThe third paragraph concludes our discussion. It wraps up all the key points.",
        "method": "recursive",
        "chunk_size": 200,
        "chunk_overlap": 50
    }' | jq '.chunk_count, .avg_chunk_length, .chunks[0]'
echo ""
echo ""

# Test 5: Hybrid chunking
echo "5️⃣ Hybrid Chunking (Recommended)"
curl -X POST "$CHUNKING_URL/chunk" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "This is a long document with multiple sentences. We want to split it intelligently. The first paragraph discusses the introduction. It sets the context for everything that follows.\n\nThe second paragraph goes into more detail. Here we explore the main concepts and provide examples. This is crucial for understanding.\n\nThe third paragraph concludes our discussion. It wraps up all the key points.",
        "method": "hybrid",
        "chunk_size": 200,
        "chunk_overlap": 50
    }' | jq '.chunk_count, .method, .chunks'
echo ""

echo "✅ Hybrid Chunking Service tests completed!"

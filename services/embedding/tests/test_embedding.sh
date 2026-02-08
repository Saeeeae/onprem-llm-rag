#!/bin/bash
# E5 Embedding Service Test Script

echo "🧪 Testing E5 Embedding Service..."
echo ""

EMBEDDING_URL="${EMBEDDING_URL:-http://localhost:8002}"

# Test 1: Health Check
echo "1️⃣ Health Check"
curl -X GET "$EMBEDDING_URL/health" | jq '.'
echo ""
echo ""

# Test 2: Service Info
echo "2️⃣ Service Info"
curl -X GET "$EMBEDDING_URL/" | jq '.'
echo ""
echo ""

# Test 3: Built-in test
echo "3️⃣ Internal Test (Multilingual)"
curl -X POST "$EMBEDDING_URL/test" | jq '.'
echo ""
echo ""

# Test 4: Single text embedding
echo "4️⃣ Single Text Embedding"
curl -X POST "$EMBEDDING_URL/embed" \
    -H "Content-Type: application/json" \
    -d '{
        "texts": "This is a test sentence for embedding.",
        "normalize": true,
        "batch_size": 32
    }' | jq '.embeddings[0][:10], .dimension, .count'
echo ""
echo ""

# Test 5: Batch embedding
echo "5️⃣ Batch Text Embedding"
curl -X POST "$EMBEDDING_URL/embed" \
    -H "Content-Type: application/json" \
    -d '{
        "texts": [
            "First sentence in English.",
            "두번째 문장은 한국어입니다.",
            "第三个句子是中文。"
        ],
        "normalize": true
    }' | jq '.count, .dimension'
echo ""
echo ""

# Test 6: Similarity
echo "6️⃣ Similarity Test"
curl -X POST "$EMBEDDING_URL/similarity?text1=Hello%20world&text2=Hi%20there" | jq '.'
echo ""

echo "✅ E5 Embedding Service tests completed!"

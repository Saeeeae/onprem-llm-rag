#!/bin/bash
# GLM-OCR Service Test Script

echo "🧪 Testing GLM-OCR Service..."
echo ""

OCR_URL="${OCR_URL:-http://localhost:8001}"

# Test 1: Health Check
echo "1️⃣ Health Check"
curl -X GET "$OCR_URL/health" | jq '.'
echo ""
echo ""

# Test 2: Root endpoint
echo "2️⃣ Service Info"
curl -X GET "$OCR_URL/" | jq '.'
echo ""
echo ""

# Test 3: Built-in test endpoint
echo "3️⃣ Internal Test"
curl -X POST "$OCR_URL/test" | jq '.'
echo ""
echo ""

# Test 4: OCR with sample image (if image exists)
if [ -f "test_image.png" ]; then
    echo "4️⃣ OCR Test with test_image.png"
    curl -X POST "$OCR_URL/ocr" \
        -F "file=@test_image.png" \
        -F "language=en" | jq '.'
    echo ""
else
    echo "4️⃣ Skipped (test_image.png not found)"
    echo "   Create a test image: services/ocr/tests/test_image.png"
fi

echo "✅ GLM-OCR Service tests completed!"

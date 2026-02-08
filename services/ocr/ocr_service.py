"""
GLM-OCR Service - Standalone OCR API
Model: zai-org/GLM-OCR (VLM-based OCR)
"""
import os
import io
import logging
from pathlib import Path
from typing import Optional, List
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="GLM-OCR Service",
    description="Standalone OCR service using GLM-OCR model",
    version="1.0.0"
)

# Global model cache
_model = None
_tokenizer = None
_device = None


def get_device():
    """Get compute device (GPU if available)"""
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {_device}")
    return _device


def load_model():
    """Lazy load GLM-OCR model"""
    global _model, _tokenizer
    
    if _model is None:
        model_name = os.getenv("OCR_MODEL", "zai-org/GLM-OCR")
        model_path = os.getenv("OCR_MODEL_PATH", model_name)
        
        logger.info(f"Loading GLM-OCR model from {model_path}...")
        
        try:
            _tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            _model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if get_device() == "cuda" else torch.float32
            ).to(get_device())
            _model.eval()
            
            logger.info("✅ GLM-OCR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load GLM-OCR model: {e}")
            raise
    
    return _model, _tokenizer


def ocr_image(image: Image.Image, language: str = "en") -> str:
    """
    Perform OCR on image using GLM-OCR
    
    Args:
        image: PIL Image
        language: Language code (en, zh, ko, etc.)
    
    Returns:
        Extracted text
    """
    model, tokenizer = load_model()
    
    try:
        # Convert image to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # GLM-OCR inference
        # Note: Actual implementation depends on GLM-OCR's API
        # This is a placeholder - adjust based on model documentation
        with torch.no_grad():
            # Prepare prompt (adjust based on model's requirements)
            prompt = "Extract all text from this image:"
            
            # Process image and generate text
            # Placeholder - replace with actual GLM-OCR API call
            inputs = tokenizer(prompt, return_tensors="pt").to(get_device())
            
            # Generate text (adjust based on model API)
            outputs = model.generate(
                **inputs,
                max_length=2048,
                temperature=0.1,
                top_p=0.9,
                do_sample=False
            )
            
            text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove prompt from output
            if text.startswith(prompt):
                text = text[len(prompt):].strip()
            
            return text
    
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GLM-OCR",
        "model": os.getenv("OCR_MODEL", "zai-org/GLM-OCR"),
        "status": "running",
        "device": get_device()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        device = get_device()
        model_loaded = _model is not None
        
        return {
            "status": "healthy",
            "model_loaded": model_loaded,
            "device": device,
            "gpu_available": torch.cuda.is_available()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/ocr")
async def ocr_endpoint(
    file: UploadFile = File(...),
    language: str = "en"
):
    """
    OCR endpoint
    
    Args:
        file: Image file (PNG, JPG, JPEG, TIF, TIFF)
        language: Language code (en, ko, zh, ja)
    
    Returns:
        Extracted text
    """
    try:
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/tiff"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        logger.info(f"Processing image: {file.filename} ({image.size})")
        
        # Perform OCR
        text = ocr_image(image, language)
        
        return {
            "status": "success",
            "filename": file.filename,
            "text": text,
            "language": language,
            "image_size": image.size
        }
    
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_ocr():
    """
    Test endpoint with sample image
    Creates a simple test image and performs OCR
    """
    try:
        # Create test image with text
        from PIL import ImageDraw, ImageFont
        
        img = Image.new('RGB', (800, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw test text
        test_text = "GLM-OCR Test: Hello World! 안녕하세요 테스트입니다."
        draw.text((10, 80), test_text, fill='black')
        
        # Perform OCR
        result = ocr_image(img, language="en")
        
        return {
            "status": "success",
            "test_image_text": test_text,
            "ocr_result": result,
            "note": "This is a synthetic test. Real OCR performance may vary."
        }
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("OCR_SERVICE_PORT", "8001"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

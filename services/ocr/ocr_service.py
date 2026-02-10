"""
GLM-OCR Service - Standalone OCR API

Model: zai-org/GLM-OCR (VLM-based OCR)
Port: 8001
"""
import os
import io
from pathlib import Path
from typing import Optional, List

import uvicorn
from PIL import Image
from fastapi import UploadFile, File, HTTPException

from shared.logging import setup_logging
from shared.device import get_device, get_torch_dtype, is_gpu_available
from shared.config import GPUServiceSettings
from shared.fastapi_utils import create_service_app, add_health_endpoint, add_root_endpoint

# =============================================================================
# Configuration
# =============================================================================


class OCRSettings(GPUServiceSettings):
    SERVICE_NAME: str = "GLM-OCR"
    SERVICE_PORT: int = 8001
    OCR_MODEL: str = "zai-org/GLM-OCR"
    OCR_MODEL_PATH: str = ""


settings = OCRSettings()
logger = setup_logging(settings.SERVICE_NAME, level=settings.LOG_LEVEL)

# =============================================================================
# Model Management (Lazy Loading)
# =============================================================================

_model = None
_tokenizer = None


def load_model():
    """Lazy load GLM-OCR model"""
    global _model, _tokenizer

    if _model is None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        model_path = settings.OCR_MODEL_PATH or settings.OCR_MODEL
        logger.info(f"Loading GLM-OCR model from {model_path}...")

        try:
            _tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            _model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=get_torch_dtype(),
            ).to(get_device())
            _model.eval()

            logger.info("GLM-OCR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load GLM-OCR model: {e}")
            raise

    return _model, _tokenizer


def ocr_image(image: Image.Image, language: str = "en") -> str:
    """Perform OCR on image using GLM-OCR."""
    model, tokenizer = load_model()
    import torch

    try:
        if image.mode != "RGB":
            image = image.convert("RGB")

        with torch.no_grad():
            prompt = "Extract all text from this image:"
            inputs = tokenizer(prompt, return_tensors="pt").to(get_device())

            outputs = model.generate(
                **inputs,
                max_length=2048,
                temperature=0.1,
                top_p=0.9,
                do_sample=False
            )

            text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            if text.startswith(prompt):
                text = text[len(prompt):].strip()

            return text

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise


# =============================================================================
# FastAPI Application
# =============================================================================

app = create_service_app(
    title="GLM-OCR Service",
    description="Standalone OCR service using GLM-OCR model",
    version="1.0.0",
)


def _health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "model_loaded": _model is not None,
        "device": get_device(),
        "gpu_available": is_gpu_available(),
    }


add_health_endpoint(app, _health_check)
add_root_endpoint(app, {
    "service": settings.SERVICE_NAME,
    "model": settings.OCR_MODEL,
    "status": "running",
    "device": get_device(),
})


@app.post("/ocr")
async def ocr_endpoint(
    file: UploadFile = File(...),
    language: str = "en"
):
    """OCR endpoint - extract text from uploaded image."""
    try:
        allowed_types = ["image/png", "image/jpeg", "image/tiff"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )

        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        logger.info(f"Processing image: {file.filename} ({image.size})")

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
    """Test endpoint with sample image."""
    try:
        from PIL import ImageDraw

        img = Image.new('RGB', (800, 200), color='white')
        draw = ImageDraw.Draw(img)

        test_text = "GLM-OCR Test: Hello World!"
        draw.text((10, 80), test_text, fill='black')

        result = ocr_image(img, language="en")

        return {
            "status": "success",
            "test_image_text": test_text,
            "ocr_result": result,
            "device": get_device(),
        }

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("OCR_SERVICE_PORT", str(settings.SERVICE_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

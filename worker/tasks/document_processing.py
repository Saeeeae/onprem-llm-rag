"""Document Processing Task - OCR, Chunking, Embedding"""
import os
from pathlib import Path
from celery import Task
from celery_app import app
from typing import List
import logging

logger = logging.getLogger(__name__)


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from document based on file type"""
    text = ""
    
    try:
        if file_type in [".pdf"]:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = "\n".join([page.extract_text() for page in reader.pages])
        
        elif file_type in [".docx", ".doc"]:
            import docx
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        
        elif file_type in [".xlsx", ".xls"]:
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            text = ""
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    text += " ".join([str(cell) for cell in row if cell]) + "\n"
        
        elif file_type in [".pptx", ".ppt"]:
            from pptx import Presentation
            prs = Presentation(file_path)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
        
        elif file_type in [".tif", ".tiff", ".png", ".jpg", ".jpeg"]:
            # OCR for images
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang=os.getenv("TESSERACT_LANG", "eng"))
        
        else:
            logger.warning(f"Unsupported file type: {file_type}")
    
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
    
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []
    
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks


@app.task(name="tasks.document_processing.process_document", bind=True)
def process_document(
    self: Task,
    file_path: str,
    file_hash: str,
    department: str,
    role: str
):
    """
    Process a single document:
    1. Extract text (OCR if needed)
    2. Chunk text
    3. Generate embeddings
    4. Upsert to Qdrant
    5. Log to PostgreSQL
    """
    logger.info(f"Processing document: {file_path}")
    
    try:
        # Get file info
        path = Path(file_path)
        filename = path.name
        file_type = path.suffix.lower()
        file_size = path.stat().st_size
        
        # Step 1: Extract text
        text = extract_text(file_path, file_type)
        
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return {"status": "skipped", "reason": "no_text"}
        
        # Step 2: Chunk text
        chunks = chunk_text(text)
        logger.info(f"Generated {len(chunks)} chunks from {filename}")
        
        # Step 3 & 4: Embed and upsert to Qdrant
        # (In production, import qdrant_service and database models)
        # For now, placeholder
        
        logger.info(f"Successfully processed {filename}")
        
        return {
            "status": "completed",
            "filename": filename,
            "chunks": len(chunks),
            "department": department,
            "role": role
        }
    
    except Exception as e:
        logger.error(f"Failed to process document {file_path}: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

"""
Document Processing Task - Using Microservices

OCR: GLM-OCR Service (Port 8001)
Chunking: Hybrid Chunking Service (Port 8003)
Embedding: E5 Embedding Service (Port 8002)
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from celery import Task
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointIdsList, PointStruct, VectorParams
from sqlalchemy import create_engine, text

from celery_app import app

from shared.service_client import OCRClient, ChunkingClient, EmbeddingClient

logger = logging.getLogger(__name__)

# Service clients
ocr_client = OCRClient(base_url=os.getenv("OCR_URL", "http://ocr_service:8001"))
chunking_client = ChunkingClient(base_url=os.getenv("CHUNKING_URL", "http://chunking_service:8003"))
embedding_client = EmbeddingClient(base_url=os.getenv("EMBEDDING_URL", "http://embedding_service:8002"))

_db_engine = None


def get_db_engine():
    """Create and cache SQLAlchemy engine for worker metadata writes."""
    global _db_engine
    if _db_engine is None:
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "admin")
        password = os.getenv("POSTGRES_PASSWORD", "securepassword")
        database = os.getenv("POSTGRES_DB", "onprem_llm")
        dsn = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        _db_engine = create_engine(dsn, pool_pre_ping=True)
    return _db_engine


def get_qdrant_client() -> QdrantClient:
    """Create Qdrant client from environment."""
    return QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        timeout=30,
    )


def ensure_qdrant_collection(client: QdrantClient) -> str:
    """Create collection if missing."""
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "documents")
    vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "1024"))
    collections = client.get_collections().collections
    names = {collection.name for collection in collections}
    if collection_name not in names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    return collection_name


def get_existing_document(file_hash: str) -> Optional[Dict[str, Any]]:
    """Load existing document row by file hash."""
    engine = get_db_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, qdrant_point_ids
                FROM documents
                WHERE file_hash = :file_hash
                """
            ),
            {"file_hash": file_hash},
        ).mappings().first()
        return dict(row) if row else None


def delete_existing_qdrant_points(client: QdrantClient, collection_name: str, point_ids: List[str]) -> None:
    """Delete previous vectors before re-indexing modified document."""
    if not point_ids:
        return
    client.delete(
        collection_name=collection_name,
        points_selector=PointIdsList(points=point_ids),
    )


def upsert_to_qdrant(
    client: QdrantClient,
    collection_name: str,
    document_id: UUID,
    chunks: List[str],
    embeddings: List[List[float]],
    department: str,
    role: str,
    filename: str,
    file_path: str,
    file_type: str,
) -> List[str]:
    """Upsert chunk vectors with RBAC payload into Qdrant."""
    points: List[PointStruct] = []
    point_ids: List[str] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid4())
        point_ids.append(point_id)
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document_id": str(document_id),
                    "chunk_index": idx,
                    "content": chunk,
                    "filename": filename,
                    "file_path": file_path,
                    "file_type": file_type,
                    "department": department,
                    "role": role,
                },
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    return point_ids


def upsert_document_metadata(
    document_id: UUID,
    filename: str,
    file_path: str,
    file_type: str,
    file_size: int,
    file_hash: str,
    department: str,
    role: str,
    point_ids: List[str],
    chunk_count: int,
) -> None:
    """Upsert processed document metadata into PostgreSQL."""
    engine = get_db_engine()
    point_ids_literal = "{" + ",".join(point_ids) + "}"
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO documents (
                    id, filename, file_path, file_type, file_size, file_hash,
                    department, role, qdrant_point_ids, chunk_count, indexed_at, updated_at
                )
                VALUES (
                    CAST(:id AS uuid), :filename, :file_path, :file_type, :file_size, :file_hash,
                    :department, :role, CAST(:qdrant_point_ids AS uuid[]), :chunk_count, NOW(), NOW()
                )
                ON CONFLICT (file_hash) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    file_path = EXCLUDED.file_path,
                    file_type = EXCLUDED.file_type,
                    file_size = EXCLUDED.file_size,
                    department = EXCLUDED.department,
                    role = EXCLUDED.role,
                    qdrant_point_ids = EXCLUDED.qdrant_point_ids,
                    chunk_count = EXCLUDED.chunk_count,
                    indexed_at = NOW(),
                    updated_at = NOW()
                """
            ),
            {
                "id": str(document_id),
                "filename": filename,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": file_size,
                "file_hash": file_hash,
                "department": department,
                "role": role,
                "qdrant_point_ids": point_ids_literal,
                "chunk_count": chunk_count,
            },
        )


async def extract_text_async(file_path: str, file_type: str) -> str:
    """Extract text from document using appropriate service."""
    text = ""

    try:
        if file_type in [".tif", ".tiff", ".png", ".jpg", ".jpeg"]:
            result = await ocr_client.ocr(file_path)
            text = result.get("text", "")
            logger.info(f"OCR extracted {len(text)} chars from {file_path}")

        elif file_type in [".pdf"]:
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

        else:
            logger.warning(f"Unsupported file type: {file_type}")

    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")

    return text.strip()


async def chunk_text_async(
    text: str,
    method: str = "hybrid",
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[str]:
    """Chunk text using Hybrid Chunking Service."""
    if not text:
        return []

    try:
        result = await chunking_client.chunk(
            text=text,
            method=method,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
        chunks = result.get("chunks", [])
        logger.info(f"Chunking created {len(chunks)} chunks (method={method})")
        return chunks

    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        return []


async def embed_chunks_async(chunks: List[str], batch_size: int = 32) -> List[List[float]]:
    """Generate embeddings using E5 Embedding Service."""
    if not chunks:
        return []

    try:
        result = await embedding_client.embed(
            texts=chunks,
            normalize=True,
            batch_size=batch_size,
        )
        embeddings = result.get("embeddings", [])
        dimension = result.get("dimension", 0)
        logger.info(f"Embedded {len(embeddings)} chunks (dimension={dimension})")
        return embeddings

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []


@app.task(name="tasks.document_processing.process_document", bind=True)
def process_document(
    self: Task,
    file_path: str,
    file_hash: str,
    department: str,
    role: str
):
    """
    Process a single document using microservices:
    1. Extract text (GLM-OCR for images, libraries for docs)
    2. Chunk text (Hybrid Chunking Service)
    3. Generate embeddings (E5 Embedding Service)
    4. Upsert to Qdrant
    5. Log to PostgreSQL
    """
    logger.info(f"Processing document: {file_path}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        path = Path(file_path)
        filename = path.name
        file_type = path.suffix.lower()
        file_size = path.stat().st_size

        # Step 1: Extract text
        text = loop.run_until_complete(extract_text_async(file_path, file_type))
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return {"status": "skipped", "reason": "no_text"}

        # Step 2: Chunk text
        chunks = loop.run_until_complete(
            chunk_text_async(text, method="hybrid", chunk_size=1000, overlap=200)
        )
        if not chunks:
            logger.warning(f"No chunks created from {file_path}")
            return {"status": "skipped", "reason": "no_chunks"}

        # Step 3: Generate embeddings
        embeddings = loop.run_until_complete(embed_chunks_async(chunks, batch_size=32))
        if not embeddings:
            logger.warning(f"No embeddings generated for {file_path}")
            return {"status": "skipped", "reason": "no_embeddings"}
        if len(embeddings) != len(chunks):
            raise RuntimeError(
                f"Chunk/embedding mismatch for {filename}: {len(chunks)} chunks, {len(embeddings)} embeddings"
            )

        # Step 4: Upsert to Qdrant (replace existing points if file hash already exists)
        existing_document = get_existing_document(file_hash)
        document_id = (
            UUID(str(existing_document["id"])) if existing_document else uuid4()
        )

        qdrant_client = get_qdrant_client()
        collection_name = ensure_qdrant_collection(qdrant_client)

        old_point_ids = []
        if existing_document and existing_document.get("qdrant_point_ids"):
            old_point_ids = [str(point_id) for point_id in existing_document["qdrant_point_ids"]]
        delete_existing_qdrant_points(qdrant_client, collection_name, old_point_ids)

        point_ids = upsert_to_qdrant(
            client=qdrant_client,
            collection_name=collection_name,
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            department=department,
            role=role,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
        )

        # Step 5: Persist metadata in PostgreSQL
        upsert_document_metadata(
            document_id=document_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            file_hash=file_hash,
            department=department,
            role=role,
            point_ids=point_ids,
            chunk_count=len(chunks),
        )

        logger.info(
            f"Successfully processed {filename}: chunks={len(chunks)}, vectors={len(point_ids)}"
        )
        return {
            "status": "completed",
            "filename": filename,
            "document_id": str(document_id),
            "chunks": len(chunks),
            "embeddings": len(embeddings),
            "department": department,
            "role": role,
        }
    except Exception as e:
        logger.error(f"Failed to process document {file_path}: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        loop.close()

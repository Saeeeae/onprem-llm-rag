"""Qdrant Vector Database Service with RBAC Filtering"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for interacting with Qdrant vector database"""
    
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            timeout=30
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_url = settings.EMBEDDING_URL
        self._initialize_collection()

    def _extract_vector_size(self, collection_info: Any) -> Optional[int]:
        """Extract vector size from Qdrant collection info."""
        try:
            vectors = collection_info.config.params.vectors
            if isinstance(vectors, dict):
                # Named vectors; use first size.
                first_vector = next(iter(vectors.values()), None)
                return int(getattr(first_vector, "size", 0)) if first_vector else None
            return int(getattr(vectors, "size", 0))
        except Exception:
            return None

    def _initialize_collection(self):
        """Initialize Qdrant collection if not exists"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                info = self.client.get_collection(self.collection_name)
                existing_size = self._extract_vector_size(info)
                expected_size = settings.QDRANT_VECTOR_SIZE
                if existing_size and existing_size != expected_size:
                    raise RuntimeError(
                        "Qdrant vector size mismatch for collection "
                        f"'{self.collection_name}': existing={existing_size}, expected={expected_size}. "
                        "Align embedding model/vector size or recreate the collection."
                    )
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")
            raise

    def _embed_batch_sync(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings from embedding microservice (sync)."""
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.embedding_url}/embed",
                json={
                    "texts": texts,
                    "normalize": True,
                    "batch_size": settings.EMBEDDING_BATCH_SIZE,
                },
            )
            response.raise_for_status()
            result = response.json()

        embeddings = result.get("embeddings", [])
        if len(embeddings) != len(texts):
            raise ValueError(
                f"Embedding count mismatch: expected {len(texts)}, got {len(embeddings)}"
            )
        return embeddings

    async def _embed_batch_async(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings from embedding microservice (async)."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.embedding_url}/embed",
                json={
                    "texts": texts,
                    "normalize": True,
                    "batch_size": settings.EMBEDDING_BATCH_SIZE,
                },
            )
            response.raise_for_status()
            result = response.json()

        embeddings = result.get("embeddings", [])
        if len(embeddings) != len(texts):
            raise ValueError(
                f"Embedding count mismatch: expected {len(texts)}, got {len(embeddings)}"
            )
        return embeddings
    
    def upsert_documents(
        self,
        document_id: UUID,
        chunks: List[str],
        department: str,
        role: str,
        filename: str,
        file_path: str,
        file_type: str,
    ) -> List[UUID]:
        """
        Insert document chunks with RBAC metadata.
        Returns list of Qdrant point IDs.
        """
        try:
            # Generate embeddings via embedding microservice
            embeddings = self._embed_batch_sync(chunks)
            
            # Create points with RBAC metadata
            points = []
            point_ids = []
            
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = uuid4()
                point_ids.append(point_id)
                
                point = PointStruct(
                    id=str(point_id),
                    vector=embedding,
                    payload={
                        "document_id": str(document_id),
                        "chunk_index": idx,
                        "content": chunk,
                        "filename": filename,
                        "file_path": file_path,
                        "file_type": file_type,
                        "department": department,  # RBAC: Department filter
                        "role": role,              # RBAC: Role filter
                    }
                )
                points.append(point)
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} chunks for document {document_id}")
            return point_ids
        
        except Exception as e:
            logger.error(f"Failed to upsert documents: {e}")
            raise
    
    async def search_with_filter(
        self,
        query: str,
        user_filter: Dict[str, Any],
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search vectors with RBAC filter.
        
        Args:
            query: Search query text
            user_filter: RBAC filter based on user's department and role
            top_k: Number of results to return
            score_threshold: Minimum similarity score (optional)
        
        Returns:
            List of search results with content and metadata
        """
        try:
            # Generate query embedding
            query_embedding = (await self._embed_batch_async([query]))[0]
            
            # Build Qdrant filter
            qdrant_filter = Filter(
                must=[
                    Filter(
                        should=[
                            FieldCondition(
                                key="department",
                                match=MatchValue(value=cond["match"]["value"])
                            )
                            for cond in user_filter["must"][0]["should"]
                        ]
                    ),
                    Filter(
                        should=[
                            FieldCondition(
                                key="role",
                                match=MatchValue(value=cond["match"]["value"])
                            )
                            for cond in user_filter["must"][1]["should"]
                        ]
                    )
                ]
            )
            
            # Search
            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=top_k,
                score_threshold=score_threshold or settings.RAG_SIMILARITY_THRESHOLD,
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "point_id": hit.id,
                    "document_id": hit.payload.get("document_id"),
                    "content": hit.payload.get("content"),
                    "filename": hit.payload.get("filename"),
                    "file_type": hit.payload.get("file_type"),
                    "chunk_index": hit.payload.get("chunk_index"),
                    "score": hit.score,
                    "metadata": {
                        "department": hit.payload.get("department"),
                        "role": hit.payload.get("role"),
                        "file_path": hit.payload.get("file_path")
                    }
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def delete_document(self, document_id: UUID):
        """Delete all chunks of a document"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=str(document_id))
                            )
                        ]
                    )
                }
            )
            logger.info(f"Deleted document {document_id} from Qdrant")
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_points": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}


# Singleton instance
qdrant_service = QdrantService()

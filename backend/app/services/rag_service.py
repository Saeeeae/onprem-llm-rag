"""RAG Orchestration Service"""
import time
from typing import List, Dict, Any
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import vllm_service
from app.models import User
from app.middleware.auth import build_qdrant_filter
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrate RAG pipeline: Retrieve + Generate"""
    
    def build_rag_prompt(self, query: str, context_documents: List[Dict[str, Any]]) -> str:
        """Build prompt with retrieved context"""
        context_str = "\n\n".join([
            f"[Document {i+1}: {doc['filename']}]\n{doc['content']}"
            for i, doc in enumerate(context_documents)
        ])
        
        prompt = f"""You are a helpful AI assistant for a biotech company. Answer the user's question based ONLY on the provided documents. If the answer cannot be found in the documents, say "I don't have enough information to answer that question."

Context Documents:
{context_str}

User Question: {query}

Answer:"""
        return prompt
    
    async def generate_answer(
        self,
        query: str,
        user: User,
        top_k: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Generate RAG answer:
        1. Build RBAC filter from user
        2. Retrieve relevant documents from Qdrant
        3. Build prompt with context
        4. Generate answer with vLLM
        """
        start_time = time.time()
        
        try:
            # Step 1: Build RBAC filter
            user_filter = build_qdrant_filter(user)
            logger.info(f"User {user.username} ({user.department}/{user.role}) querying: {query[:100]}...")
            
            # Step 2: Retrieve documents
            retrieved_docs = qdrant_service.search_with_filter(
                query=query,
                user_filter=user_filter,
                top_k=top_k
            )
            
            if not retrieved_docs:
                return {
                    "response": "I couldn't find any relevant documents to answer your question. This might be due to access restrictions or the information not being available in the system.",
                    "retrieved_documents": [],
                    "token_count": 0,
                    "latency_ms": int((time.time() - start_time) * 1000)
                }
            
            # Step 3: Build prompt
            prompt = self.build_rag_prompt(query, retrieved_docs)
            
            # Step 4: Generate answer
            llm_response = await vllm_service.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Parse response
            answer = llm_response["choices"][0]["text"].strip()
            token_count = llm_response["usage"]["total_tokens"]
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "response": answer,
                "retrieved_documents": [
                    {
                        "document_id": doc["document_id"],
                        "filename": doc["filename"],
                        "score": doc["score"],
                        "content": doc["content"][:500],  # Truncate for response
                        "metadata": doc["metadata"]
                    }
                    for doc in retrieved_docs
                ],
                "token_count": token_count,
                "latency_ms": latency_ms
            }
        
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            raise


# Singleton instance
rag_service = RAGService()

import logging
from typing import List, Dict, Any

import numpy as np
import ollama

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi


# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =============================================================================
# HYBRID RETRIEVAL ENGINE
# =============================================================================

class HybridRetriever:
    """
    Enterprise Hybrid Retrieval Engine

    Features:
    - Dense retrieval
    - Sparse retrieval (BM25)
    - Reciprocal Rank Fusion (RRF)
    - Final context profiling
    - LLM-ready context generation
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        rrf_k: int = 60
    ):

        logger.info(
            f"Loading embedding model: {embedding_model}"
        )

        self.embedding_model = SentenceTransformer(
            embedding_model
        )

        self.rrf_k = rrf_k

        logger.info(
            "HybridRetriever initialized successfully"
        )

    # =========================================================================
    # DENSE RETRIEVAL
    # =========================================================================

    def dense_retrieval(
        self,
        query: str,
        candidate_documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Dense semantic retrieval using cosine similarity.
        """

        try:

            logger.info(
                "Starting dense retrieval"
            )

            query_embedding = self.embedding_model.encode(
                query
            )

            chunks = [
                doc["chunk"]
                for doc in candidate_documents
            ]

            chunk_embeddings = self.embedding_model.encode(
                chunks
            )

            similarities = cosine_similarity(
                [query_embedding],
                chunk_embeddings
            )[0]

            dense_results = []

            for idx, score in enumerate(similarities):

                dense_results.append({
                    "rank": idx + 1,
                    "score": float(score),
                    "document": candidate_documents[idx]
                })

            dense_results = sorted(
                dense_results,
                key=lambda x: x["score"],
                reverse=True
            )

            logger.info(
                f"Dense retrieval completed | "
                f"Retrieved: {len(dense_results[:top_k])}"
            )

            return dense_results[:top_k]

        except Exception as e:

            logger.exception(
                f"Dense retrieval failed: {str(e)}"
            )

            return []

    # =========================================================================
    # SPARSE RETRIEVAL
    # =========================================================================

    def sparse_retrieval(
        self,
        query: str,
        candidate_documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Sparse retrieval using BM25.
        """

        try:

            logger.info(
                "Starting sparse retrieval"
            )

            chunks = [
                doc["chunk"]
                for doc in candidate_documents
            ]

            tokenized_corpus = [
                chunk.lower().split()
                for chunk in chunks
            ]

            bm25 = BM25Okapi(tokenized_corpus)

            tokenized_query = query.lower().split()

            scores = bm25.get_scores(
                tokenized_query
            )

            sparse_results = []

            for idx, score in enumerate(scores):

                sparse_results.append({
                    "rank": idx + 1,
                    "score": float(score),
                    "document": candidate_documents[idx]
                })

            sparse_results = sorted(
                sparse_results,
                key=lambda x: x["score"],
                reverse=True
            )

            logger.info(
                f"Sparse retrieval completed | "
                f"Retrieved: {len(sparse_results[:top_k])}"
            )

            return sparse_results[:top_k]

        except Exception as e:

            logger.exception(
                f"Sparse retrieval failed: {str(e)}"
            )

            return []

    # =========================================================================
    # RECIPROCAL RANK FUSION (RRF)
    # =========================================================================

    def reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Combines dense + sparse retrieval rankings.
        """

        try:

            logger.info(
                "Starting Reciprocal Rank Fusion"
            )

            rrf_scores = {}

            # -----------------------------------------------------------------
            # DENSE RESULTS
            # -----------------------------------------------------------------

            for rank, result in enumerate(dense_results):

                doc_id = result["document"]["id"]

                score = 1 / (self.rrf_k + rank + 1)

                if doc_id not in rrf_scores:

                    rrf_scores[doc_id] = {
                        "rrf_score": 0,
                        "document": result["document"]
                    }

                rrf_scores[doc_id]["rrf_score"] += score

            # -----------------------------------------------------------------
            # SPARSE RESULTS
            # -----------------------------------------------------------------

            for rank, result in enumerate(sparse_results):

                doc_id = result["document"]["id"]

                score = 1 / (self.rrf_k + rank + 1)

                if doc_id not in rrf_scores:

                    rrf_scores[doc_id] = {
                        "rrf_score": 0,
                        "document": result["document"]
                    }

                rrf_scores[doc_id]["rrf_score"] += score

            # -----------------------------------------------------------------
            # SORT FINAL RESULTS
            # -----------------------------------------------------------------

            final_results = []

            for doc_id, value in rrf_scores.items():

                final_results.append({
                    "document": value["document"],
                    "rrf_score": value["rrf_score"]
                })

            final_results = sorted(
                final_results,
                key=lambda x: x["rrf_score"],
                reverse=True
            )

            logger.info(
                f"RRF completed | Final results: "
                f"{len(final_results[:top_k])}"
            )

            return final_results[:top_k]

        except Exception as e:

            logger.exception(
                f"RRF failed: {str(e)}"
            )

            return []

    # =========================================================================
    # CONTEXT PROFILING
    # =========================================================================

    def build_llm_context(
        self,
        retrieval_results: List[Dict[str, Any]]
    ) -> str:
        """
        Builds enterprise-grade context for LLM.
        """

        try:

            logger.info(
                "Building LLM context"
            )

            context_sections = []

            for idx, result in enumerate(retrieval_results):

                document = result["document"]

                metadata = document.get(
                    "metadata",
                    {}
                )

                context_block = f"""
DOCUMENT {idx + 1}

Invoice Number:
{metadata.get('invoice_number', 'UNKNOWN')}

Vendor:
{metadata.get('vendor', 'UNKNOWN')}

PO Number:
{metadata.get('po_number', 'UNKNOWN')}

Status:
{metadata.get('status', 'UNKNOWN')}

Risk Level:
{metadata.get('risk_level', 'UNKNOWN')}

Amount:
{metadata.get('amount', 'UNKNOWN')}

Chunk Content:
{document.get('chunk', '')}
"""

                context_sections.append(
                    context_block.strip()
                )

            final_context = "\n\n".join(
                context_sections
            )

            logger.info(
                "LLM context built successfully"
            )

            return final_context

        except Exception as e:

            logger.exception(
                f"Context building failed: {str(e)}"
            )

            return ""

    # =========================================================================
    # FINAL LLM ANSWER GENERATION
    # =========================================================================

    def generate_llm_response(
        self,
        user_query: str,
        context: str,
        model: str = "qwen2.5:3b"
    ) -> str:
        """
        Final answer generation using retrieved context.
        """

        try:

            logger.info(
                "Generating final LLM response"
            )

            prompt = f"""
You are an enterprise invoice intelligence assistant.

Your job is to answer questions using the retrieved invoice context.

INSTRUCTIONS:
- Be factual and concise.
- Use the provided context.
- If partial information exists, answer using available evidence.
- Explain reasoning clearly.
- Do not hallucinate invoice details.

USER QUERY:
{user_query}

RETRIEVED CONTEXT:
{context}

FINAL ANSWER:
"""

            response = ollama.chat(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            final_answer = response["message"]["content"]

            logger.info(
                "LLM response generated successfully"
            )

            return final_answer

        except Exception as e:

            logger.exception(
                f"LLM response generation failed: {str(e)}"
            )

            return (
                "Failed to generate response."
            )

    # =========================================================================
    # FULL HYBRID PIPELINE
    # =========================================================================

    def retrieve_and_answer(
        self,
        user_query: str,
        semantic_query: str,
        candidate_documents: List[Dict[str, Any]],
        top_k: int = 5,
        llm_model: str = "qwen2.5:3b"
    ) -> Dict[str, Any]:
        """
        Complete enterprise retrieval pipeline.
        """

        try:

            logger.info(
                "Starting full hybrid retrieval pipeline"
            )

            # -----------------------------------------------------------------
            # DENSE RETRIEVAL
            # -----------------------------------------------------------------

            dense_results = self.dense_retrieval(
                query=semantic_query,
                candidate_documents=candidate_documents,
                top_k=top_k
            )

            # -----------------------------------------------------------------
            # SPARSE RETRIEVAL
            # -----------------------------------------------------------------

            sparse_results = self.sparse_retrieval(
                query=semantic_query,
                candidate_documents=candidate_documents,
                top_k=top_k
            )

            # -----------------------------------------------------------------
            # RRF FUSION
            # -----------------------------------------------------------------

            fused_results = self.reciprocal_rank_fusion(
                dense_results=dense_results,
                sparse_results=sparse_results,
                top_k=top_k
            )

            # -----------------------------------------------------------------
            # CONTEXT BUILDING
            # -----------------------------------------------------------------

            context = self.build_llm_context(
                fused_results
            )

            # -----------------------------------------------------------------
            # FINAL LLM RESPONSE
            # -----------------------------------------------------------------

            final_answer = self.generate_llm_response(
                user_query=user_query,
                context=context,
                model=llm_model
            )

            logger.info(
                "Hybrid retrieval pipeline completed"
            )

            return {
                "query": user_query,
                "semantic_query": semantic_query,
                "dense_results": dense_results,
                "sparse_results": sparse_results,
                "fused_results": fused_results,
                "context": context,
                "final_answer": final_answer
            }

        except Exception as e:

            logger.exception(
                f"Hybrid pipeline failed: {str(e)}"
            )

            return {
                "error": str(e)
            }



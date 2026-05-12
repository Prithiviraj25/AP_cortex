import pickle
import logging
from pathlib import Path
from typing import Dict, Any

from inference.query_understanding import QueryUnderstandingEngine
from inference.metadata_filtering import MetadataFilterEngine
from inference.hybrid_search_answer import HybridRetriever


# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)



# =============================================================================
# CONFIGURATION
# =============================================================================

VECTOR_DB_DIR = Path("vectordatabase")

METADATA_PATH = VECTOR_DB_DIR / "metadata.pkl"

DEFAULT_LLM_MODEL = "qwen2.5:3b"


# =============================================================================
# INFERENCE PIPELINE
# =============================================================================

class InvoiceInferencePipeline:
    """
    Enterprise-grade invoice intelligence inference pipeline.

    Pipeline:
    User Query
        ↓
    Query Understanding
        ↓
    Metadata Validation
        ↓
    Metadata Filtering
        ↓
    Hybrid Retrieval
        ↓
    RRF Fusion
        ↓
    Context Building
        ↓
    Final LLM Answer
    """

    def __init__(
        self,
        llm_model: str = DEFAULT_LLM_MODEL
    ):

        self.llm_model = llm_model

        self.metadata_store = None

        self.query_engine = None
        self.metadata_engine = None
        self.hybrid_retriever = None

        self._initialize()

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def _initialize(self) -> None:
        """
        Initializes all retrieval components.
        """

        try:

            logger.info(
                "Initializing InvoiceInferencePipeline"
            )

            # -----------------------------------------------------------------
            # VALIDATE VECTOR DATABASE
            # -----------------------------------------------------------------

            if not VECTOR_DB_DIR.exists():

                raise FileNotFoundError(
                    f"Vector DB directory not found: "
                    f"{VECTOR_DB_DIR}"
                )

            if not METADATA_PATH.exists():

                raise FileNotFoundError(
                    f"Metadata store not found: "
                    f"{METADATA_PATH}"
                )

            logger.info(
                "Vector database validation successful"
            )

            # -----------------------------------------------------------------
            # LOAD METADATA STORE
            # -----------------------------------------------------------------

            logger.info(
                "Loading metadata store"
            )

            with open(METADATA_PATH, "rb") as f:

                self.metadata_store = pickle.load(f)

            logger.info(
                f"Metadata store loaded successfully | "
                f"Records: {len(self.metadata_store)}"
            )

            # -----------------------------------------------------------------
            # INITIALIZE QUERY UNDERSTANDING
            # -----------------------------------------------------------------

            self.query_engine = QueryUnderstandingEngine(
                model=self.llm_model
            )

            logger.info(
                "Query understanding engine initialized"
            )

            # -----------------------------------------------------------------
            # INITIALIZE METADATA FILTERING
            # -----------------------------------------------------------------

            self.metadata_engine = MetadataFilterEngine(
                metadata_store=self.metadata_store
            )

            logger.info(
                "Metadata filtering engine initialized"
            )

            # -----------------------------------------------------------------
            # INITIALIZE HYBRID RETRIEVER
            # -----------------------------------------------------------------

            self.hybrid_retriever = HybridRetriever()

            logger.info(
                "Hybrid retriever initialized"
            )

            logger.info(
                "InvoiceInferencePipeline initialized successfully"
            )

        except Exception as e:

            logger.exception(
                f"Pipeline initialization failed: {str(e)}"
            )

            raise

    # =========================================================================
    # EMPTY RESPONSE
    # =========================================================================

    def _empty_response(
        self,
        message: str
    ) -> Dict[str, Any]:
        """
        Standardized empty response.
        """

        return {
            "success": False,
            "message": message,
            "query_understanding": None,
            "filtered_documents_count": 0,
            "final_answer": None,
            "retrieved_context": None
        }

    # =========================================================================
    # MAIN PIPELINE
    # =========================================================================

    def run(
        self,
        user_query: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Complete inference pipeline.
        """

        try:

            logger.info("=" * 80)

            logger.info(
                f"Starting inference pipeline "
                f"for query: {user_query}"
            )

            # -----------------------------------------------------------------
            # VALIDATE INPUT
            # -----------------------------------------------------------------

            if not user_query:

                return self._empty_response(
                    "User query is empty"
                )

            if not user_query.strip():

                return self._empty_response(
                    "User query contains only whitespace"
                )

            # -----------------------------------------------------------------
            # STEP 1: QUERY UNDERSTANDING
            # -----------------------------------------------------------------

            logger.info(
                "STEP 1: Query Understanding"
            )

            query_understanding = (
                self.query_engine.understand_query(
                    user_query
                )
            )

            logger.info(
                f"Query understanding result: "
                f"{query_understanding}"
            )

            if not query_understanding:

                return self._empty_response(
                    "Failed to understand query"
                )

            # -----------------------------------------------------------------
            # STEP 2: METADATA FILTERING
            # -----------------------------------------------------------------

            logger.info(
                "STEP 2: Metadata Filtering"
            )

            filtered_documents = (
                self.metadata_engine.filter_documents(
                    query_understanding
                )
            )

            logger.info(
                f"Metadata filtering completed | "
                f"Matched documents: "
                f"{len(filtered_documents)}"
            )

            # -----------------------------------------------------------------
            # NO MATCHES FOUND
            # -----------------------------------------------------------------

            if len(filtered_documents) == 0:

                logger.warning(
                    "No matching documents found"
                )

                return {
                    "success": True,
                    "message": (
                        "No matching invoice records found"
                    ),
                    "query_understanding": query_understanding,
                    "filtered_documents_count": 0,
                    "final_answer": (
                        "No relevant invoice information "
                        "was found."
                    ),
                    "retrieved_context": None
                }

            # -----------------------------------------------------------------
            # STEP 3: HYBRID RETRIEVAL
            # -----------------------------------------------------------------

            logger.info(
                "STEP 3: Hybrid Retrieval"
            )

            semantic_query = (
                query_understanding.get(
                    "semantic_query",
                    user_query
                )
            )

            retrieval_result = (
                self.hybrid_retriever.retrieve_and_answer(

                    user_query=user_query,

                    semantic_query=semantic_query,

                    candidate_documents=filtered_documents,

                    top_k=top_k,

                    llm_model=self.llm_model
                )
            )

            logger.info(
                "Hybrid retrieval completed successfully"
            )

            # -----------------------------------------------------------------
            # FINAL RESPONSE
            # -----------------------------------------------------------------

            final_response = {

                "success": True,

                "message": (
                    "Inference pipeline executed successfully"
                ),

                "query_understanding": query_understanding,

                "filtered_documents_count": len(
                    filtered_documents
                ),

                "dense_results_count": len(
                    retrieval_result.get(
                        "dense_results",
                        []
                    )
                ),

                "sparse_results_count": len(
                    retrieval_result.get(
                        "sparse_results",
                        []
                    )
                ),

                "fused_results_count": len(
                    retrieval_result.get(
                        "fused_results",
                        []
                    )
                ),

                "retrieved_context": retrieval_result.get(
                    "context"
                ),

                "final_answer": retrieval_result.get(
                    "final_answer"
                )
            }

            logger.info(
                "Inference pipeline completed successfully"
            )

            logger.info("=" * 80)

            return final_response

        except Exception as e:

            logger.exception(
                f"Inference pipeline failed: {str(e)}"
            )

            return {
                "success": False,
                "message": (
                    f"Pipeline execution failed: {str(e)}"
                ),
                "query_understanding": None,
                "filtered_documents_count": 0,
                "final_answer": None,
                "retrieved_context": None
            }





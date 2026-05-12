import os
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("faiss_invoice_store")


# =============================================================================
# CONFIGURATION
# =============================================================================

VECTOR_DB_DIR = Path("vectordatabase")

FAISS_INDEX_PATH = VECTOR_DB_DIR / "invoice_index.faiss"

METADATA_PATH = VECTOR_DB_DIR / "metadata.pkl"

CONFIG_PATH = VECTOR_DB_DIR / "config.json"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


# =============================================================================
# VECTOR DATABASE CLASS
# =============================================================================

class InvoiceVectorDB:
    """
    Production-grade local FAISS vector database for invoice documents.
    """

    def __init__(self):

        self.model = None
        self.index = None
        self.metadata_store: List[Dict[str, Any]] = []

        self._initialize()

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def _initialize(self) -> None:
        """
        Initializes:
        - Folder structure
        - Embedding model
        - FAISS index
        - Metadata store
        """

        try:

            logger.info("Initializing InvoiceVectorDB")

            # -----------------------------------------------------------------
            # CREATE VECTOR DATABASE DIRECTORY
            # -----------------------------------------------------------------

            VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

            logger.info(f"Vector DB directory ready: {VECTOR_DB_DIR}")

            # -----------------------------------------------------------------
            # LOAD EMBEDDING MODEL
            # -----------------------------------------------------------------

            logger.info(
                f"Loading embedding model: {EMBEDDING_MODEL_NAME}"
            )

            self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

            logger.info("Embedding model loaded successfully")

            # -----------------------------------------------------------------
            # LOAD OR CREATE FAISS INDEX
            # -----------------------------------------------------------------

            if FAISS_INDEX_PATH.exists():

                logger.info("Existing FAISS index found. Loading...")

                self.index = faiss.read_index(str(FAISS_INDEX_PATH))

                logger.info(
                    f"FAISS index loaded successfully "
                    f"with {self.index.ntotal} vectors"
                )

            else:

                logger.info("No FAISS index found. Creating new index...")

                self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)

                self._save_index()

                logger.info("New FAISS index created successfully")

            # -----------------------------------------------------------------
            # LOAD OR CREATE METADATA STORE
            # -----------------------------------------------------------------

            if METADATA_PATH.exists():

                logger.info("Loading metadata store")

                with open(METADATA_PATH, "rb") as f:
                    self.metadata_store = pickle.load(f)

                logger.info(
                    f"Loaded metadata store with "
                    f"{len(self.metadata_store)} records"
                )

            else:

                logger.info("No metadata store found. Creating new store")

                self.metadata_store = []

                self._save_metadata()

            # -----------------------------------------------------------------
            # SAVE CONFIG
            # -----------------------------------------------------------------

            self._save_config()

            logger.info("InvoiceVectorDB initialized successfully")

        except Exception as e:

            logger.exception(
                f"Failed to initialize vector database: {str(e)}"
            )

            raise

    # =========================================================================
    # SAVE OPERATIONS
    # =========================================================================

    def _save_index(self) -> None:
        """
        Saves FAISS index to disk.
        """

        try:

            faiss.write_index(self.index, str(FAISS_INDEX_PATH))

            logger.info("FAISS index saved successfully")

        except Exception as e:

            logger.exception(
                f"Failed to save FAISS index: {str(e)}"
            )

            raise

    def _save_metadata(self) -> None:
        """
        Saves metadata store to disk.
        """

        try:

            with open(METADATA_PATH, "wb") as f:
                pickle.dump(self.metadata_store, f)

            logger.info("Metadata store saved successfully")

        except Exception as e:

            logger.exception(
                f"Failed to save metadata store: {str(e)}"
            )

            raise

    def _save_config(self) -> None:
        """
        Saves DB configuration.
        """

        try:

            config = {
                "embedding_model": EMBEDDING_MODEL_NAME,
                "embedding_dimension": EMBEDDING_DIMENSION,
                "index_type": "IndexFlatL2"
            }

            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)

        except Exception as e:

            logger.warning(
                f"Failed to save config file: {str(e)}"
            )

    # =========================================================================
    # EMBEDDING
    # =========================================================================

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generates embedding for text.
        """

        try:

            if not text or not text.strip():
                raise ValueError("Input text is empty")

            embedding = self.model.encode(text)

            embedding = np.array(
                [embedding],
                dtype=np.float32
            )

            return embedding

        except Exception as e:

            logger.exception(
                f"Embedding generation failed: {str(e)}"
            )

            raise

    # =========================================================================
    # INGEST DOCUMENT
    # =========================================================================

    def ingest_document(
        self,
        document: Dict[str, Any]
    ) -> bool:
        """
        Ingests a single document into FAISS and metadata store.

        Expected document structure:
        {
            "id": "...",
            "chunk": "...",
            "metadata": {...},
            "raw_json": {...}
        }
        """

        try:

            logger.info("Starting document ingestion")

            # -----------------------------------------------------------------
            # VALIDATION
            # -----------------------------------------------------------------

            required_fields = [
                "id",
                "chunk",
                "metadata",
                "raw_json"
            ]

            for field in required_fields:

                if field not in document:
                    raise ValueError(
                        f"Missing required field: {field}"
                    )

            chunk = document["chunk"]

            if not chunk.strip():
                raise ValueError("Chunk text is empty")

            # -----------------------------------------------------------------
            # DUPLICATE CHECK
            # -----------------------------------------------------------------

            existing_ids = {
                item["id"]
                for item in self.metadata_store
            }

            if document["id"] in existing_ids:

                logger.warning(
                    f"Duplicate document skipped: {document['id']}"
                )

                return False

            # -----------------------------------------------------------------
            # GENERATE EMBEDDING
            # -----------------------------------------------------------------

            embedding = self._generate_embedding(chunk)

            # -----------------------------------------------------------------
            # ADD TO FAISS
            # -----------------------------------------------------------------

            self.index.add(embedding)

            logger.info("Vector added to FAISS index")

            # -----------------------------------------------------------------
            # STORE METADATA
            # -----------------------------------------------------------------

            metadata_entry = {
                "id": document["id"],
                "chunk": document["chunk"],
                "metadata": document["metadata"],
                "raw_json": document["raw_json"]
            }

            self.metadata_store.append(metadata_entry)

            logger.info("Metadata added successfully")

            # -----------------------------------------------------------------
            # PERSIST TO DISK
            # -----------------------------------------------------------------

            self._save_index()

            self._save_metadata()

            logger.info(
                f"Document ingested successfully: {document['id']}"
            )

            return True

        except Exception as e:

            logger.exception(
                f"Document ingestion failed: {str(e)}"
            )

            return False

    # =========================================================================
    # BULK INGEST
    # =========================================================================

    def bulk_ingest(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Bulk ingestion for multiple documents.
        """

        success = 0
        failed = 0

        logger.info(
            f"Starting bulk ingestion for {len(documents)} documents"
        )

        for doc in documents:

            try:

                result = self.ingest_document(doc)

                if result:
                    success += 1
                else:
                    failed += 1

            except Exception:

                failed += 1

        logger.info(
            f"Bulk ingestion completed | "
            f"Success: {success} | Failed: {failed}"
        )

        return {
            "success": success,
            "failed": failed
        }

    # =========================================================================
    # DATABASE STATS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns database statistics.
        """

        try:

            return {
                "total_vectors": self.index.ntotal,
                "metadata_records": len(self.metadata_store),
                "embedding_dimension": EMBEDDING_DIMENSION,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "index_path": str(FAISS_INDEX_PATH),
                "metadata_path": str(METADATA_PATH)
            }

        except Exception as e:

            logger.exception(
                f"Failed to fetch DB stats: {str(e)}"
            )

            return {}



import logging
from typing import Dict, Any, List


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("metadata_filter")


# =============================================================================
# METADATA FILTER ENGINE
# =============================================================================

class MetadataFilterEngine:
    """
    Metadata filtering layer for invoice retrieval.

    Responsibilities:
    - Exact metadata filtering
    - Search space reduction
    - Metadata validation
    - Pre-retrieval filtering
    """

    def __init__(
        self,
        metadata_store: List[Dict[str, Any]]
    ):

        self.metadata_store = metadata_store

        logger.info(
            f"MetadataFilterEngine initialized with "
            f"{len(self.metadata_store)} records"
        )

    # =========================================================================
    # NORMALIZATION
    # =========================================================================

    def _normalize_value(
        self,
        value: Any
    ) -> str:
        """
        Normalize values for comparison.
        """

        if value is None:
            return ""

        return str(value).strip().upper()

    # =========================================================================
    # FILTER VALIDATION
    # =========================================================================

    def validate_filters(
        self,
        metadata_filters: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Validates whether metadata values exist in DB.

        Example Output:
        {
            "vendor": True,
            "status": True
        }
        """

        try:

            logger.info(
                "Starting metadata validation"
            )

            validation_results = {}

            for key, value in metadata_filters.items():

                if value is None:
                    validation_results[key] = False
                    continue

                exists = any(

                    self._normalize_value(
                        doc.get("metadata", {}).get(key)
                    )
                    ==
                    self._normalize_value(value)

                    for doc in self.metadata_store
                )

                validation_results[key] = exists

            logger.info(
                f"Metadata validation completed: "
                f"{validation_results}"
            )

            return validation_results

        except Exception as e:

            logger.exception(
                f"Metadata validation failed: {str(e)}"
            )

            return {}

    # =========================================================================
    # APPLY METADATA FILTERS
    # =========================================================================

    def filter_documents(
        self,
        query_understanding: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Applies metadata filtering to reduce retrieval space.

        Input:
        {
            "metadata_filters": {
                "vendor": "ACME",
                "status": "REJECTED"
            }
        }
        """

        try:

            logger.info(
                "Starting metadata filtering"
            )

            metadata_filters = query_understanding.get(
                "metadata_filters",
                {}
            )

            # -----------------------------------------------------------------
            # NO FILTERS
            # -----------------------------------------------------------------

            if not metadata_filters:

                logger.warning(
                    "No metadata filters found. "
                    "Returning full metadata store."
                )

                return self.metadata_store

            # -----------------------------------------------------------------
            # VALIDATE FILTERS
            # -----------------------------------------------------------------

            validation_results = self.validate_filters(
                metadata_filters
            )

            invalid_filters = [

                key
                for key, exists in validation_results.items()
                if not exists
            ]

            if invalid_filters:

                logger.warning(
                    f"Invalid filters detected: {invalid_filters}"
                )

                return []

            # -----------------------------------------------------------------
            # FILTERING
            # -----------------------------------------------------------------

            filtered_documents = []

            for document in self.metadata_store:

                metadata = document.get(
                    "metadata",
                    {}
                )

                match = True

                for key, value in metadata_filters.items():

                    document_value = metadata.get(key)

                    if (
                        self._normalize_value(document_value)
                        !=
                        self._normalize_value(value)
                    ):

                        match = False
                        break

                if match:
                    filtered_documents.append(document)

            logger.info(
                f"Metadata filtering completed | "
                f"Matched documents: {len(filtered_documents)}"
            )

            return filtered_documents

        except Exception as e:

            logger.exception(
                f"Metadata filtering failed: {str(e)}"
            )

            return []

    # =========================================================================
    # GET FILTER SUMMARY
    # =========================================================================

    def get_filter_summary(
        self,
        filtered_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Returns summary of filtered documents.
        Useful for observability/debugging.
        """

        try:

            statuses = {}
            vendors = set()

            for doc in filtered_documents:

                metadata = doc.get("metadata", {})

                status = metadata.get(
                    "status",
                    "UNKNOWN"
                )

                vendor = metadata.get(
                    "vendor",
                    "UNKNOWN"
                )

                statuses[status] = (
                    statuses.get(status, 0) + 1
                )

                vendors.add(vendor)

            return {
                "total_documents": len(filtered_documents),
                "statuses": statuses,
                "vendors": list(vendors)
            }

        except Exception as e:

            logger.exception(
                f"Failed to generate filter summary: {str(e)}"
            )

            return {}



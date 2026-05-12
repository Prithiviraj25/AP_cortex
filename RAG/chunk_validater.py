import logging
from typing import Dict, Any, Tuple, List


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("chunk_validation")


# =============================================================================
# CHUNK VALIDATION ENGINE
# =============================================================================

class ChunkValidationEngine:
    """
    Validates whether a final decision is worth embedding.

    Goals:
    - Prevent garbage embeddings
    - Prevent incomplete invoice ingestion
    - Ensure retrieval quality
    - Maintain enterprise-grade vector hygiene
    """

    # -------------------------------------------------------------------------
    # REQUIRED TOP-LEVEL FIELDS
    # -------------------------------------------------------------------------

    REQUIRED_TOP_LEVEL_FIELDS = [
        "status",
        "reasoning",
        "action",
        "confidence",
        "payment_details",
        "ai_review"
    ]

    # -------------------------------------------------------------------------
    # REQUIRED PAYMENT DETAIL FIELDS
    # -------------------------------------------------------------------------

    REQUIRED_PAYMENT_FIELDS = [
        "amount",
        "vendor",
        "po_number"
    ]

    # -------------------------------------------------------------------------
    # REQUIRED AI REVIEW FIELDS
    # -------------------------------------------------------------------------

    REQUIRED_AI_REVIEW_FIELDS = [
        "summary",
        "risk_level"
    ]

    # -------------------------------------------------------------------------
    # VALID STATUSES
    # -------------------------------------------------------------------------

    VALID_STATUSES = {
        "APPROVED",
        "REJECTED",
        "FLAGGED",
        "PENDING"
    }

    # -------------------------------------------------------------------------
    # VALID RISK LEVELS
    # -------------------------------------------------------------------------

    VALID_RISK_LEVELS = {
        "LOW",
        "MEDIUM",
        "HIGH"
    }

    # =========================================================================
    # NORMALIZATION
    # =========================================================================

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """
        Checks if a value is empty.
        """

        if value is None:
            return True

        if isinstance(value, str):

            if not value.strip():
                return True

        return False

    # =========================================================================
    # MAIN VALIDATION
    # =========================================================================

    def validate(
        self,
        final_decision: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates final decision before embedding.

        Returns:
        (
            is_valid,
            validation_report
        )
        """

        try:

            logger.info(
                "Starting chunk validation"
            )

            errors: List[str] = []
            warnings: List[str] = []

            # -----------------------------------------------------------------
            # TYPE VALIDATION
            # -----------------------------------------------------------------

            if not isinstance(final_decision, dict):

                errors.append(
                    "Final decision must be a dictionary"
                )

                return False, {
                    "valid": False,
                    "errors": errors,
                    "warnings": warnings
                }

            # -----------------------------------------------------------------
            # REQUIRED TOP LEVEL FIELDS
            # -----------------------------------------------------------------

            for field in self.REQUIRED_TOP_LEVEL_FIELDS:

                if field not in final_decision:

                    errors.append(
                        f"Missing required field: {field}"
                    )

                elif self._is_empty(
                    final_decision.get(field)
                ):

                    errors.append(
                        f"Empty required field: {field}"
                    )

            # -----------------------------------------------------------------
            # STOP EARLY IF TOP LEVEL FAILED
            # -----------------------------------------------------------------

            if errors:

                logger.warning(
                    "Top-level validation failed"
                )

                return False, {
                    "valid": False,
                    "errors": errors,
                    "warnings": warnings
                }

            # -----------------------------------------------------------------
            # STATUS VALIDATION
            # -----------------------------------------------------------------

            status = str(
                final_decision.get("status", "")
            ).upper()

            if status not in self.VALID_STATUSES:

                errors.append(
                    f"Invalid status: {status}"
                )

            # -----------------------------------------------------------------
            # CONFIDENCE VALIDATION
            # -----------------------------------------------------------------

            confidence = final_decision.get(
                "confidence"
            )

            try:

                confidence = float(confidence)

                if confidence < 0 or confidence > 1:

                    errors.append(
                        "Confidence must be between 0 and 1"
                    )

                elif confidence < 0.5:

                    warnings.append(
                        "Low confidence decision"
                    )

            except Exception:

                errors.append(
                    "Invalid confidence value"
                )

            # -----------------------------------------------------------------
            # PAYMENT DETAILS VALIDATION
            # -----------------------------------------------------------------

            payment_details = final_decision.get(
                "payment_details",
                {}
            )

            if not isinstance(payment_details, dict):

                errors.append(
                    "payment_details must be a dictionary"
                )

            else:

                for field in self.REQUIRED_PAYMENT_FIELDS:

                    if field not in payment_details:

                        errors.append(
                            f"Missing payment field: {field}"
                        )

                    elif self._is_empty(
                        payment_details.get(field)
                    ):

                        errors.append(
                            f"Empty payment field: {field}"
                        )

            # -----------------------------------------------------------------
            # AMOUNT VALIDATION
            # -----------------------------------------------------------------

            amount = payment_details.get("amount")

            try:

                amount = float(amount)

                if amount <= 0:

                    errors.append(
                        "Invoice amount must be greater than 0"
                    )

            except Exception:

                errors.append(
                    "Invalid invoice amount"
                )

            # -----------------------------------------------------------------
            # AI REVIEW VALIDATION
            # -----------------------------------------------------------------

            ai_review = final_decision.get(
                "ai_review",
                {}
            )

            if not isinstance(ai_review, dict):

                errors.append(
                    "ai_review must be a dictionary"
                )

            else:

                for field in self.REQUIRED_AI_REVIEW_FIELDS:

                    if field not in ai_review:

                        errors.append(
                            f"Missing AI review field: {field}"
                        )

                    elif self._is_empty(
                        ai_review.get(field)
                    ):

                        errors.append(
                            f"Empty AI review field: {field}"
                        )

            # -----------------------------------------------------------------
            # RISK LEVEL VALIDATION
            # -----------------------------------------------------------------

            risk_level = str(
                ai_review.get(
                    "risk_level",
                    ""
                )
            ).upper()

            if risk_level not in self.VALID_RISK_LEVELS:

                errors.append(
                    f"Invalid risk level: {risk_level}"
                )

            # -----------------------------------------------------------------
            # SEMANTIC QUALITY VALIDATION
            # -----------------------------------------------------------------

            reasoning = final_decision.get(
                "reasoning",
                ""
            )

            summary = ai_review.get(
                "summary",
                ""
            )

            combined_text = (
                f"{reasoning} {summary}"
            )

            # Too short
            if len(combined_text.split()) < 10:

                warnings.append(
                    "Very short semantic content"
                )

            # Extremely long
            if len(combined_text.split()) > 1000:

                warnings.append(
                    "Very large semantic content"
                )

            # -----------------------------------------------------------------
            # DUPLICATE SIGNALS
            # -----------------------------------------------------------------

            if reasoning.strip() == summary.strip():

                warnings.append(
                    "Reasoning and summary are identical"
                )

            # -----------------------------------------------------------------
            # FINAL RESULT
            # -----------------------------------------------------------------

            is_valid = len(errors) == 0

            validation_report = {

                "valid": is_valid,

                "errors": errors,

                "warnings": warnings,

                "metadata": {
                    "status": status,
                    "risk_level": risk_level,
                    "confidence": confidence,
                    "vendor": payment_details.get(
                        "vendor"
                    ),
                    "po_number": payment_details.get(
                        "po_number"
                    )
                }
            }

            if is_valid:

                logger.info(
                    "Chunk validation successful"
                )

            else:

                logger.warning(
                    f"Chunk validation failed | "
                    f"Errors: {len(errors)}"
                )

            return is_valid, validation_report

        except Exception as e:

            logger.exception(
                f"Critical validation failure: {str(e)}"
            )

            return False, {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }



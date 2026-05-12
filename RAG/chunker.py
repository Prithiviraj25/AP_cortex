import logging
from typing import Dict, Any, Optional
from datetime import datetime


# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)



# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def safe_get(data: Dict[str, Any], key: str, default: str = "UNKNOWN") -> Any:
    """
    Safely fetch value from dictionary.
    Handles None, missing keys, and empty strings.
    """
    try:
        value = data.get(key, default)

        if value is None:
            return default

        if isinstance(value, str) and not value.strip():
            return default

        return value

    except Exception as e:
        logger.warning(f"Failed to fetch key '{key}': {str(e)}")
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    """
    try:
        if value is None:
            return default

        return float(value)

    except Exception:
        return default


# -----------------------------------------------------------------------------
# MAIN CHUNK BUILDER
# -----------------------------------------------------------------------------

def build_invoice_chunk(final_decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Builds:
    1. Semantic chunk text
    2. Metadata payload
    3. Clean document structure for FAISS ingestion

    Returns:
        dict OR None
    """

    try:

        logger.info("Starting invoice chunk generation")

        # ---------------------------------------------------------------------
        # TOP LEVEL FIELDS
        # ---------------------------------------------------------------------

        status = safe_get(final_decision, "status")
        reasoning = safe_get(final_decision, "reasoning")
        action = safe_get(final_decision, "action")
        confidence = safe_float(final_decision.get("confidence"), 0.0)

        # ---------------------------------------------------------------------
        # PAYMENT DETAILS
        # ---------------------------------------------------------------------

        payment_details = final_decision.get("payment_details", {}) or {}

        amount = safe_float(payment_details.get("amount"))
        vendor = safe_get(payment_details, "vendor")
        po_number = safe_get(payment_details, "po_number")
        payment_terms = safe_get(payment_details, "payment_terms")
        due_date = safe_get(payment_details, "due_date")

        # ---------------------------------------------------------------------
        # AI REVIEW
        # ---------------------------------------------------------------------

        ai_review = final_decision.get("ai_review", {}) or {}

        summary = safe_get(ai_review, "summary")
        risk_level = safe_get(ai_review, "risk_level")
        recommended_action = safe_get(ai_review, "recommended_action")
        reviewer_notes = safe_get(ai_review, "reviewer_notes")
        business_impact = safe_get(ai_review, "business_impact")

        # ---------------------------------------------------------------------
        # EXTRACT INVOICE NUMBER FROM REASONING/SUMMARY
        # ---------------------------------------------------------------------

        invoice_number = "UNKNOWN"

        try:
            import re

            combined_text = f"{reasoning} {summary}"

            match = re.search(r"INV-\d+", combined_text)

            if match:
                invoice_number = match.group(0)

        except Exception as e:
            logger.warning(f"Invoice number extraction failed: {str(e)}")

        # ---------------------------------------------------------------------
        # SEMANTIC CHUNK
        # ---------------------------------------------------------------------

        semantic_chunk = f"""
        Invoice {invoice_number} from vendor {vendor} linked to purchase order
        {po_number} has status {status}.

        Invoice amount is ${amount:.2f} with payment terms '{payment_terms}'.

        Due date for payment is {due_date}.

        Risk level associated with this invoice is {risk_level}.

        Recommended action is '{recommended_action}'.

        Validation reasoning:
        {reasoning}

        AI review summary:
        {summary}

        Reviewer notes:
        {reviewer_notes}

        Business impact assessment:
        {business_impact}
        """.strip()

        # Clean whitespace
        semantic_chunk = " ".join(semantic_chunk.split())

        # ---------------------------------------------------------------------
        # METADATA
        # ---------------------------------------------------------------------

        metadata = {
            "invoice_number": invoice_number,
            "vendor": vendor,
            "po_number": po_number,
            "status": status,
            "amount": amount,
            "payment_terms": payment_terms,
            "due_date": due_date,
            "risk_level": risk_level,
            "action": action,
            "recommended_action": recommended_action,
            "confidence": confidence,
            "business_impact": business_impact,
            "created_at": datetime.utcnow().isoformat()
        }

        # ---------------------------------------------------------------------
        # FINAL DOCUMENT
        # ---------------------------------------------------------------------

        document = {
            "id": f"{invoice_number}_{po_number}",
            "chunk": semantic_chunk,
            "metadata": metadata,
            "raw_json": final_decision
        }

        logger.info(
            f"Chunk successfully created for invoice: {invoice_number}"
        )

        return document

    except Exception as e:

        logger.exception(
            f"Critical failure during invoice chunk generation: {str(e)}"
        )

        return None



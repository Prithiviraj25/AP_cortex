from .database import InvoiceDatabase
from typing import Optional, Dict
from difflib import SequenceMatcher
import logging


# =========================================================
# LOGGING CONFIG
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_str(value) -> str:
    """
    Safely convert any value to cleaned string
    """

    if value is None:
        return ""

    return str(value).strip()


def safe_lower(value) -> str:
    """
    Safe lowercase conversion
    """

    return safe_str(value).lower()


def safe_float(value, default=0.0) -> float:
    """
    Safe float conversion
    """

    try:
        if value is None or value == "":
            return default

        return float(value)

    except Exception:
        return default


# =========================================================
# STRING SIMILARITY
# =========================================================

def similarity_score(str1, str2) -> float:
    """
    Calculate safe string similarity score
    between 0.0 and 1.0
    """

    str1 = safe_lower(str1)
    str2 = safe_lower(str2)

    if not str1 or not str2:
        return 0.0

    return SequenceMatcher(None, str1, str2).ratio()


# =========================================================
# MAIN MATCHING FUNCTION
# =========================================================

def find_matching_po(
    invoice_data: Dict,
    db: InvoiceDatabase
) -> Dict:
    """
    Find matching Purchase Order for invoice.

    Matching priority:
    1. Exact PO reference match
    2. Vendor + amount fuzzy matching
    3. No match

    Returns:
        dict:
        {
            po_data,
            match_type,
            confidence,
            notes
        }
    """

    try:

        # -------------------------------------------------
        # EXTRACT INVOICE FIELDS SAFELY
        # -------------------------------------------------

        po_reference = safe_str(
            invoice_data.get("po_reference")
        )

        vendor_name = safe_str(
            invoice_data.get("vendor_name")
        )

        total_amount = safe_float(
            invoice_data.get("total_amount")
        )

        invoice_number = safe_str(
            invoice_data.get("invoice_number")
        )

        logger.info(
            f"Matching invoice: {invoice_number}"
        )

        # =================================================
        # CASE 1 — EXACT PO MATCH
        # =================================================

        if po_reference:

            logger.info(
                f"Searching exact PO match: {po_reference}"
            )

            po = db.get_po_by_number(po_reference)

            if po:

                po_vendor_name = safe_str(
                    po.get("Vendor Name")
                )

                vendor_match_score = similarity_score(
                    vendor_name,
                    po_vendor_name
                )

                logger.info(
                    f"Exact PO match found: {po_reference}"
                )

                return {
                    "po_data": po,
                    "match_type": "exact",
                    "confidence": round(vendor_match_score, 4),
                    "notes": (
                        f"Exact PO match found for "
                        f"{po_reference}"
                    )
                }

            else:

                logger.warning(
                    f"PO reference not found: {po_reference}"
                )

                return {
                    "po_data": None,
                    "match_type": "not_found",
                    "confidence": 0.0,
                    "notes": (
                        f"PO reference '{po_reference}' "
                        f"not found in database"
                    )
                }

        # =================================================
        # CASE 2 — FUZZY MATCH
        # =================================================

        logger.warning(
            "No PO reference found. "
            "Attempting fuzzy match..."
        )

        fuzzy_matches = db.search_po_by_vendor_and_amount(
            vendor_name=vendor_name,
            amount=total_amount,
            tolerance=0.15
        )

        if fuzzy_matches:

            best_match = fuzzy_matches[0]

            confidence = safe_float(
                best_match.get("match_confidence")
            )

            po_number = safe_str(
                best_match.get("PO Number")
            )

            logger.info(
                f"Fuzzy match found: {po_number}"
            )

            return {
                "po_data": best_match,
                "match_type": "fuzzy",
                "confidence": round(confidence, 4),
                "notes": (
                    f"Fuzzy match found: {po_number} "
                    f"(vendor + amount similarity)"
                )
            }

        # =================================================
        # CASE 3 — NO MATCH
        # =================================================

        logger.warning(
            "No matching PO found"
        )

        return {
            "po_data": None,
            "match_type": "no_match",
            "confidence": 0.0,
            "notes": (
                f"No PO match found for vendor "
                f"'{vendor_name}' "
                f"and amount '{total_amount}'"
            )
        }

    except Exception as e:

        logger.exception(
            "Unexpected PO matching failure"
        )

        return {
            "po_data": None,
            "match_type": "error",
            "confidence": 0.0,
            "notes": f"Matching failed: {str(e)}"
        }


# =========================================================
# TESTING
# =========================================================


"""
decision.py

Hybrid invoice decision engine:
- Deterministic business rules
- AI-generated financial review layer

This module:
1. Makes deterministic approval decisions
2. Uses an LLM to generate reviewer-friendly explanations

Author: Your AP Automation System
"""

from typing import Any, Dict, List, Optional
import json
import ollama


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _safe_get(data: Optional[Dict], key: str, default=None):
    """Safely get value from dictionary."""
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def _contains_critical_issue(issues: List[str]) -> bool:
    """
    Detect critical rejection conditions.
    """

    critical_keywords = [
        "duplicate",
        "no matching po",
        "closed",
        "exceeds remaining po balance",
        "fraud",
        "critical",
        "invalid",
    ]

    for issue in issues:
        issue_lower = issue.lower()

        for keyword in critical_keywords:
            if keyword in issue_lower:
                return True

    return False


def _build_payment_details(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build payment details for approved invoices."""

    return {
        "amount": invoice_data.get("total_amount"),
        "vendor": invoice_data.get("vendor_name"),
        "po_number": invoice_data.get("po_reference"),
        "payment_terms": invoice_data.get("payment_terms"),
        "due_date": invoice_data.get("due_date"),
    }


# =====================================================================
# AI REVIEW LAYER
# =====================================================================

def generate_ai_review(
    invoice_data: Dict[str, Any],
    matched_po: Dict[str, Any],
    validation_result: Dict[str, Any],
    decision: Dict[str, Any],
    model: str = "llama3:latest",
) -> Dict[str, Any]:
    """
    Generate AI-powered financial review commentary.

    This DOES NOT make the decision.
    It only explains/analyzes the deterministic outcome.
    """

    prompt = f"""
You are a senior Accounts Payable financial analyst.

Analyze the invoice processing decision and generate:
1. Executive summary
2. Risk assessment
3. Recommended next steps
4. Human reviewer notes

IMPORTANT:
- Do NOT change the decision status
- Explain the reasoning professionally
- Keep response concise and finance-friendly
- Mention invoice numbers, PO references, and discrepancies
- Return ONLY valid JSON

INPUT DATA:

Invoice:
{json.dumps(invoice_data, indent=2)}

PO Match:
{json.dumps(matched_po, indent=2)}

Validation:
{json.dumps(validation_result, indent=2)}

Decision:
{json.dumps(decision, indent=2)}

Return JSON format:

{{
  "summary": "...",
  "risk_level": "LOW/MEDIUM/HIGH",
  "recommended_action": "...",
  "reviewer_notes": "...",
  "business_impact": "..."
}}
"""

    try:

        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        import re

        content = response["message"]["content"].strip()

        # Remove markdown fences
        content = content.replace("```json", "")
        content = content.replace("```", "").strip()

        try:
            # Extract first JSON object from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)

            if json_match:
                json_content = json_match.group(0)
                return json.loads(json_content)

            raise ValueError("No JSON object found")

        except Exception:

            return {
                "summary": content,
                "risk_level": "UNKNOWN",
                "recommended_action": "Review manually.",
                "reviewer_notes": "LLM returned non-JSON response.",
                "business_impact": "Unknown"
            }

    except Exception as e:

        return {
            "summary": "AI review generation failed.",
            "risk_level": "UNKNOWN",
            "recommended_action": "Review manually.",
            "reviewer_notes": str(e),
            "business_impact": "Unknown",
        }


# =====================================================================
# MAIN DECISION ENGINE
# =====================================================================

def make_decision(
    invoice_data: Dict[str, Any],
    matched_po: Dict[str, Any],
    validation_result: Dict[str, Any],
    use_ai_review: bool = True,
) -> Dict[str, Any]:
    """
    Main deterministic decision engine.
    """

    invoice_number = _safe_get(
        invoice_data,
        "invoice_number",
        "UNKNOWN",
    )

    vendor_name = _safe_get(
        invoice_data,
        "vendor_name",
        "UNKNOWN VENDOR",
    )

    total_amount = _safe_get(
        invoice_data,
        "total_amount",
        0.0,
    )

    match_type = _safe_get(
        matched_po,
        "match_type",
        "no_match",
    )

    confidence = float(
        _safe_get(
            matched_po,
            "confidence",
            0.0,
        )
    )

    po_data = _safe_get(
        matched_po,
        "po_data",
        {},
    )

    approved_amount = _safe_get(
        po_data,
        "Approved Amount",
    )

    po_number = _safe_get(
        po_data,
        "PO Number",
        invoice_data.get("po_reference"),
    )

    is_valid = bool(
        _safe_get(
            validation_result,
            "is_valid",
            False,
        )
    )

    issues = _safe_get(
        validation_result,
        "issues",
        [],
    ) or []

    warnings = _safe_get(
        validation_result,
        "warnings",
        [],
    ) or []

    # ==============================================================
    # REJECT
    # ==============================================================

    if not is_valid and _contains_critical_issue(issues):

        decision = {
            "status": "REJECTED",
            "reasoning": (
                f"Invoice {invoice_number} from "
                f"{vendor_name} was rejected due to "
                f"critical validation failures: "
                f"{'; '.join(issues)}"
            ),
            "action": "Do not pay",
            "confidence": 1.0,
        }

    # ==============================================================
    # FLAG
    # ==============================================================

    elif (
        warnings
        or match_type == "fuzzy"
        or confidence < 0.90
    ):

        review_reasons = []

        if match_type == "fuzzy":
            review_reasons.append(
                f"Fuzzy PO match ({confidence:.0%} confidence)"
            )

        if confidence < 0.90:
            review_reasons.append(
                f"Low PO match confidence ({confidence:.0%})"
            )

        if warnings:
            review_reasons.extend(warnings)

        decision = {
            "status": "FLAGGED_FOR_REVIEW",
            "reasoning": (
                f"Invoice {invoice_number} requires "
                f"manual review: "
                f"{'; '.join(review_reasons)}"
            ),
            "action": "Review and approve manually",
            "confidence": round(
                min(confidence, 0.95),
                2,
            ),
            "suggested_actions": [
                "Verify PO reference",
                "Review validation warnings",
                "Confirm invoice accuracy",
            ],
        }

    # ==============================================================
    # APPROVE
    # ==============================================================

    else:

        decision = {
            "status": "APPROVED",
            "reasoning": (
                f"Invoice {invoice_number} matches "
                f"{po_number}. Amount "
                f"${total_amount:.2f} within approved "
                f"${approved_amount:.2f}. "
                f"All validations passed."
            ),
            "action": "Proceed to payment",
            "confidence": 1.0,
            "payment_details": _build_payment_details(
                invoice_data
            ),
        }

    # ==============================================================
    # AI REVIEW
    # ==============================================================

    if use_ai_review:

        ai_review = generate_ai_review(
            invoice_data=invoice_data,
            matched_po=matched_po,
            validation_result=validation_result,
            decision=decision,
        )

        decision["ai_review"] = ai_review

    return decision


# =====================================================================
# TESTING
# =====================================================================

if __name__ == "__main__":

    invoice_data = {
        "invoice_number": "INV-5567",
        "vendor_name": "TECHVENDOR INC.",
        "po_reference": "PO-2847",
        "total_amount": 123.90,
        "invoice_date": "2026-03-22",
        "due_date": "2026-04-21",
        "payment_terms": "Net 30 Days",
    }

    matched_po = {
        "po_data": {
            "PO Number": "PO-2847",
            "Vendor Name": "TechVendor Inc.",
            "Approved Amount": 120.00,
            "Status": "Open",
        },
        "match_type": "fuzzy",
        "confidence": 0.85,
        "notes": "Vendor fuzzy match",
    }

    validation_result = {
        "is_valid": True,
        "issues": [],
        "warnings": [
            "Amount exceeds PO by $3.90 (3.25%)"
        ],
        "checks_passed": [
            "Vendor partially matched"
        ],
    }

    final_result = make_decision(
        invoice_data,
        matched_po,
        validation_result,
        use_ai_review=True,
    )

    print(json.dumps(final_result, indent=2))
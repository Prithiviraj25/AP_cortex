import json
import logging
import re
from typing import Dict, Any, Optional

import ollama


# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)



# =============================================================================
# QUERY UNDERSTANDING ENGINE
# =============================================================================

class QueryUnderstandingEngine:
    """
    LLM-powered query understanding layer for enterprise invoice retrieval.

    Responsibilities:
    - Intent extraction
    - Entity extraction
    - Metadata filter extraction
    - Semantic query generation
    """

    def __init__(
        self,
        model: str = "qwen2.5:3b"
    ):

        self.model = model

        logger.info(
            f"QueryUnderstandingEngine initialized "
            f"with model: {self.model}"
        )

    # =========================================================================
    # PROMPT BUILDER
    # =========================================================================

    def _build_prompt(
        self,
        user_query: str
    ) -> str:
        """
        Builds structured extraction prompt.
        """

        prompt = f"""
You are an enterprise invoice retrieval query parser.

Your task is to analyze the user query and extract:

1. intent
2. invoice_number
3. po_number
4. vendor
5. status
6. risk_level
7. semantic_query
8. metadata_filters

Return ONLY valid JSON.

IMPORTANT RULES:
- Do not hallucinate values.
- Use null if not found.
- semantic_query should contain the semantic meaning of the query.
- metadata_filters should only contain fields that actually exist.
- status must be one of:
  APPROVED, REJECTED, FLAGGED, PENDING
- risk_level must be one of:
  LOW, MEDIUM, HIGH

EXAMPLES:

User Query:
"Show rejected invoices from ACME related to amount mismatch"

Output:
{{
    "intent": "invoice_search",
    "invoice_number": null,
    "po_number": null,
    "vendor": "ACME",
    "status": "REJECTED",
    "risk_level": null,
    "semantic_query": "amount mismatch invoices",
    "metadata_filters": {{
        "vendor": "ACME",
        "status": "REJECTED"
    }}
}}

User Query:
"Why was INV-8473 rejected?"

Output:
{{
    "intent": "invoice_explanation",
    "invoice_number": "INV-8473",
    "po_number": null,
    "vendor": null,
    "status": null,
    "risk_level": null,
    "semantic_query": "reason for invoice rejection",
    "metadata_filters": {{
        "invoice_number": "INV-8473"
    }}
}}

Now analyze this query:

User Query:
"{user_query}"
"""

        return prompt.strip()

    # =========================================================================
    # JSON CLEANER
    # =========================================================================

    def _extract_json(
        self,
        text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extracts JSON safely from LLM response.
        """

        try:

            # Remove markdown blocks if present
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)

            text = text.strip()

            # Find JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)

            if not match:

                logger.error("No JSON object found in response")

                return None

            json_text = match.group(0)

            parsed = json.loads(json_text)

            return parsed

        except json.JSONDecodeError as e:

            logger.error(
                f"Failed to parse JSON response: {str(e)}"
            )

            logger.debug(f"Raw response: {text}")

            return None

        except Exception as e:

            logger.exception(
                f"Unexpected JSON extraction error: {str(e)}"
            )

            return None

    # =========================================================================
    # FALLBACK EXTRACTION
    # =========================================================================

    def _fallback_extraction(
        self,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Regex-based fallback if LLM fails.
        """

        logger.warning(
            "Using fallback extraction mechanism"
        )

        invoice_match = re.search(
            r"INV-\d+",
            user_query,
            re.IGNORECASE
        )

        po_match = re.search(
            r"PO-\d+",
            user_query,
            re.IGNORECASE
        )

        status = None

        query_upper = user_query.upper()

        possible_statuses = [
            "APPROVED",
            "REJECTED",
            "FLAGGED",
            "PENDING"
        ]

        for s in possible_statuses:

            if s in query_upper:
                status = s
                break

        return {
            "intent": "invoice_search",
            "invoice_number": (
                invoice_match.group(0)
                if invoice_match else None
            ),
            "po_number": (
                po_match.group(0)
                if po_match else None
            ),
            "vendor": None,
            "status": status,
            "risk_level": None,
            "semantic_query": user_query,
            "metadata_filters": {}
        }

    # =========================================================================
    # MAIN QUERY UNDERSTANDING
    # =========================================================================

    def understand_query(
        self,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Main query understanding pipeline.
        """

        try:

            logger.info(
                f"Processing user query: {user_query}"
            )

            if not user_query or not user_query.strip():

                raise ValueError("User query is empty")

            # -----------------------------------------------------------------
            # BUILD PROMPT
            # -----------------------------------------------------------------

            prompt = self._build_prompt(user_query)

            logger.info("Prompt generated successfully")

            # -----------------------------------------------------------------
            # LLM INFERENCE
            # -----------------------------------------------------------------

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            logger.info("LLM response received")

            response_text = response["message"]["content"]

            logger.debug(f"Raw LLM response: {response_text}")

            # -----------------------------------------------------------------
            # PARSE JSON
            # -----------------------------------------------------------------

            parsed_response = self._extract_json(
                response_text
            )

            if parsed_response is None:

                logger.warning(
                    "LLM JSON parsing failed. "
                    "Using fallback extraction."
                )

                return self._fallback_extraction(
                    user_query
                )

            logger.info(
                "Query understanding completed successfully"
            )

            return parsed_response

        except Exception as e:

            logger.exception(
                f"Query understanding failed: {str(e)}"
            )

            return self._fallback_extraction(
                user_query
            )



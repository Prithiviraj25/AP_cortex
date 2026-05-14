import ollama
import json
import re
from pathlib import Path


def clean_json_response(response_text):
    """
    Clean markdown/code block formatting from LLM response
    """
    response_text = response_text.strip()

    # Remove ```json
    if response_text.startswith("```json"):
        response_text = response_text[7:]

    # Remove ```
    if response_text.startswith("```"):
        response_text = response_text[3:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    return response_text.strip()


def validate_extraction(data):
    """
    Validate extracted invoice data
    """
    warnings = []

    # Critical field checks
    if not data.get("invoice_number"):
        warnings.append("Missing invoice number")

    if not data.get("vendor_name"):
        warnings.append("Missing vendor name")

    if not data.get("total_amount"):
        warnings.append("Missing total amount")

    if not data.get("po_reference"):
        warnings.append("Missing PO reference - fuzzy matching may be required")

    # Amount validation
    subtotal = data.get("subtotal")
    tax = data.get("tax")
    total = data.get("total_amount")

    if subtotal is not None and tax is not None and total is not None:
        calculated_total = subtotal + tax

        if abs(calculated_total - total) > 0.01:
            warnings.append(
                f"Amount mismatch: subtotal + tax = {calculated_total}, but total = {total}"
            )

    return warnings


def structure_invoice_data(markdown_text, model="qwen2.5:7b"):
    """
    Convert invoice markdown text into structured JSON using local Ollama

    Args:
        markdown_text (str): Extracted markdown content
        model (str): Ollama model name

    Returns:
        dict: Structured invoice JSON
    """

    prompt = f"""
You are an invoice data extraction assistant.

Extract invoice information from the given markdown and return ONLY valid JSON.

RULES:
1. Extract all fields accurately
2. Normalize dates to YYYY-MM-DD format
3. Convert monetary values into float numbers
4. Remove currency symbols
5. If data is missing, use null
6. Do NOT hallucinate values
8. if the passed markdown is OCR scanned EG: it will begin with similar line like '''![image 1](<tmp80041wl5_images/imageFile1.png>)''' then try to contruct the json with more
precaution as the md might have broken tables and missing values, in such cases try to use the context of the invoice to fill in the values, if you are not sure about any value then put null for that field
7. Return ONLY raw JSON

JSON FORMAT:
{{
  "vendor_name": string,
  "vendor_tax_id": string or null,
  "vendor_contact": string or null,
  "invoice_number": string,
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD" or null,
  "po_reference": string or null,
  "bill_to": {{
    "company": string,
    "address": string
  }},
  "line_items": [
    {{
      "description": string,
      "quantity": string,
      "unit_price": float,
      "amount": float
    }}
  ],
  "subtotal": float,
  "tax": float,
  "tax_rate": float or null,
  "total_amount": float,
  "currency": string,
  "payment_terms": string or null,
  "payment_instructions": string or null
}}

INVOICE MARKDOWN:
{markdown_text}

Return ONLY JSON:
"""

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={ "temperature": 0.35}
        )

        response_text = response["message"]["content"]

        # Clean markdown formatting
        response_text = clean_json_response(response_text)

        # Extract JSON safely
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if not json_match:
            raise ValueError("No valid JSON found in model response")

        json_text = json_match.group(0)

        structured_data = json.loads(json_text)

        # Add metadata
        structured_data["extraction_metadata"] = {
            "extraction_method": "ollama_llama3",
            "model": model,
            "warnings": validate_extraction(structured_data)
        }

        return structured_data

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        raise

import ollama
import json
import re
from json_repair import repair_json


def structure_scanned_invoice_data(ocr_text, model="qwen2.5:7b"):
    """
    Convert EasyOCR extracted invoice text into structured JSON.

    Args:
        ocr_text (str): Raw OCR extracted text from EasyOCR
        model (str): Ollama model name

    Returns:
        dict: Structured invoice data
    """

    prompt = f"""
You are an expert invoice reconstruction and extraction system.

The input is RAW LINE-BY-LINE OCR TEXT extracted from a scanned invoice.

IMPORTANT:
The OCR process has DESTROYED the original visual layout.

This means:
- table columns are broken
- rows may appear vertically instead of horizontally
- nearby values may be separated
- headers and values may not be adjacent
- line ordering may be imperfect
- duplicated OCR text may exist
- words may be partially corrupted

Your FIRST task is to mentally reconstruct the ORIGINAL 2D invoice layout.

Think carefully about:
- which values belong in the same row
- which text belongs to headers
- which numbers correspond to quantities/prices/totals
- nearby semantic relationships
- invoice table structure
- repeated OCR artifacts

After reconstructing the probable invoice layout,
extract the invoice into structured JSON.

IMPORTANT EXTRACTION RULES:
1. Return ONLY raw JSON
2. Use valid JSON parsable by Python json.loads()
3. Use DOUBLE quotes only
4. No markdown
5. No explanations
6. No trailing commas
7. Normalize dates to YYYY-MM-DD
8. Monetary values must be float
9. Remove currency symbols from numbers
10. If uncertain use null
11. NEVER hallucinate missing values
12. Infer table rows carefully from context
13. Ignore duplicated OCR lines when necessary
14. Reconstruct table rows semantically, not line-by-line

EXAMPLE OF HOW OCR MAY BE BROKEN:

BAD OCR:
Item A
20 pcs
10.00
200.00

REAL TABLE ROW:
Description: Item A
Quantity: 20 pcs
Unit Price: 10.00
Amount: 200.00

ANOTHER EXAMPLE:

BAD OCR:
Invoice
Number
7578765

REAL VALUE:
invoice_number = 7578765

EXPECTED JSON FORMAT:
{{
  "vendor_name": string,
  "vendor_tax_id": string or null,
  "vendor_contact": string or null,
  "invoice_number": string or null,
  "invoice_date": "YYYY-MM-DD" or null,
  "due_date": "YYYY-MM-DD" or null,
  "po_reference": string or null,

  "bill_to": {{
    "company": string or null,
    "address": string or null
  }},

  "line_items": [
    {{
      "description": string,
      "quantity": string or null,
      "unit_price": float or null,
      "amount": float or null,
      "tax_rate": float or null
    }}
  ],

  "subtotal": float or null,
  "tax": float or null,
  "tax_rate": float or null,
  "total_amount": float or null,
  "currency": string or null,
  "payment_terms": string or null,
  "payment_instructions": string or null
}}

RAW OCR INPUT:
{ocr_text}

Return ONLY VALID JSON:
"""
    try:

        response = ollama.chat(
            model=model,
            format="json",   # IMPORTANT
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={ "temperature": 0.35}
        )

        response_text = response["message"]["content"].strip()

        # Remove markdown wrappers if model adds them
        response_text = response_text.replace("```json", "")
        response_text = response_text.replace("```", "").strip()

        # Extract JSON safely
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if not json_match:
            raise ValueError("No valid JSON found in model response")

        json_text = json_match.group(0)

        # Try parsing directly
        try:
            structured_data = json.loads(json_text)

        except json.JSONDecodeError:
            print("⚠️ Malformed JSON detected. Repairing...")

            fixed_json = repair_json(json_text)

            structured_data = json.loads(fixed_json)

        # Add metadata
        structured_data["extraction_metadata"] = {
            "extraction_method": "easyocr_ollama",
            "model": model,
            "ocr_input": True,
            "warnings": validate_extraction(structured_data)
        }

        return structured_data

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        raise

def extract_invoice_from_markdown_file(markdown_file_path, output_json_path=None):
    """
    Read markdown file and extract structured invoice JSON

    Args:
        markdown_file_path (str): Path to markdown file
        output_json_path (str): Optional path to save JSON

    Returns:
        dict: Extracted invoice data
    """

    markdown_file_path = Path(markdown_file_path)

    if not markdown_file_path.exists():
        raise FileNotFoundError(f"File not found: {markdown_file_path}")

    # Read markdown content
    with open(markdown_file_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # Extract structured invoice
    structured_data = structure_invoice_data(markdown_text)

    # Save JSON if output path provided
    if output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2)

        print(f"✅ JSON saved to: {output_json_path}")

    return structured_data


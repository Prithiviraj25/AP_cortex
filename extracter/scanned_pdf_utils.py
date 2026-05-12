import fitz  # PyMuPDF


def is_scanned_pdf(pdf_path, min_text_chars=50):
    """
    Detect whether a PDF is scanned or digital.

    Args:
        pdf_path (str): Path to PDF
        min_text_chars (int): Minimum extracted text threshold

    Returns:
        bool:
            True  -> scanned PDF (needs OCR)
            False -> digital PDF
    """

    doc = fitz.open(pdf_path)

    extracted_text = ""

    for page in doc:
        extracted_text += page.get_text()

    extracted_text = extracted_text.strip()

    
    return len(extracted_text) < min_text_chars


import logging
from pathlib import Path
import opendataloader_pdf

# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)




def extract_pdf_to_json(
    pdf_path: str,
    output_dir: str = "output",
    hybrid: str = "docling-fast",
    hybrid_mode: str = "full"
) -> str:
    """
    Extract structured JSON from a PDF using opendataloader_pdf.

    Args:
        pdf_path (str): Path to source PDF
        output_dir (str): Directory where outputs are stored
        hybrid (str): OCR backend
        hybrid_mode (str): OCR mode

    Returns:
        str: Path to generated JSON file
    """

    try:
        logger.info("Starting PDF extraction process")

        # ----------------------------------------
        # VALIDATE INPUT PDF
        # ----------------------------------------

        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(
                f"PDF file not found: {pdf_path}"
            )

        if pdf_file.suffix.lower() != ".pdf":
            raise ValueError(
                "Input file must be a PDF"
            )

        logger.info(f"Input PDF: {pdf_file}")

        # ----------------------------------------
        # CREATE OUTPUT DIRECTORY
        # ----------------------------------------

        output_path = Path(output_dir)

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        logger.info(f"Output directory: {output_path}")

        # ----------------------------------------
        # RUN EXTRACTION
        # ----------------------------------------

        logger.info("Running opendataloader_pdf.convert()")

        opendataloader_pdf.convert(
            input_path=[str(pdf_file)],
            output_dir=str(output_path),
            format="json",
            hybrid=hybrid,
            hybrid_mode=hybrid_mode
        )

        logger.info("Extraction completed successfully")

        # ----------------------------------------
        # EXPECTED JSON FILE
        # ----------------------------------------

        json_file = output_path / f"{pdf_file.stem}.json"

        if not json_file.exists():
            raise FileNotFoundError(
                f"JSON file was not generated: {json_file}"
            )

        logger.info(f"JSON generated: {json_file}")

        return str(json_file)

    except FileNotFoundError as e:

        logger.error(f"File Error: {e}")
        raise

    except ValueError as e:

        logger.error(f"Validation Error: {e}")
        raise

    except Exception as e:

        logger.exception("Unexpected extraction failure")

        raise RuntimeError(
            f"Failed to extract JSON from PDF: {e}"
        )


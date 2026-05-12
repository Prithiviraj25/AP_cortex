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


# ---------------------------------------------------
# PDF → Markdown Extraction Function
# ---------------------------------------------------
def extract_pdf_to_markdown(
    pdf_path: str,
    output_dir: str = "output",
    hybrid: str = "docling-fast",
    hybrid_mode: str = "full"
) -> str:
    """
    Extract markdown from a PDF using opendataloader_pdf.

    Args:
        pdf_path (str): Path to source PDF
        output_dir (str): Directory where outputs are stored
        hybrid (str): OCR backend
        hybrid_mode (str): OCR mode

    Returns:
        str: Path to generated markdown file
    """

    try:
        logger.info("Starting PDF extraction process")

        # Validate input PDF
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if pdf_file.suffix.lower() != ".pdf":
            raise ValueError("Input file must be a PDF")

        logger.info(f"Input PDF: {pdf_file}")

        # Create output directory if missing
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Output directory: {output_path}")

        # Run extraction
        logger.info("Running opendataloader_pdf.convert()")

        opendataloader_pdf.convert(
            input_path=[str(pdf_file)],
            output_dir=str(output_path),
            format="markdown",
            hybrid=hybrid,
            hybrid_mode=hybrid_mode
        )

        logger.info("Extraction completed successfully")

        # Expected markdown filename
        markdown_file = output_path / f"{pdf_file.stem}.md"

        if not markdown_file.exists():
            raise FileNotFoundError(
                f"Markdown file was not generated: {markdown_file}"
            )

        logger.info(f"Markdown generated: {markdown_file}")

        return str(markdown_file)

    except FileNotFoundError as e:
        logger.error(f"File Error: {e}")
        raise

    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        raise

    except Exception as e:
        logger.exception("Unexpected extraction failure")
        raise RuntimeError(
            f"Failed to extract markdown from PDF: {e}"
        )



from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
from pathlib import Path
import pandas as pd
from typing import Dict, Any
import json

# Your existing imports
from RAG.chunker import build_invoice_chunk
from extracter.pdf_extracter import extract_pdf_to_markdown
from extracter.md_to_json import extract_invoice_from_markdown_file
from validation.database import InvoiceDatabase
from validation.matcher import find_matching_po
from validation.validator import validate_invoice
from validation.decision import make_decision
from extracter.scanned_pdf_utils import is_scanned_pdf,extract_pdf_to_json
from extracter.scanned_context_builder import extract_invoice_with_context
from extracter.md_to_json import   structure_scanned_invoice_data
from RAG.chunk_validater import ChunkValidationEngine
from RAG.chunker import build_invoice_chunk
from RAG.embedder import InvoiceVectorDB
from pydantic import BaseModel
from inference.inference import InvoiceInferencePipeline
import logging
# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


vector_db = InvoiceVectorDB()

# =========================================================
# FASTAPI APP INITIALIZATION
# =========================================================

app = FastAPI(
    title="Invoice Intelligence API",
    description="AI-powered invoice processing backend",
    version="1.0.0"
)

# =========================================================
# CORS MIDDLEWARE (Allow React Frontend)
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3000",
        "http://192.168.29.160:3000",
        ["*"],
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# GLOBAL STATE (for database caching)
# =========================================================

cached_database_path = None

# =========================================================
# GLOBAL INFERENCE PIPELINE
# =========================================================

try:

    inference_pipeline = InvoiceInferencePipeline(
        llm_model="qwen2.5:3b"
    )

    logger.info(
        "Inference pipeline initialized successfully"
    )

except Exception as e:

    logger.exception(
        f"Failed to initialize inference pipeline: {str(e)}"
    )

    inference_pipeline = None

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def serialize_result(obj: Any) -> Any:
    """Convert numpy/pandas types to JSON-serializable types"""
    if isinstance(obj, dict):
        return {k: serialize_result(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_result(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    elif pd.isna(obj):
        return None
    else:
        return obj
    
# =========================================================
# REQUEST MODELS
# =========================================================

class QueryRequest(BaseModel):

    user_query: str

    top_k: int = 3
# =========================================================
# API ENDPOINTS
# =========================================================


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Invoice Intelligence API is running",
        "version": "1.0.0"
    }

@app.post("/api/process-invoice")
async def process_invoice(
    invoice_pdf: UploadFile = File(...),
    database_excel: UploadFile = File(None)
):
    """
    Main endpoint to process invoice
    
    Accepts:
    - invoice_pdf: Invoice PDF file (required)
    - database_excel: Excel file with Purchase Orders and Payment History (optional - will use cached if not provided)
    
    Returns:
    - Complete processing result with decision
    """
    
    global cached_database_path
    
    try:
        # Validate file types
        if not invoice_pdf.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Invoice must be a PDF file")
        
        # Determine which database to use
        if database_excel and database_excel.filename:
            # Use uploaded database file
            if not database_excel.filename.endswith(('.xlsx', '.xls')):
                raise HTTPException(status_code=400, detail="Database must be an Excel file")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel:
                content = await database_excel.read()
                tmp_excel.write(content)
                temp_excel_path = tmp_excel.name
        elif cached_database_path and Path(cached_database_path).exists():
            # Use cached database file
            temp_excel_path = str(cached_database_path)
        else:
            raise HTTPException(status_code=400, detail="No database provided. Please upload a database first via /api/upload-database")
        
        # Save uploaded invoice temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            content = await invoice_pdf.read()
            tmp_pdf.write(content)
            temp_pdf_path = tmp_pdf.name
        
        # Create output directory
        output_dir = "parsed"
        Path(output_dir).mkdir(exist_ok=True)
        
        # STEP 1: Extract invoice data from scanned and unscanned
        if is_scanned_pdf(temp_pdf_path):
            json_output_path=extract_pdf_to_json(temp_pdf_path)
            context_to_llm=extract_invoice_with_context(json_output_path)
            invoice_json=structure_scanned_invoice_data(context_to_llm)
        else:
            path_to_md = extract_pdf_to_markdown(temp_pdf_path, output_dir)
            invoice_json = extract_invoice_from_markdown_file(path_to_md)
        
        # STEP 2: Load database and match PO
        db = InvoiceDatabase(temp_excel_path)
        matched_po = find_matching_po(invoice_json, db)
        
        # STEP 3: Validate invoice
        validation_result = validate_invoice(invoice_json, matched_po, db)
        
        # STEP 4: Make decision
        final_decision = make_decision(
            invoice_json, 
            matched_po, 
            validation_result,
            use_ai_review=True
        )
        # step to index the data
        validator = ChunkValidationEngine()
        is_valid, report = validator.validate(
        final_decision
        ) 
        if is_valid:
            chunk = build_invoice_chunk(final_decision)
            vector_db.ingest_document(chunk)
            logger.info("Invoice chunk added to vector database")
        else:
            logger.warning("Invoice chunk failed validation and will not be indexed")
            logger.warning(f"Validation report: {report}")
        
        # Serialize results (convert pandas/numpy types to JSON-safe types)
        result = {
            "invoice": serialize_result(invoice_json),
            "po_match": serialize_result(matched_po),
            "validation": serialize_result(validation_result),
            "decision": serialize_result(final_decision),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Clean up temp files (only delete PDF, keep cached Excel)
        Path(temp_pdf_path).unlink(missing_ok=True)
        
        # Only delete temporary Excel if it wasn't from cache
        if database_excel and database_excel.filename:
            Path(temp_excel_path).unlink(missing_ok=True)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-database")
async def upload_database(
    database_excel: UploadFile = File(...)
):
    """
    Upload and cache database file
    
    This endpoint allows frontend to upload database once
    and reuse it for multiple invoice processing requests
    """
    
    global cached_database_path
    
    try:
        # Validate file type
        if not database_excel.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Database must be an Excel file")
        
        # Save to persistent location
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        
        cached_database_path = cache_dir / "database.xlsx"
        
        with open(cached_database_path, "wb") as f:
            content = await database_excel.read()
            f.write(content)
        
        # Load and return summary
        xls = pd.ExcelFile(cached_database_path)
        po_df = pd.read_excel(xls, sheet_name='Purchase Orders')
        payment_df = pd.read_excel(xls, sheet_name='Payment History')
        
        return {
            "status": "success",
            "message": "Database uploaded successfully",
            "summary": {
                "purchase_orders": len(po_df),
                "payment_records": len(payment_df),
                "vendors": po_df["Vendor Name"].nunique() if "Vendor Name" in po_df.columns else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/po-database")
async def get_po_database():
    """
    Get Purchase Orders data
    
    Returns the Purchase Orders from uploaded database
    """
    
    try:
        if cached_database_path is None or not Path(cached_database_path).exists():
            raise HTTPException(status_code=404, detail="No database uploaded. Please upload database first.")
        
        xls = pd.ExcelFile(cached_database_path)
        po_df = pd.read_excel(xls, sheet_name='Purchase Orders')
        
        # Convert to JSON-safe format
        po_data = po_df.to_dict(orient='records')
        po_data = serialize_result(po_data)
        
        return {
            "data": po_data,
            "total": len(po_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment-history")
async def get_payment_history():
    """
    Get Payment History data
    
    Returns the Payment History from uploaded database
    """
    
    try:
        if cached_database_path is None or not Path(cached_database_path).exists():
            raise HTTPException(status_code=404, detail="No database uploaded. Please upload database first.")
        
        xls = pd.ExcelFile(cached_database_path)
        payment_df = pd.read_excel(xls, sheet_name='Payment History')
        
        # Convert to JSON-safe format
        payment_data = payment_df.to_dict(orient='records')
        payment_data = serialize_result(payment_data)
        
        return {
            "data": payment_data,
            "total": len(payment_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_analytics():
    """
    Get analytics data
    
    Returns aggregated analytics from PO and Payment data
    """
    
    try:
        if cached_database_path is None or not Path(cached_database_path).exists():
            raise HTTPException(status_code=404, detail="No database uploaded. Please upload database first.")
        
        xls = pd.ExcelFile(cached_database_path)
        po_df = pd.read_excel(xls, sheet_name='Purchase Orders')
        payment_df = pd.read_excel(xls, sheet_name='Payment History')
        
        # Calculate analytics
        analytics = {
            "overview": {
                "total_pos": int(len(po_df)),
                "total_payments": int(len(payment_df)),
                "total_committed": float(po_df['Approved Amount'].sum()) if 'Approved Amount' in po_df.columns else 0,
                "total_spent": float(payment_df['Invoice Amount'].sum()) if 'Invoice Amount' in payment_df.columns else 0,
                "active_vendors": int(po_df['Vendor Name'].nunique()) if 'Vendor Name' in po_df.columns else 0
            },
            "po_by_status": po_df['Status'].value_counts().to_dict() if 'Status' in po_df.columns else {},
            "top_vendors": (
                po_df.groupby('Vendor Name')['Approved Amount']
                .sum()
                .nlargest(10)
                .to_dict()
            ) if 'Vendor Name' in po_df.columns and 'Approved Amount' in po_df.columns else {},
            "payment_methods": payment_df['Payment Method'].value_counts().to_dict() if 'Payment Method' in payment_df.columns else {}
        }
        
        # Serialize (convert numpy types)
        analytics = serialize_result(analytics)
        
        return analytics
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clear-cache")
async def clear_cache():
    """
    Clear cached database
    """
    
    global cached_database_path
    
    try:
        if cached_database_path and Path(cached_database_path).exists():
            Path(cached_database_path).unlink()
        
        cached_database_path = None
        
        return {
            "status": "success",
            "message": "Cache cleared"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_invoice_system(
    request: QueryRequest
):
    """
    Enterprise invoice intelligence query endpoint.

    Accepts:
    - user_query: Natural language query
    - top_k: Number of retrieval results

    Returns:
    - Query understanding
    - Retrieved context
    - Final LLM answer
    """

    try:

        logger.info("=" * 80)

        logger.info(
            f"Received inference query: "
            f"{request.user_query}"
        )

        # -------------------------------------------------
        # VALIDATE PIPELINE
        # -------------------------------------------------

        if inference_pipeline is None:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Inference pipeline is not initialized"
                )
            )

        # -------------------------------------------------
        # VALIDATE QUERY
        # -------------------------------------------------

        if not request.user_query:

            raise HTTPException(
                status_code=400,
                detail="User query is required"
            )

        if not request.user_query.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "User query cannot be empty"
                )
            )

        # -------------------------------------------------
        # RUN PIPELINE
        # -------------------------------------------------

        result = inference_pipeline.run(

            user_query=request.user_query,

            top_k=request.top_k
        )

        logger.info(
            "Inference query completed successfully"
        )

        logger.info("=" * 80)

        return JSONResponse(
            content=serialize_result(result)
        )

    except HTTPException:

        raise

    except Exception as e:

        logger.exception(
            f"Inference endpoint failed: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Invoice Intelligence API Server")
    print("="*60)
    print("📍 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🔄 CORS enabled for: http://localhost:3000")
    print("="*60 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True  # Auto-reload on code changes
    )
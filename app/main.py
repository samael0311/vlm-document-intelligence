"""
FastAPI Microservice for Multimodal Document & Invoice Extraction.
High-throughput REST API with automated validation, telemetry, and batching.
"""

import time
import uuid
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.invoice import (
    InvoiceData,
    InvoiceExtractionResponse,
    BatchExtractionResponse,
    ExtractionMetadata,
)
from app.preprocessors.image_processor import DocumentPreprocessor
from app.validators.consistency import InvoiceConsistencyValidator
from app.extractors import get_extractor


# In-memory metrics tracking
METRICS = {
    "total_extractions": 0,
    "successful_extractions": 0,
    "flagged_for_review": 0,
    "total_latency_ms": 0.0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up components
    print(f"[*] Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"[*] Active VLM Provider: {settings.VLM_PROVIDER.upper()}")
    yield
    # Shutdown
    print("[*] Shutting down Document Extraction Service")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade Vision-Language AI pipeline for automated invoice extraction, schema enforcement, and mathematical validation.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

preprocessor = DocumentPreprocessor()
validator = InvoiceConsistencyValidator()


@app.get("/health", tags=["System"])
async def health_check():
    """Returns service health, active VLM provider, and version."""
    avg_latency = (
        (METRICS["total_latency_ms"] / METRICS["total_extractions"])
        if METRICS["total_extractions"] > 0
        else 0.0
    )
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
        "vlm_provider": settings.VLM_PROVIDER,
        "metrics": {
            "total_processed": METRICS["total_extractions"],
            "review_flag_rate": (
                round(METRICS["flagged_for_review"] / METRICS["total_extractions"], 3)
                if METRICS["total_extractions"] > 0
                else 0.0
            ),
            "average_latency_ms": round(avg_latency, 2),
        },
    }


@app.post(
    "/api/v1/extract",
    response_model=InvoiceExtractionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Extraction"],
)
async def extract_invoice(
    file: UploadFile = File(..., description="PDF invoice or Image (PNG, JPG, TIFF)"),
    provider: Optional[str] = Form(None, description="Optional override: 'mock', 'openai', or 'qwen'"),
):
    """
    Extracts structured fields from an uploaded invoice document.
    Performs image normalization, VLM inference, and deterministic math consistency validation.
    """
    start_time = time.perf_counter()
    doc_id = str(uuid.uuid4())
    filename = file.filename or "unknown_document"

    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # 1. Preprocess & slice document
        images = preprocessor.process_file_bytes(file_bytes, filename)
        if not images:
            raise HTTPException(status_code=400, detail="Failed to render any pages from file.")

        # 2. Invoke VLM Extractor
        extractor = get_extractor(provider)
        invoice_data, confidence = await extractor.extract(images)

        # 3. Post-Extraction Consistency & Arithmetic Validation
        arithmetic_valid, review_required, reasons = validator.validate(invoice_data)

        # Flag if confidence is below threshold
        if confidence < settings.CONFIDENCE_THRESHOLD:
            review_required = True
            reasons.append(
                f"Model confidence ({confidence:.2f}) below threshold ({settings.CONFIDENCE_THRESHOLD:.2f})"
            )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Update metrics
        METRICS["total_extractions"] += 1
        METRICS["successful_extractions"] += 1
        METRICS["total_latency_ms"] += latency_ms
        if review_required:
            METRICS["flagged_for_review"] += 1

        metadata = ExtractionMetadata(
            model_name=provider or settings.VLM_PROVIDER,
            latency_ms=latency_ms,
            pages_processed=len(images),
            confidence_score=confidence,
            arithmetic_valid=arithmetic_valid,
            review_required=review_required,
            review_reasons=reasons,
        )

        return InvoiceExtractionResponse(
            success=True,
            document_id=doc_id,
            filename=filename,
            data=invoice_data,
            metadata=metadata,
            errors=[],
        )

    except HTTPException:
        raise
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        METRICS["total_extractions"] += 1
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "document_id": doc_id,
                "filename": filename,
                "data": None,
                "metadata": {
                    "model_name": provider or settings.VLM_PROVIDER,
                    "latency_ms": latency_ms,
                    "pages_processed": 0,
                    "confidence_score": 0.0,
                    "arithmetic_valid": False,
                    "review_required": True,
                    "review_reasons": ["Processing pipeline exception"],
                },
                "errors": [str(exc)],
            },
        )


@app.post(
    "/api/v1/validate-schema",
    tags=["Validation"],
)
async def validate_raw_schema(invoice: InvoiceData):
    """
    Validates an existing JSON payload against mathematical and business consistency rules.
    Used for re-validating manually edited invoices.
    """
    arithmetic_valid, review_required, reasons = validator.validate(invoice)
    return {
        "valid": arithmetic_valid and not review_required,
        "arithmetic_valid": arithmetic_valid,
        "review_required": review_required,
        "reasons": reasons,
        "data": invoice.model_dump(),
    }

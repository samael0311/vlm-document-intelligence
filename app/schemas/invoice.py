"""
Pydantic V2 schemas for deterministic invoice and document extraction.
Enforces strict typing, financial consistency constraints, and metadata logging.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    INR = "INR"
    JPY = "JPY"
    CHF = "CHF"
    OTHER = "OTHER"


class PartyInfo(BaseModel):
    """Details for Vendor or Customer entities."""
    name: str = Field(..., description="Legal company name or individual name")
    tax_id: Optional[str] = Field(None, description="VAT ID, EIN, GSTIN, or Tax Registration Number")
    address: Optional[str] = Field(None, description="Full billing or physical address")
    email: Optional[str] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact telephone number")
    website: Optional[str] = Field(None, description="Corporate URL")


class LineItem(BaseModel):
    """Detailed itemized row in the invoice table."""
    item_code: Optional[str] = Field(None, description="SKU, Part Number, or Catalog Code")
    description: str = Field(..., description="Description of the service or product")
    quantity: float = Field(..., ge=0.0, description="Quantity delivered or billed")
    unit_price: Decimal = Field(..., ge=Decimal("0.00"), description="Unit price per item")
    line_total: Decimal = Field(..., ge=Decimal("0.00"), description="Calculated total for this line item")
    tax_rate: Optional[float] = Field(None, description="Applicable tax percentage for this item (e.g. 18.0)")

    @field_validator("unit_price", "line_total", mode="before")
    @classmethod
    def parse_decimal(cls, v):
        if v is None:
            return Decimal("0.00")
        if isinstance(v, (float, int, str)):
            return Decimal(str(round(float(v), 2)))
        return v


class TaxDetail(BaseModel):
    """Tax breakdown item (e.g., State Sales Tax, VAT, GST)."""
    tax_type: str = Field(..., description="Tax identifier e.g. 'VAT', 'GST', 'State Tax'")
    rate_percentage: Optional[float] = Field(None, description="Tax rate percentage")
    tax_amount: Decimal = Field(..., description="Total tax amount levied")


class InvoiceData(BaseModel):
    """Standardized schema for extracted financial documents."""
    invoice_number: str = Field(..., description="Unique invoice or bill identifier")
    invoice_date: date = Field(..., description="Date when invoice was issued (YYYY-MM-DD)")
    due_date: Optional[date] = Field(None, description="Payment due date (YYYY-MM-DD)")
    purchase_order_number: Optional[str] = Field(None, description="Associated PO number if present")
    
    vendor: PartyInfo = Field(..., description="Biller / Vendor information")
    customer: PartyInfo = Field(..., description="Buyer / Client information")
    
    line_items: List[LineItem] = Field(default_factory=list, description="Itemized billing rows")
    
    subtotal: Decimal = Field(..., description="Net sum of line items before tax and discounts")
    tax_amount: Decimal = Field(default=Decimal("0.00"), description="Total tax amount")
    taxes: List[TaxDetail] = Field(default_factory=list, description="Granular tax items")
    discount_amount: Decimal = Field(default=Decimal("0.00"), description="Discount or deduction applied")
    shipping_amount: Decimal = Field(default=Decimal("0.00"), description="Freight or handling charge")
    total_amount: Decimal = Field(..., description="Final payable amount")
    
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD, description="Standard 3-letter currency code")
    payment_terms: Optional[str] = Field(None, description="Payment terms e.g. 'Net 30', 'Due on Receipt'")
    bank_account_number: Optional[str] = Field(None, description="Remittance bank account or IBAN")
    notes: Optional[str] = Field(None, description="Special instructions or remarks")

    @field_validator("subtotal", "tax_amount", "discount_amount", "shipping_amount", "total_amount", mode="before")
    @classmethod
    def parse_monetary(cls, v):
        if v is None:
            return Decimal("0.00")
        if isinstance(v, (float, int, str)):
            return Decimal(str(round(float(v), 2)))
        return v


class ExtractionMetadata(BaseModel):
    """Telemetry, audit trail, and validation confidence stats."""
    model_name: str = Field(..., description="VLM model ID used for inference")
    latency_ms: float = Field(..., description="Total inference + post-processing time in milliseconds")
    pages_processed: int = Field(default=1, description="Number of pages ingested")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall document extraction confidence")
    arithmetic_valid: bool = Field(..., description="Whether subtotal + tax - discount matches total")
    review_required: bool = Field(default=False, description="Flagged for human-in-the-loop review")
    review_reasons: List[str] = Field(default_factory=list, description="Specific anomaly or mismatch reasons")


class InvoiceExtractionResponse(BaseModel):
    """API payload response for a single document extraction."""
    success: bool = True
    document_id: str
    filename: str
    data: Optional[InvoiceData] = None
    metadata: ExtractionMetadata
    errors: List[str] = Field(default_factory=list)


class BatchExtractionResponse(BaseModel):
    """API payload response for batch processing."""
    total_documents: int
    successful: int
    failed: int
    flagged_for_review: int
    average_latency_ms: float
    results: List[InvoiceExtractionResponse]

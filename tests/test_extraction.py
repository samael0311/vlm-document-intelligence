"""
Automated unit and integration tests for VLM extraction microservice.
Validates Pydantic serialization, arithmetic consistency engine, and API routes.
"""

import pytest
from datetime import date
from decimal import Decimal
from PIL import Image

from app.schemas.invoice import InvoiceData, PartyInfo, LineItem, CurrencyEnum
from app.validators.consistency import InvoiceConsistencyValidator
from app.preprocessors.image_processor import DocumentPreprocessor
from app.extractors.mock_extractor import MockExtractor


def create_sample_invoice(
    subtotal: Decimal = Decimal("200.00"),
    tax: Decimal = Decimal("20.00"),
    discount: Decimal = Decimal("10.00"),
    total: Decimal = Decimal("210.00"),
    due_date: date = date(2026, 11, 30)
) -> InvoiceData:
    return InvoiceData(
        invoice_number="TEST-INV-001",
        invoice_date=date(2026, 11, 1),
        due_date=due_date,
        vendor=PartyInfo(name="Acme Supplies Co."),
        customer=PartyInfo(name="Globex Corp."),
        line_items=[
            LineItem(
                description="Widget Model Alpha",
                quantity=2.0,
                unit_price=Decimal("50.00"),
                line_total=Decimal("100.00")
            ),
            LineItem(
                description="Widget Model Beta",
                quantity=1.0,
                unit_price=Decimal("100.00"),
                line_total=Decimal("100.00")
            )
        ],
        subtotal=subtotal,
        tax_amount=tax,
        discount_amount=discount,
        shipping_amount=Decimal("0.00"),
        total_amount=total,
        currency=CurrencyEnum.USD
    )


def test_clean_invoice_passes_validation():
    """Verify mathematically accurate invoice generates zero review flags."""
    validator = InvoiceConsistencyValidator()
    invoice = create_sample_invoice()
    arithmetic_valid, review_required, reasons = validator.validate(invoice)

    assert arithmetic_valid is True
    assert review_required is False
    assert len(reasons) == 0


def test_subtotal_mismatch_flags_review():
    """Verify that an altered line item sum immediately triggers an arithmetic flag."""
    validator = InvoiceConsistencyValidator()
    # Declared subtotal is 200.00, but line items only sum to 200.00 while subtotal is set to 250.00
    invoice = create_sample_invoice(subtotal=Decimal("250.00"), total=Decimal("260.00"))
    arithmetic_valid, review_required, reasons = validator.validate(invoice)

    assert arithmetic_valid is False
    assert review_required is True
    assert any("Subtotal discrepancy" in r for r in reasons)


def test_grand_total_mismatch_flags_review():
    """Verify that erroneous grand total is caught by math check."""
    validator = InvoiceConsistencyValidator()
    # 200 + 20 - 10 = 210, but declared is 999.00
    invoice = create_sample_invoice(total=Decimal("999.00"))
    arithmetic_valid, review_required, reasons = validator.validate(invoice)

    assert arithmetic_valid is False
    assert review_required is True
    assert any("Grand total discrepancy" in r for r in reasons)


def test_temporal_anomaly_flag():
    """Verify due date prior to invoice date triggers human review."""
    validator = InvoiceConsistencyValidator()
    # Due date is Oct 2026, while invoice date is Nov 2026
    invoice = create_sample_invoice(due_date=date(2026, 10, 15))
    arithmetic_valid, review_required, reasons = validator.validate(invoice)

    assert review_required is True
    assert any("Due date" in r for r in reasons)


def test_image_preprocessor_resizing():
    """Verify preprocessor clamps oversized images to configured bounds."""
    preprocessor = DocumentPreprocessor(max_dim=1024)
    huge_img = Image.new("RGB", (3000, 4000), color=(255, 255, 255))
    normalized = preprocessor.normalize_image(huge_img)

    w, h = normalized.size
    assert max(w, h) == 1024
    assert normalized.mode == "RGB"


@pytest.mark.asyncio
async def test_mock_extractor_execution():
    """Verify mock extractor returns deterministic high-confidence schema."""
    extractor = MockExtractor(simulate_latency_ms=10)
    dummy_img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    data, confidence = await extractor.extract([dummy_img])

    assert data.invoice_number == "INV-2026-9842"
    assert confidence > 0.90
    assert len(data.line_items) == 3
    assert data.total_amount == Decimal("967.55")

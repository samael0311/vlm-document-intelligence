"""
Deterministic Mock VLM Extractor for local verification, CI/CD pipelines, and unit tests.
Simulates realistic extraction latencies and returns fully compliant structured data.
"""

import asyncio
from datetime import date
from decimal import Decimal
from typing import List, Tuple
from PIL import Image

from app.extractors.base import BaseExtractor
from app.schemas.invoice import InvoiceData, PartyInfo, LineItem, TaxDetail, CurrencyEnum


class MockExtractor(BaseExtractor):
    """Generates synthetic high-fidelity invoice extractions for offline testing."""

    def __init__(self, simulate_latency_ms: int = 150):
        self.simulate_latency_ms = simulate_latency_ms

    async def extract(self, images: List[Image.Image]) -> Tuple[InvoiceData, float]:
        if self.simulate_latency_ms > 0:
            await asyncio.sleep(self.simulate_latency_ms / 1000.0)

        # Realistic mock invoice data
        data = InvoiceData(
            invoice_number="INV-2026-9842",
            invoice_date=date(2026, 10, 24),
            due_date=date(2026, 11, 23),
            purchase_order_number="PO-99120",
            vendor=PartyInfo(
                name="Apex Cloud Logistics LLC",
                tax_id="US-EIN-92-3849102",
                address="100 Tech Way, Suite 400, Austin, TX 78701",
                email="billing@apexcloud.io",
                phone="+1 (512) 555-0199",
                website="https://apexcloud.io"
            ),
            customer=PartyInfo(
                name="Liberty Global Solutions Inc.",
                tax_id="US-EIN-13-8839201",
                address="500 Enterprise Blvd, Boston, MA 02116",
                email="accounts-payable@libertyglobal.com",
                phone="+1 (617) 555-0144"
            ),
            line_items=[
                LineItem(
                    item_code="SRV-GPU-H100",
                    description="On-demand GPU Cluster Hosting (120 Hours)",
                    quantity=120.0,
                    unit_price=Decimal("4.50"),
                    line_total=Decimal("540.00"),
                    tax_rate=8.25
                ),
                LineItem(
                    item_code="SRV-BW-EGRESS",
                    description="Dedicated High-Speed Bandwidth Egress (10 TB)",
                    quantity=10.0,
                    unit_price=Decimal("15.00"),
                    line_total=Decimal("150.00"),
                    tax_rate=8.25
                ),
                LineItem(
                    item_code="SUP-PREM-247",
                    description="24/7 Enterprise Tier SLA Support & Monitoring",
                    quantity=1.0,
                    unit_price=Decimal("250.00"),
                    line_total=Decimal("250.00"),
                    tax_rate=8.25
                ),
            ],
            subtotal=Decimal("940.00"),
            tax_amount=Decimal("77.55"),
            taxes=[
                TaxDetail(
                    tax_type="State & Local Sales Tax",
                    rate_percentage=8.25,
                    tax_amount=Decimal("77.55")
                )
            ],
            discount_amount=Decimal("50.00"),
            shipping_amount=Decimal("0.00"),
            total_amount=Decimal("967.55"),  # 940.00 + 77.55 - 50.00 = 967.55
            currency=CurrencyEnum.USD,
            payment_terms="Net 30 Days",
            bank_account_number="US99CITI1029384756",
            notes="Thank you for your business! Please include INV-2026-9842 on your remittance wire."
        )

        confidence_score = 0.985
        return data, confidence_score

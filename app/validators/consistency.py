"""
Post-extraction arithmetic, temporal, and completeness consistency validator.
Ensures 100% deterministic, audit-proof data ingestion before storage.
"""

from decimal import Decimal
from typing import Tuple, List
from datetime import date, timedelta
from app.schemas.invoice import InvoiceData
from app.config import settings


class InvoiceConsistencyValidator:
    """Performs deep sanity checks on extracted invoice structures."""

    def __init__(self, tolerance: float = settings.MATH_TOLERANCE_DELTA):
        self.tolerance = Decimal(str(tolerance))

    def validate(self, invoice: InvoiceData) -> Tuple[bool, bool, List[str]]:
        """
        Validates invoice arithmetic, dates, and mandatory fields.
        Returns:
            Tuple[arithmetic_valid: bool, review_required: bool, review_reasons: List[str]]
        """
        reasons: List[str] = []
        arithmetic_valid = True

        # 1. Line Item Sum vs Subtotal
        if invoice.line_items:
            calculated_subtotal = sum(
                (item.line_total for item in invoice.line_items),
                Decimal("0.00")
            )
            subtotal_diff = abs(calculated_subtotal - invoice.subtotal)
            if subtotal_diff > self.tolerance:
                arithmetic_valid = False
                reasons.append(
                    f"Subtotal discrepancy: Sum of line items ({calculated_subtotal:.2f}) "
                    f"does not match declared subtotal ({invoice.subtotal:.2f}) [Diff: {subtotal_diff:.2f}]"
                )

            # Individual line item unit_price * quantity check
            for idx, item in enumerate(invoice.line_items, 1):
                expected_total = Decimal(str(round(float(item.quantity) * float(item.unit_price), 2)))
                item_diff = abs(expected_total - item.line_total)
                if item_diff > self.tolerance:
                    reasons.append(
                        f"Line {idx} '{item.description[:25]}...': qty ({item.quantity}) * unit_price "
                        f"({item.unit_price:.2f}) = {expected_total:.2f}, but line_total is {item.line_total:.2f}"
                    )

        # 2. Subtotal + Tax + Shipping - Discount vs Grand Total
        expected_grand_total = (
            invoice.subtotal
            + invoice.tax_amount
            + invoice.shipping_amount
            - invoice.discount_amount
        )
        total_diff = abs(expected_grand_total - invoice.total_amount)
        if total_diff > self.tolerance:
            arithmetic_valid = False
            reasons.append(
                f"Grand total discrepancy: Subtotal ({invoice.subtotal:.2f}) + Tax ({invoice.tax_amount:.2f}) "
                f"+ Shipping ({invoice.shipping_amount:.2f}) - Discount ({invoice.discount_amount:.2f}) = "
                f"{expected_grand_total:.2f}, but declared total is {invoice.total_amount:.2f} [Diff: {total_diff:.2f}]"
            )

        # 3. Temporal Consistency (Dates)
        if invoice.due_date and invoice.invoice_date:
            if invoice.due_date < invoice.invoice_date:
                reasons.append(
                    f"Due date ({invoice.due_date}) occurs before invoice issue date ({invoice.invoice_date})"
                )

        today = date.today()
        if invoice.invoice_date > today + timedelta(days=7):
            reasons.append(f"Invoice date is far in future ({invoice.invoice_date})")

        # 4. Mandatory Identity Fields
        if not invoice.vendor.name or invoice.vendor.name.strip() == "":
            reasons.append("Vendor name is missing or empty")

        if not invoice.customer.name or invoice.customer.name.strip() == "":
            reasons.append("Customer name is missing or empty")

        # 5. Non-zero Total Check
        if invoice.total_amount <= Decimal("0.00"):
            reasons.append("Invoice total amount is zero or negative")

        review_required = len(reasons) > 0
        return arithmetic_valid, review_required, reasons

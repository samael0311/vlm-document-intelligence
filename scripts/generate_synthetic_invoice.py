"""
Synthetic Invoice Generator.
Creates realistic clean and noisy document images for pipeline testing and demonstrations.
"""

import os
from PIL import Image, ImageDraw, ImageFont


def generate_invoice_image(output_path: str = "sample_invoice.png"):
    width, height = 1200, 1600
    img = Image.new("RGB", (width, height), color=(252, 252, 254))
    draw = ImageDraw.Draw(img)

    # Use default bitmap font
    font = ImageFont.load_default()

    # Draw header
    draw.rectangle([60, 60, 1140, 160], fill=(240, 244, 248), outline=(200, 210, 220), width=2)
    draw.text((90, 80), "APEX CLOUD LOGISTICS LLC", fill=(30, 41, 59))
    draw.text((90, 105), "100 Tech Way, Suite 400 | Austin, TX 78701 | Tax ID: US-EIN-92-3849102", fill=(100, 116, 139))
    draw.text((90, 125), "Email: billing@apexcloud.io | Tel: +1 (512) 555-0199", fill=(100, 116, 139))

    # Invoice title & metadata box
    draw.text((850, 80), "INVOICE", fill=(15, 23, 42))
    draw.text((850, 105), "Invoice #: INV-2026-9842", fill=(51, 65, 85))
    draw.text((850, 125), "Date: 2026-10-24", fill=(51, 65, 85))
    draw.text((850, 140), "Due Date: 2026-11-23", fill=(51, 65, 85))

    # Bill To Box
    draw.rectangle([60, 190, 560, 310], outline=(226, 232, 240), fill=(255, 255, 255), width=1)
    draw.text((80, 205), "BILL TO:", fill=(71, 85, 105))
    draw.text((80, 225), "Liberty Global Solutions Inc.", fill=(15, 23, 42))
    draw.text((80, 245), "Attn: Accounts Payable", fill=(100, 116, 139))
    draw.text((80, 265), "500 Enterprise Blvd, Boston, MA 02116", fill=(100, 116, 139))
    draw.text((80, 285), "Tax ID: US-EIN-13-8839201", fill=(100, 116, 139))

    # PO & Terms Box
    draw.rectangle([640, 190, 1140, 310], outline=(226, 232, 240), fill=(255, 255, 255), width=1)
    draw.text((660, 205), "TERMS & DETAILS:", fill=(71, 85, 105))
    draw.text((660, 225), "Purchase Order #: PO-99120", fill=(15, 23, 42))
    draw.text((660, 245), "Payment Terms: Net 30 Days", fill=(100, 116, 139))
    draw.text((660, 265), "Remit Wire: US99CITI1029384756", fill=(100, 116, 139))
    draw.text((660, 285), "Currency: USD", fill=(100, 116, 139))

    # Table Header
    y_table = 360
    draw.rectangle([60, y_table, 1140, y_table + 40], fill=(241, 245, 249), outline=(203, 213, 225))
    draw.text((80, y_table + 12), "ITEM CODE", fill=(51, 65, 85))
    draw.text((250, y_table + 12), "DESCRIPTION", fill=(51, 65, 85))
    draw.text((700, y_table + 12), "QTY", fill=(51, 65, 85))
    draw.text((850, y_table + 12), "UNIT PRICE", fill=(51, 65, 85))
    draw.text((1020, y_table + 12), "TOTAL (USD)", fill=(51, 65, 85))

    # Table Rows
    rows = [
        ("SRV-GPU-H100", "On-demand GPU Cluster Hosting (120 Hours)", "120.00", "$4.50", "$540.00"),
        ("SRV-BW-EGRESS", "Dedicated High-Speed Bandwidth Egress (10 TB)", "10.00", "$15.00", "$150.00"),
        ("SUP-PREM-247", "24/7 Enterprise Tier SLA Support & Monitoring", "1.00", "$250.00", "$250.00"),
    ]

    curr_y = y_table + 40
    for code, desc, qty, rate, total in rows:
        draw.rectangle([60, curr_y, 1140, curr_y + 45], outline=(241, 245, 249), fill=(255, 255, 255))
        draw.text((80, curr_y + 15), code, fill=(100, 116, 139))
        draw.text((250, curr_y + 15), desc, fill=(15, 23, 42))
        draw.text((700, curr_y + 15), qty, fill=(51, 65, 85))
        draw.text((850, curr_y + 15), rate, fill=(51, 65, 85))
        draw.text((1020, curr_y + 15), total, fill=(15, 23, 42))
        curr_y += 45

    # Totals Summary
    y_summary = curr_y + 40
    draw.rectangle([750, y_summary, 1140, y_summary + 160], outline=(203, 213, 225), fill=(248, 250, 252), width=1)
    draw.text((770, y_summary + 15), "Subtotal:", fill=(71, 85, 105))
    draw.text((1030, y_summary + 15), "$940.00", fill=(15, 23, 42))

    draw.text((770, y_summary + 45), "Discount (Corporate):", fill=(71, 85, 105))
    draw.text((1030, y_summary + 45), "-$50.00", fill=(22, 101, 52))

    draw.text((770, y_summary + 75), "Sales Tax (8.25%):", fill=(71, 85, 105))
    draw.text((1030, y_summary + 75), "$77.55", fill=(15, 23, 42))

    draw.rectangle([750, y_summary + 110, 1140, y_summary + 160], fill=(226, 232, 240))
    draw.text((770, y_summary + 125), "TOTAL BALANCE DUE:", fill=(15, 23, 42))
    draw.text((1010, y_summary + 125), "$967.55 USD", fill=(15, 23, 42))

    # Footer
    draw.text((60, 1500), "Thank you for your business! Apex Cloud Logistics LLC.", fill=(148, 163, 184))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    print(f"[+] Successfully generated synthetic invoice: {output_path}")


if __name__ == "__main__":
    generate_invoice_image("sample_invoice.png")

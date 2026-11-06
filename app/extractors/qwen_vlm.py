"""
Self-hosted Open-Weights Vision-Language Model Extractor (Qwen 2.5-VL 7B / InternVL).
Optimized for AWS EC2 G5 instances with FP16/BF16 and BitsAndBytes 4-bit quantization.
"""

import json
import re
from typing import List, Tuple
from PIL import Image

from app.extractors.base import BaseExtractor
from app.schemas.invoice import InvoiceData
from app.config import settings


QWEN_PROMPT_TEMPLATE = """You are a specialized document intelligence model.
Extract all tabular rows, dates, totals, and party details from this invoice into a clean JSON object following this exact structure:
{
  "invoice_number": "str",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "purchase_order_number": "str or null",
  "vendor": {"name": "str", "tax_id": "str or null", "address": "str or null", "email": "str or null"},
  "customer": {"name": "str", "tax_id": "str or null", "address": "str or null"},
  "line_items": [
    {"item_code": "str or null", "description": "str", "quantity": 1.0, "unit_price": 10.0, "line_total": 10.0}
  ],
  "subtotal": 0.00,
  "tax_amount": 0.00,
  "discount_amount": 0.00,
  "shipping_amount": 0.00,
  "total_amount": 0.00,
  "currency": "USD"
}
Output ONLY the JSON object. Do not include markdown codeblocks or conversational filler.
"""


class QwenVLMExtractor(BaseExtractor):
    """Local GPU-accelerated inference using HuggingFace Transformers."""

    def __init__(self, model_id: str = settings.QWEN_MODEL_ID):
        self.model_id = model_id
        self.model = None
        self.processor = None
        self.device = settings.QWEN_DEVICE

    def _lazy_init(self):
        """Initializes model weights on first call to prevent cold startup bottlenecks."""
        if self.model is None:
            import torch
            from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

            torch_dtype = torch.bfloat16 if settings.QWEN_TORCH_DTYPE == "bfloat16" else torch.float16

            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=torch_dtype,
                device_map="auto" if self.device == "cuda" else None,
                load_in_4bit=settings.QWEN_LOAD_IN_4BIT if self.device == "cuda" else False
            )
            if self.device == "cpu":
                self.model.to("cpu")

    async def extract(self, images: List[Image.Image]) -> Tuple[InvoiceData, float]:
        self._lazy_init()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": images[0]},
                    {"type": "text", "text": QWEN_PROMPT_TEMPLATE}
                ]
            }
        ]

        text_prompt = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = self.processor.process_vision_info(messages)

        inputs = self.processor(
            text=[text_prompt],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        )
        inputs = inputs.to(self.model.device)

        import torch
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=2048)

        # Slice off input tokens to get generation only
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        # Extract JSON substring
        json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if not json_match:
            raise ValueError(f"Model failed to generate structured JSON. Raw output: {output_text[:200]}")

        parsed_dict = json.loads(json_match.group(0))
        invoice_data = InvoiceData.model_validate(parsed_dict)
        return invoice_data, 0.94

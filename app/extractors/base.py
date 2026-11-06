"""
Abstract base class for vision-language extraction engines.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from PIL import Image
from app.schemas.invoice import InvoiceData


class BaseExtractor(ABC):
    """Interface that every VLM backend must implement."""

    @abstractmethod
    async def extract(self, images: List[Image.Image]) -> Tuple[InvoiceData, float]:
        """
        Extracts structured InvoiceData from preprocessed document images.
        
        Args:
            images: List of normalized PIL Images (one per document page)
            
        Returns:
            Tuple[InvoiceData, confidence_score: float]
        """
        pass

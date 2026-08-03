"""
Document Processing Service.

Extracts raw text from uploaded procurement documents.
Uses a hybrid approach:
1. Attempts direct digital text extraction (PyMuPDF).
2. If text is sparse or empty (indicating a scanned document),
   falls back to OCR (PaddleOCR).
"""

import enum
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import fitz  # PyMuPDF
import numpy as np
from pydantic import BaseModel, Field

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExtractionMethod(str, enum.Enum):
    """Method used to extract text from a document."""

    TEXT = "text"
    OCR = "ocr"


class DocumentInfo(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"


class ProcessingInfo(BaseModel):
    method: ExtractionMethod
    processing_time_seconds: float
    page_count: int


class DocumentMetadata(BaseModel):
    title: str | None = None
    author: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: str | None = None
    modification_date: str | None = None
    language: str | None = None
    encrypted: bool = False


class ContentStatistics(BaseModel):
    raw_text: str = ""
    character_count: int = 0
    word_count: int = 0


class DocumentExtractionResult(BaseModel):
    """Standardized result of document processing."""

    success: bool
    document: DocumentInfo
    processing: ProcessingInfo
    metadata: DocumentMetadata
    content: ContentStatistics
    errors: list[str] = Field(default_factory=list)


class DocumentProcessor:
    """
    Handles PDF document text extraction and OCR fallback.

    Provides a clean, crash-free interface for extracting text from
    both digital and scanned PDFs.
    """

    # Meaningful text threshold: if raw text has fewer than this many words per page,
    # we assume it might be a scanned document and fallback to OCR.
    _WORDS_PER_PAGE_THRESHOLD = 20

    def __init__(self) -> None:
        # Lazy initialization of OCR engine to save memory if only text PDFs are processed.
        self._ocr_engine = None

    def _get_ocr_engine(self) -> Any:
        """Initialize and return the PaddleOCR engine locally."""
        if self._ocr_engine is None:
            try:
                from paddleocr import PaddleOCR

                # Initialize PaddleOCR with English language. Use CPU by default to avoid GPU dependency issues.
                logger.info("Initializing PaddleOCR engine...")
                self._ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            except ImportError as e:
                logger.error("PaddleOCR is not installed or failed to load: %s", e)
                raise RuntimeError("OCR engine unavailable.") from e
        return self._ocr_engine

    def process_document(self, file_path: Path) -> DocumentExtractionResult:
        """
        Process a document and extract its raw text.

        Attempts PyMuPDF digital extraction first. If it yields insufficient text,
        falls back to PaddleOCR.

        Args:
            file_path: Absolute path to the PDF document.

        Returns:
            DocumentExtractionResult with extracted text and metadata.
        """
        start_time = time.time()
        errors: list[str] = []
        method = ExtractionMethod.TEXT
        extracted_text = ""
        page_count = 0
        
        # Populate defaults
        doc_info = DocumentInfo()
        if file_path.exists():
            doc_info.file_name = file_path.name
            doc_info.file_path = str(file_path.absolute())
            doc_info.file_size_bytes = file_path.stat().st_size

        doc_meta = DocumentMetadata()

        # Helper to construct proper response internally
        def make_result(success_: bool, errs: list[str], txt: str, mthd: ExtractionMethod, p_count: int) -> DocumentExtractionResult:
            end_time = time.time()
            return DocumentExtractionResult(
                success=success_,
                document=doc_info,
                processing=ProcessingInfo(
                    method=mthd,
                    processing_time_seconds=end_time - start_time,
                    page_count=p_count
                ),
                metadata=doc_meta,
                content=ContentStatistics(
                    raw_text=txt,
                    character_count=len(txt),
                    word_count=len(txt.split())
                ),
                errors=errs
            )

        if not file_path.exists():
            return make_result(False, ["File not found."], "", method, 0)

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", file_path, e)
            return make_result(False, [f"Corrupted or unsupported PDF: {e}"], "", method, 0)

        try:
            doc_meta.encrypted = doc.is_encrypted
            if doc_meta.encrypted:
                return make_result(False, ["Document is password protected."], "", method, 0)

            page_count = len(doc)
            if page_count == 0:
                return make_result(False, ["Empty document."], "", method, 0)

            # Metadata extraction
            doc_meta.title = doc.metadata.get("title")
            doc_meta.author = doc.metadata.get("author")
            doc_meta.creator = doc.metadata.get("creator")
            doc_meta.producer = doc.metadata.get("producer")
            doc_meta.creation_date = doc.metadata.get("creationDate")
            doc_meta.modification_date = doc.metadata.get("modDate")
            # PyMuPDF doesn't give a standard global language field reliably, leave as None for now.

            # Strategy 1: PyMuPDF Text Extraction
            extracted_text = self._try_text_extraction(doc)

            # Check if extraction was sufficient.
            words = extracted_text.split()
            avg_words_per_page = len(words) / page_count if page_count > 0 else 0

            # Fallback to Strategy 2: OCR
            if avg_words_per_page < self._WORDS_PER_PAGE_THRESHOLD:
                logger.info(
                    "Digital extraction yielded %d words on %d pages. Falling back to OCR.",
                    len(words),
                    page_count,
                )
                try:
                    extracted_text = self._run_ocr(doc)
                    method = ExtractionMethod.OCR
                except Exception as e:
                    logger.error("OCR extraction failed: %s", e)
                    errors.append(f"OCR failure: {e}")
                    # If OCR fails, we still return whatever text PyMuPDF found (even if sparse)
                    method = ExtractionMethod.TEXT
        except Exception as e:
            logger.error("Unexpected error processing document %s: %s", file_path, e)
            errors.append(f"Unexpected processing error: {e}")
        finally:
            doc.close()

        extracted_text = self._clean_text(extracted_text)
        success = len(errors) == 0 and len(extracted_text.strip()) > 0

        logger.info(
            "Document processed in %.2fs using %s (Pages: %d, Success: %s)",
            time.time() - start_time,
            method.value,
            page_count,
            success,
        )

        return make_result(success, errors, extracted_text, method, page_count)

    def _try_text_extraction(self, doc: fitz.Document) -> str:
        """Extract text page by page using PyMuPDF."""
        pages_text = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            if text:
                pages_text.append(text)
        return "\n\n--- Page Break ---\n\n".join(pages_text)

    def _run_ocr(self, doc: fitz.Document) -> str:
        """
        Convert PDF pages to images and run PaddleOCR.
        Requires generating a pixmap for each page.
        """
        ocr = self._get_ocr_engine()
        pages_text = []

        for i in range(len(doc)):
            page = doc.load_page(i)
            # Render page to an image (pixmap) with a reasonable DPI (zoom)
            zoom = 2.0  # ~144 DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert pixmap to numpy array for PaddleOCR (needs BGR array)
            # PyMuPDF provides RGB, so we need to convert to BGR using numpy slicing
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            if pix.n == 3:
                # RGB to BGR
                img_array = img_array[:, :, ::-1]

            # Run OCR on the image
            result = ocr.ocr(img_array, cls=True)

            page_words = []
            if result and result[0]:
                for line in result[0]:
                    # line structure: [[box_coords], (text, confidence)]
                    text = line[1][0]
                    page_words.append(text)

            # Join lines on the page
            page_text = "\n".join(page_words)
            pages_text.append(page_text)

        return "\n\n--- Page Break ---\n\n".join(pages_text)

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalize whitespace and clean up raw text keeping useful formatting.
        - Trims leading/trailing spaces
        - Removes excessive consecutive blank lines
        """
        if not text:
            return ""

        # Split into lines
        lines = text.splitlines()

        # Trim spaces per line & remove excessive blank lines
        cleaned_lines = []
        blank_count = 0
        for line in lines:
            line_str = line.strip()
            if not line_str:
                blank_count += 1
                # max two consecutive blank lines
                if blank_count <= 2:
                    cleaned_lines.append("")
            else:
                blank_count = 0
                cleaned_lines.append(line_str)

        return "\n".join(cleaned_lines).strip()

"""
Unit tests for the DocumentProcessor service.
"""

import math
from pathlib import Path

import fitz  # PyMuPDF
import pytest

from app.services.document_processor import DocumentProcessor, ExtractionMethod


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def digital_pdf_path(temp_dir: Path) -> Path:
    """Create a digital PDF with direct text."""
    path = temp_dir / "digital.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Add enough words to bypass the OCR threshold (>20 words)
    text = "This is a digital PDF file with easily extractable text. " * 5
    page.insert_text(fitz.Point(50, 50), text)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def empty_pdf_path(temp_dir: Path) -> Path:
    """Create an empty PDF (0 pages)."""
    path = temp_dir / "empty.pdf"
    # Actually, a PDF with 0 pages is often considered malformed, but 
    # we can just write an empty byte file which will fail to open properly 
    # or create a 1-page blank pdf. Let's create a 1-page blank PDF.
    doc = fitz.open()
    doc.new_page()
    doc.save(path)
    doc.close()
    return path

@pytest.fixture
def corrupted_pdf_path(temp_dir: Path) -> Path:
    """Create a corrupted PDF file."""
    path = temp_dir / "corrupted.pdf"
    path.write_bytes(b"This is not a PDF file.")
    return path


def test_missing_file_handling():
    processor = DocumentProcessor()
    result = processor.process_document(Path("/path/to/nonexistent/file.pdf"))
    
    assert result.success is False
    assert result.processing.page_count == 0
    assert "File not found" in result.errors[0]
    assert result.content.raw_text == ""


def test_corrupted_file_handling(corrupted_pdf_path: Path):
    processor = DocumentProcessor()
    result = processor.process_document(corrupted_pdf_path)
    
    assert result.success is False
    assert result.processing.page_count == 0
    assert "Corrupted or unsupported" in result.errors[0]


def test_blank_page_handling(empty_pdf_path: Path):
    processor = DocumentProcessor()
    result = processor.process_document(empty_pdf_path)
    
    assert result.success is False
    assert result.processing.page_count == 1
    assert result.content.raw_text == ""


def test_digital_text_extraction(digital_pdf_path: Path):
    processor = DocumentProcessor()
    result = processor.process_document(digital_pdf_path)
    
    assert result.success is True
    assert result.processing.method == ExtractionMethod.TEXT
    assert result.processing.page_count == 1
    assert "digital PDF file" in result.content.raw_text

"""PDF text extraction module using pypdf."""

from pathlib import Path
from typing import List, Tuple
from pypdf import PdfReader

from .utils import log_message


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass


class ScanBasedPDFError(Exception):
    """Raised when PDF appears to be scan-based (image-only)."""
    pass


def extract_text_from_pdf(
    pdf_path: Path,
    start_page: int = 1,
    end_page: int = 0
) -> Tuple[str, List[str]]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        start_page: First page to extract (1-indexed)
        end_page: Last page to extract (0 = to end)
        
    Returns:
        Tuple of (full_text, list_of_page_texts)
        
    Raises:
        PDFExtractionError: If PDF cannot be read
        ScanBasedPDFError: If >50% of pages have no extractable text
    """
    if not pdf_path.exists():
        raise PDFExtractionError(f"File not found: {pdf_path}")
    
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        raise PDFExtractionError(f"Cannot read PDF: {e}")
    
    total_pages = len(reader.pages)
    log_message(f"PDF has {total_pages} pages")
    
    # Validate page range
    if start_page < 1:
        start_page = 1
    if end_page <= 0 or end_page > total_pages:
        end_page = total_pages
    if start_page > end_page:
        raise PDFExtractionError(f"Invalid page range: {start_page}-{end_page}")
    
    log_message(f"Extracting pages {start_page} to {end_page}")
    
    page_texts: List[str] = []
    empty_pages = 0
    
    total_to_extract = end_page - (start_page - 1)
    for i, page_num in enumerate(range(start_page - 1, end_page)):
        try:
            page = reader.pages[page_num]
            text = page.extract_text() or ""
            text = text.strip()
            
            if len(text) < 10:  # Almost empty
                empty_pages += 1
                
            page_texts.append(text)
        except Exception as e:
            # Only log first few errors to avoid spam
            if empty_pages < 5:
                log_message(f"Warning: Could not extract page {page_num + 1}: {e}")
            page_texts.append("")
            empty_pages += 1
        
        # Log progress every 500 pages for large PDFs
        if (i + 1) % 500 == 0:
            log_message(f"Extracted {i + 1}/{total_to_extract} pages...")
    
    # Check if this is a scan-based PDF
    total_extracted = len(page_texts)
    empty_ratio = empty_pages / total_extracted if total_extracted > 0 else 1.0
    
    if empty_ratio > 0.5:
        raise ScanBasedPDFError(
            f"This PDF appears to be scan-based (image-only). "
            f"{empty_pages}/{total_extracted} pages ({empty_ratio:.0%}) have no extractable text. "
            f"Please use OCR software to convert scanned images to text first."
        )
    
    if empty_pages > 0:
        log_message(f"Warning: {empty_pages} pages had minimal/no text")
    
    full_text = "\n\n".join(page_texts)
    log_message(f"Extracted {len(full_text)} characters from {total_extracted} pages")
    
    return full_text, page_texts


def get_pdf_info(pdf_path: Path) -> dict:
    """Get basic PDF metadata."""
    try:
        reader = PdfReader(str(pdf_path))
        metadata = reader.metadata or {}
        return {
            "pages": len(reader.pages),
            "title": metadata.get("/Title", ""),
            "author": metadata.get("/Author", ""),
        }
    except Exception as e:
        return {"error": str(e)}

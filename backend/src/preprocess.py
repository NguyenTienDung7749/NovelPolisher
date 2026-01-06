"""Text preprocessing module for fixing PDF-converted text issues."""

import re
from typing import List, Set
from collections import Counter

from .utils import log_message


# Sentence-ending punctuation (Vietnamese + Chinese + common)
SENTENCE_ENDINGS = set('.!?…:;"\'"」』】）)]\u201d\u201c')

# Characters that indicate line should NOT be joined
LINE_START_BLOCK = set('•·●○◆◇■□▪▫–—-')


def normalize_newlines(text: str) -> str:
    """Convert all newline variants to unix-style \\n."""
    return text.replace('\r\n', '\n').replace('\r', '\n')


def is_page_number_line(line: str) -> bool:
    """Check if line is just a page number."""
    stripped = line.strip()
    # Match patterns like: "1", "- 1 -", "Page 1", "Trang 1"
    patterns = [
        r'^\s*\d+\s*$',  # Just number
        r'^\s*[-—–]\s*\d+\s*[-—–]\s*$',  # - 1 -
        r'^\s*(Page|Trang|p\.?)\s*\d+\s*$',  # Page 1
    ]
    for pattern in patterns:
        if re.match(pattern, stripped, re.IGNORECASE):
            return True
    return False


def is_chapter_heading(line: str) -> bool:
    """Check if line looks like a chapter heading."""
    stripped = line.strip()
    # Match: Chương N: Title, CHƯƠNG N - Title, Chương N. Title, Chương N (no title), etc.
    pattern = r'^\s*chương\s+\d{1,5}\s*(?:[:：.\-–—]|$)'
    return bool(re.match(pattern, stripped, re.IGNORECASE))


def should_join_lines(current_line: str, next_line: str) -> bool:
    """
    Determine if two lines should be joined.
    
    Lines should be joined if:
    - Current line does NOT end with sentence-ending punctuation
    - Next line starts with lowercase or continuation character
    - Neither line is a chapter heading
    """
    current = current_line.rstrip()
    next_stripped = next_line.strip()
    
    # Don't join if either is empty
    if not current or not next_stripped:
        return False
    
    # Don't join if either is a chapter heading
    if is_chapter_heading(current) or is_chapter_heading(next_stripped):
        return False
    
    # Don't join if current ends with sentence-ending punctuation
    if current[-1] in SENTENCE_ENDINGS:
        return False
    
    # Don't join if next starts with blocking character
    if next_stripped[0] in LINE_START_BLOCK:
        return False
    
    # Don't join if next line starts with uppercase (likely new sentence/paragraph)
    # But be careful with Vietnamese - check if it's truly uppercase
    first_char = next_stripped[0]
    if first_char.isupper() and not first_char.isdigit():
        # Could be start of new sentence, don't join
        return False
    
    # Join the lines
    return True


def find_repeating_headers_footers(page_texts: List[str], threshold: float = 0.3) -> Set[str]:
    """
    Find lines that repeat across many pages (likely headers/footers).
    
    Args:
        page_texts: List of text from each page
        threshold: Minimum ratio of pages a line must appear in to be considered repeating
        
    Returns:
        Set of lines to remove
    """
    line_counts: Counter = Counter()
    total_pages = len(page_texts)
    
    if total_pages < 3:
        return set()
    
    # For very large PDFs, sample pages instead of scanning all
    # This significantly improves performance for 6000+ page documents
    if total_pages > 200:
        # Sample first 50, last 50, and 100 random pages from middle
        import random
        sample_indices = list(range(50)) + list(range(total_pages - 50, total_pages))
        middle_range = list(range(50, total_pages - 50))
        if len(middle_range) > 100:
            sample_indices.extend(random.sample(middle_range, 100))
        else:
            sample_indices.extend(middle_range)
        sample_indices = sorted(set(sample_indices))
        sampled_pages = [page_texts[i] for i in sample_indices]
        effective_total = len(sampled_pages)
    else:
        sampled_pages = page_texts
        effective_total = total_pages
    
    # Count short lines (likely headers/footers) across sampled pages
    for page_text in sampled_pages:
        seen_on_page: Set[str] = set()
        for line in page_text.split('\n'):
            stripped = line.strip()
            # Only consider short lines (headers/footers are usually short)
            if 3 <= len(stripped) <= 40:
                if stripped not in seen_on_page:
                    line_counts[stripped] += 1
                    seen_on_page.add(stripped)
    
    # Find lines appearing on >= threshold of pages
    min_count = int(effective_total * threshold)
    repeating = {line for line, count in line_counts.items() if count >= min_count}
    
    if repeating:
        log_message(f"Found {len(repeating)} repeating header/footer lines to remove")
    
    return repeating


def normalize_chapter_title(text: str) -> str:
    """
    Normalize chapter title format.
    
    Handles: ":" or "：" or "-" or "–" and extra whitespace
    """
    # Normalize chapter heading separators
    # Pattern: Chương N followed by separator
    def normalize_heading(match):
        chap_word = match.group(1)
        number = match.group(2)
        title = match.group(3).strip()
        return f"{chap_word} {number}: {title}"
    
    pattern = r'(Chương|CHƯƠNG|chương)\s+(\d{1,5})\s*[:：\-–]\s*(.+?)(?=\n|$)'
    text = re.sub(pattern, normalize_heading, text, flags=re.MULTILINE)
    
    return text


def preprocess_text(text: str, page_texts: List[str] = None) -> str:
    """
    Full preprocessing pipeline for PDF-extracted text.
    
    Args:
        text: Raw extracted text
        page_texts: Optional list of per-page texts for header/footer detection
        
    Returns:
        Cleaned and normalized text
    """
    log_message("Starting text preprocessing...")
    
    # Step 1: Normalize newlines
    text = normalize_newlines(text)
    original_len = len(text)
    
    # Step 2: Find repeating headers/footers if page texts available
    repeating_lines: Set[str] = set()
    if page_texts:
        repeating_lines = find_repeating_headers_footers(page_texts)
    
    # Step 3: Process line by line
    lines = text.split('\n')
    processed_lines: List[str] = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip page numbers
        if is_page_number_line(stripped):
            i += 1
            continue
        
        # Skip repeating headers/footers
        if stripped in repeating_lines:
            i += 1
            continue
        
        # Skip completely empty lines (but track for paragraph detection)
        if not stripped:
            # Keep one blank line for paragraph separation
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append('')
            i += 1
            continue
        
        # Check if we should join with next line
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if should_join_lines(line, next_line) and not is_page_number_line(next_line.strip()):
                # Join lines with a space
                lines[i + 1] = stripped + ' ' + next_line.strip()
                i += 1
                continue
        
        processed_lines.append(stripped)
        i += 1
    
    # Step 4: Join lines and normalize chapter titles
    result = '\n'.join(processed_lines)
    result = normalize_chapter_title(result)
    
    # Step 5: Clean up multiple blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    final_len = len(result)
    reduction = (1 - final_len / original_len) * 100 if original_len > 0 else 0
    log_message(f"Preprocessing complete: {original_len} -> {final_len} chars ({reduction:.1f}% reduced)")
    
    return result.strip()

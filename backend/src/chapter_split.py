"""Chapter splitting module for Vietnamese novels."""

import re
from dataclasses import dataclass
from typing import List, Optional

from .utils import log_message


@dataclass
class Chapter:
    """Represents a chapter in the novel."""
    number: int
    title: str
    text: str
    
    def __repr__(self) -> str:
        return f"Chapter({self.number}, '{self.title[:30]}...', {len(self.text)} chars)"


# Main chapter pattern - case insensitive, multiline
# Matches: Chương 1: Title, CHƯƠNG 1 - Title, Chương 1：Title, Chương 1. Title, etc.
# Also matches: Chương 1 (without separator/title) for plain chapter headers
CHAPTER_PATTERN = re.compile(
    r'^\s*chương\s+(\d{1,5})\s*(?:[:：.\-–—]\s*(.+?))?\s*$',
    re.IGNORECASE | re.MULTILINE
)


def split_into_chapters(text: str) -> List[Chapter]:
    """
    Split text into chapters based on chapter headings.
    
    Args:
        text: Preprocessed novel text
        
    Returns:
        List of Chapter objects
    """
    log_message("Splitting text into chapters...")
    
    # Find all chapter headings
    matches = list(CHAPTER_PATTERN.finditer(text))
    
    if not matches:
        log_message("WARNING: No chapter headings found! Using entire text as single chapter.")
        return [Chapter(
            number=1,
            title="Toàn bộ nội dung",
            text=text.strip()
        )]
    
    log_message(f"Found {len(matches)} chapter headings")
    
    chapters: List[Chapter] = []
    total_matches = len(matches)
    
    for i, match in enumerate(matches):
        chapter_num = int(match.group(1))
        # Handle optional title (group 2 may be None for "Chương N" without separator)
        chapter_title = (match.group(2) or f"Chương {chapter_num}").strip()
        
        # Get text from end of this heading to start of next heading (or end of text)
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        chapter_text = text[start_pos:end_pos].strip()
        
        chapters.append(Chapter(
            number=chapter_num,
            title=chapter_title,
            text=chapter_text
        ))
        
        # Only log progress every 50 chapters to avoid I/O overhead
        if (i + 1) % 50 == 0 or i == total_matches - 1:
            log_message(f"Processed {i + 1}/{total_matches} chapters...")
    
    # Check for text before first chapter
    first_match = matches[0]
    prologue_text = text[:first_match.start()].strip()
    if prologue_text and len(prologue_text) > 100:
        log_message(f"Found prologue/intro text before Chapter 1 ({len(prologue_text)} chars)")
        # Insert prologue as Chapter 0
        chapters.insert(0, Chapter(
            number=0,
            title="Mở đầu",
            text=prologue_text
        ))
    
    return chapters


def validate_chapters(chapters: List[Chapter]) -> List[str]:
    """
    Validate chapter list for potential issues.
    
    Returns list of warning messages.
    """
    warnings: List[str] = []
    
    if not chapters:
        warnings.append("No chapters found")
        return warnings
    
    # Check for gaps in chapter numbers
    numbers = [c.number for c in chapters if c.number > 0]
    if numbers:
        expected = set(range(min(numbers), max(numbers) + 1))
        actual = set(numbers)
        missing = expected - actual
        if missing:
            warnings.append(f"Missing chapter numbers: {sorted(missing)}")
    
    # Check for very short chapters
    for chapter in chapters:
        if len(chapter.text) < 100:
            warnings.append(f"Chapter {chapter.number} is very short ({len(chapter.text)} chars)")
    
    return warnings

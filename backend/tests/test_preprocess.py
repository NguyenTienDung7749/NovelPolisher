"""Tests for preprocessing module."""

import pytest
from src.preprocess import (
    normalize_newlines,
    is_page_number_line,
    is_chapter_heading,
    should_join_lines,
    preprocess_text
)


class TestNormalizeNewlines:
    """Test newline normalization."""
    
    def test_crlf_to_lf(self):
        """Convert Windows line endings to Unix."""
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = normalize_newlines(text)
        assert result == "Line 1\nLine 2\nLine 3"
    
    def test_cr_to_lf(self):
        """Convert old Mac line endings to Unix."""
        text = "Line 1\rLine 2\rLine 3"
        result = normalize_newlines(text)
        assert result == "Line 1\nLine 2\nLine 3"
    
    def test_mixed_endings(self):
        """Handle mixed line endings."""
        text = "Line 1\r\nLine 2\rLine 3\nLine 4"
        result = normalize_newlines(text)
        assert "\r" not in result
        assert result.count("\n") == 3


class TestIsPageNumberLine:
    """Test page number detection."""
    
    def test_simple_number(self):
        """Detect simple page number."""
        assert is_page_number_line("42")
        assert is_page_number_line("  123  ")
    
    def test_dashed_number(self):
        """Detect dashed page number."""
        assert is_page_number_line("- 42 -")
        assert is_page_number_line("—15—")
    
    def test_page_prefix(self):
        """Detect 'Page N' format."""
        assert is_page_number_line("Page 10")
        assert is_page_number_line("Trang 5")
    
    def test_not_page_number(self):
        """Non-page-number content."""
        assert not is_page_number_line("Chapter 1")
        assert not is_page_number_line("42 monkeys")
        assert not is_page_number_line("In the year 2024")


class TestIsChapterHeading:
    """Test chapter heading detection."""
    
    def test_standard_format(self):
        """Detect standard chapter heading."""
        assert is_chapter_heading("Chương 1: Title")
        assert is_chapter_heading("CHƯƠNG 10: Another Title")
    
    def test_with_dash(self):
        """Detect chapter with dash separator."""
        assert is_chapter_heading("Chương 5 - Title Here")
    
    def test_not_chapter(self):
        """Non-chapter text."""
        assert not is_chapter_heading("This is regular text")
        assert not is_chapter_heading("Chapter 1 in English")


class TestShouldJoinLines:
    """Test line joining logic."""
    
    def test_join_incomplete_sentence(self):
        """Join lines when sentence is incomplete."""
        current = "Anh ta đi"
        next_line = "về nhà."
        assert should_join_lines(current, next_line)
    
    def test_no_join_after_period(self):
        """Don't join after sentence-ending punctuation."""
        current = "Anh ta đi về nhà."
        next_line = "Hôm nay trời đẹp."
        assert not should_join_lines(current, next_line)
    
    def test_no_join_chapter_heading(self):
        """Don't join before chapter heading."""
        current = "End of chapter"
        next_line = "Chương 2: New Chapter"
        assert not should_join_lines(current, next_line)
    
    def test_no_join_empty_lines(self):
        """Don't join empty lines."""
        assert not should_join_lines("", "Next line")
        assert not should_join_lines("Current line", "")


class TestPreprocessText:
    """Test full preprocessing pipeline."""
    
    def test_basic_preprocessing(self):
        """Test basic text cleanup."""
        text = "Line 1\r\nLine 2\r\n\r\nParagraph 2"
        result = preprocess_text(text)
        
        assert "\r" not in result
        assert "Line 1" in result
        assert "Paragraph 2" in result
    
    def test_removes_page_numbers(self):
        """Page numbers should be removed."""
        text = "Content here.\n42\nMore content."
        result = preprocess_text(text)
        
        # Page number should be removed
        assert "\n42\n" not in result
    
    def test_preserves_chapters(self):
        """Chapter headings should be preserved."""
        text = """
Chương 1: Thiếu Niên

Nội dung chương 1.

Chương 2: Tiếp Theo

Nội dung chương 2.
"""
        result = preprocess_text(text)
        
        assert "Chương 1:" in result
        assert "Chương 2:" in result

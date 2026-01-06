"""Tests for chapter splitting module."""

import pytest
from src.chapter_split import split_into_chapters, CHAPTER_PATTERN


class TestChapterPattern:
    """Test chapter detection regex pattern."""
    
    def test_standard_format(self):
        """Test standard 'Chương N: Title' format."""
        text = "Chương 1: Thiếu Niên Anh Tuấn"
        match = CHAPTER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "1"
        assert match.group(2) == "Thiếu Niên Anh Tuấn"
    
    def test_uppercase_format(self):
        """Test uppercase 'CHƯƠNG N: Title' format."""
        text = "CHƯƠNG 2: Gặp Gỡ Định Mệnh"
        match = CHAPTER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "2"
        assert match.group(2) == "Gặp Gỡ Định Mệnh"
    
    def test_fullwidth_colon(self):
        """Test fullwidth colon '：' format."""
        text = "Chương 3： Tình Cờ Hội Ngộ"
        match = CHAPTER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "3"
        assert match.group(2) == "Tình Cờ Hội Ngộ"
    
    def test_dash_separator(self):
        """Test dash '-' separator format."""
        text = "Chương 4 - Tiểu Thư Sinh Phong Lưu"
        match = CHAPTER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "4"
        assert match.group(2) == "Tiểu Thư Sinh Phong Lưu"
    
    def test_en_dash_separator(self):
        """Test en-dash '–' separator format."""
        text = "Chương 5 – Bước Đường Công Danh"
        match = CHAPTER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "5"
        assert match.group(2) == "Bước Đường Công Danh"
    
    def test_extra_whitespace(self):
        """Test handling of extra whitespace."""
        text = "  Chương   10  :   Thử Thách Mới   "
        match = CHAPTER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "10"
        assert match.group(2).strip() == "Thử Thách Mới"


class TestSplitIntoChapters:
    """Test chapter splitting functionality."""
    
    def test_split_two_chapters(self):
        """Test splitting text with two chapters."""
        text = """
Chương 1: Thiếu Niên Khởi Hành

Lý Thanh Vân nhìn ra cửa sổ, trời đã sang thu.
Hôm nay là ngày cuối cùng ở nhà.

Chương 2: Gặp Gỡ Tại Kinh Thành

Kinh thành đông đúc, người qua lại tấp nập.
Thanh Vân cảm thấy choáng ngợp.
"""
        chapters = split_into_chapters(text)
        
        assert len(chapters) == 2
        assert chapters[0].number == 1
        assert chapters[0].title == "Thiếu Niên Khởi Hành"
        assert "Lý Thanh Vân" in chapters[0].text
        
        assert chapters[1].number == 2
        assert chapters[1].title == "Gặp Gỡ Tại Kinh Thành"
        assert "Kinh thành" in chapters[1].text
    
    def test_no_chapters_fallback(self):
        """Test fallback when no chapters are found."""
        text = """
Đây là nội dung không có tiêu đề chương.
Chỉ là văn bản thuần túy.
"""
        chapters = split_into_chapters(text)
        
        assert len(chapters) == 1
        assert chapters[0].number == 1
        assert chapters[0].title == "Toàn bộ nội dung"
    
    def test_prologue_detection(self):
        """Test detection of prologue text before first chapter."""
        text = """
Tiêu Dao Tiểu Thư Sinh
Tác giả: Hắc Cẩu

Đây là câu chuyện về một thư sinh...

Chương 1: Khởi Đầu

Nội dung chương 1 ở đây.
"""
        chapters = split_into_chapters(text)
        
        # Should have prologue (chapter 0) and chapter 1
        assert len(chapters) == 2
        assert chapters[0].number == 0
        assert chapters[0].title == "Mở đầu"
        assert "Tiêu Dao" in chapters[0].text
        assert chapters[1].number == 1


class TestChapterPatternMultiline:
    """Test chapter pattern in multiline context."""
    
    def test_find_all_chapters(self):
        """Test finding all chapters in multiline text."""
        text = """
Some intro text here.

Chương 1: Đầu Tiên

Content 1.

Chương 2: Thứ Hai

Content 2.

Chương 3: Thứ Ba

Content 3.
"""
        matches = list(CHAPTER_PATTERN.finditer(text))
        
        assert len(matches) == 3
        assert matches[0].group(1) == "1"
        assert matches[1].group(1) == "2"
        assert matches[2].group(1) == "3"

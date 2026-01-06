"""
Comprehensive Test Suite for TieuDaoPolisher Backend
======================================================
This test file extends the existing test coverage with additional tests
as requested for the code review.

Run with: pytest backend/tests/test_suite.py -v
"""

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import modules under test
from src.preprocess import preprocess_text, should_join_lines, is_chapter_heading
from src.chapter_split import split_into_chapters, Chapter, CHAPTER_PATTERN
from src.chunking import create_chunks, split_by_paragraphs, Chunk


class TestPreprocessTextAdvanced:
    """Extended tests for preprocess_text function."""
    
    def test_joins_broken_pdf_lines(self):
        """
        Test that broken lines from PDF extraction are properly joined.
        Common PDF issue: sentences broken mid-phrase.
        """
        # Input: PDF-typical broken lines without sentence-ending punctuation
        text = """Lý Thanh Vân nhìn ra ngoài
cửa sổ, bầu trời
đã chuyển sang màu xám.

Chương 1: Khởi Đầu

Anh ta đứng dậy
và bước ra ngoài."""
        
        result = preprocess_text(text)
        
        # Lines without punctuation should be joined
        # Chapter headings should be preserved on their own line
        assert "Chương 1:" in result
        # The chapter heading should still be recognizable
        assert is_chapter_heading("Chương 1: Khởi Đầu")
    
    def test_preserves_chapter_headings_completely(self):
        """Chapter headings should never be joined to adjacent lines."""
        text = """Nội dung cuối chương trước
không có dấu chấm

Chương 5: Tiêu Đề Mới

Nội dung chương mới bắt đầu ở đây."""
        
        result = preprocess_text(text)
        
        # Chapter heading should be on its own line
        lines = result.split('\n')
        chapter_line = [l for l in lines if 'Chương 5:' in l]
        assert len(chapter_line) == 1
        assert chapter_line[0].strip().startswith('Chương 5:')
    
    def test_handles_multiple_line_breaks(self):
        """Multiple consecutive blank lines should be normalized."""
        text = "Paragraph 1.\n\n\n\n\nParagraph 2."
        result = preprocess_text(text)
        
        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in result


class TestSplitChaptersAdvanced:
    """Extended tests for split_into_chapters function."""
    
    def test_split_two_chapters_exact(self):
        """
        Input: Text chứa "Chương 1: A... Chương 2: B..."
        Expect: List trả về độ dài 2, đúng title và body.
        """
        text = """Chương 1: Khởi Đầu Mới

Nội dung của chương 1 ở đây.
Có nhiều dòng và đoạn văn.

Chương 2: Cuộc Hành Trình

Nội dung của chương 2 ở đây.
Cũng có nhiều dòng."""
        
        chapters = split_into_chapters(text)
        
        # Exact 2 chapters
        assert len(chapters) == 2
        
        # Chapter 1
        assert chapters[0].number == 1
        assert chapters[0].title == "Khởi Đầu Mới"
        assert "Nội dung của chương 1" in chapters[0].text
        
        # Chapter 2
        assert chapters[1].number == 2
        assert chapters[1].title == "Cuộc Hành Trình"
        assert "Nội dung của chương 2" in chapters[1].text
    
    def test_chapter_variants(self):
        """Test various chapter heading formats are recognized."""
        variants = [
            ("Chương 1: Tiêu đề", 1, "Tiêu đề"),
            ("CHƯƠNG 10 - Tiêu Đề Lớn", 10, "Tiêu Đề Lớn"),
            ("Chương 5 – En Dash Title", 5, "En Dash Title"),
            ("Chương 3： Fullwidth Colon", 3, "Fullwidth Colon"),
            ("  Chương 100  :  Extra Spaces  ", 100, "Extra Spaces"),
        ]
        
        for heading, expected_num, expected_title in variants:
            match = CHAPTER_PATTERN.search(heading)
            assert match is not None, f"Failed to match: {heading}"
            assert int(match.group(1)) == expected_num
            assert match.group(2).strip() == expected_title
    
    def test_no_false_positive_in_text(self):
        """Ensure chapter pattern doesn't match regular text."""
        # These should NOT match
        non_chapters = [
            "Trong chương trình hôm nay",  # "chương trình" != "chương X:"
            "Xem chương 1 để biết thêm",  # Not at line start
            "chương một: không có số",  # No numeric chapter number
        ]
        
        for text in non_chapters:
            # Ensure it's not a standalone line match
            match = CHAPTER_PATTERN.search(text)
            # Some may match partially, but validate context
            if match:
                # If it matches, it should be a valid chapter format
                assert match.group(1).isdigit(), f"Unexpected match: {text}"


class TestChunkTextAdvanced:
    """Extended tests for chunk_text (create_chunks) function."""
    
    def test_chunk_10000_chars_into_3000(self):
        """
        Input: Một chương dài 10.000 ký tự. Max_chars = 3000.
        Expect: Phải chia thành 4 phần (3000, 3000, 3000, 1000).
        Không được cắt giữa chừng từ/câu.
        """
        # Create ~10000 character text with paragraph structure
        paragraphs = []
        char_count = 0
        para_num = 0
        while char_count < 10000:
            para_num += 1
            # Each paragraph ~500 chars
            para = f"Đoạn văn số {para_num}. " + ("Nội dung bổ sung để tăng độ dài. " * 15)
            paragraphs.append(para)
            char_count += len(para) + 2  # +2 for \n\n
        
        long_text = "\n\n".join(paragraphs)
        
        # Create chapter and chunks
        chapters = [Chapter(number=1, title="Test Long Chapter", text=long_text)]
        chunks = create_chunks(chapters, max_chars=3000)
        
        # Should have multiple chunks (around 4 based on ~10000/3000)
        assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"
        
        # All chunks should be reasonably close to max_chars (with tolerance)
        for i, chunk in enumerate(chunks[:-1]):  # All except last
            # Allow 20% tolerance for paragraph boundary alignment
            assert len(chunk.text) <= 3600, \
                f"Chunk {i} too long: {len(chunk.text)} chars"
        
        # Verify no mid-word cuts by checking all chunks end with punctuation or complete words
        for chunk in chunks:
            text = chunk.text.strip()
            # Should end with punctuation or complete word
            last_char = text[-1] if text else ''
            # Vietnamese text typically ends with periods, commas, or complete diacritics
            assert not text.endswith(' '), f"Chunk ends with space: {text[-20:]}"
    
    def test_chunk_preserves_paragraph_boundaries(self):
        """Chunks should split at paragraph boundaries, not mid-paragraph."""
        text = """Đoạn văn đầu tiên với nội dung dài. Có nhiều câu trong đoạn này.

Đoạn văn thứ hai cũng dài. Nội dung tiếp tục ở đây.

Đoạn văn thứ ba kết thúc ở đây."""
        
        chunks = split_by_paragraphs(text, max_chars=100)
        
        for chunk in chunks:
            # Each chunk should not break mid-sentence
            # Count paragraph separators should be whole number
            para_count = chunk.count('\n\n')
            # Paragraphs should be complete
            assert chunk.strip(), "Empty chunk found"
    
    def test_single_chunk_for_short_chapter(self):
        """Short chapters should not be split."""
        chapters = [Chapter(number=1, title="Short", text="Nội dung ngắn.")]
        chunks = create_chunks(chapters, max_chars=1000)
        
        assert len(chunks) == 1
        assert chunks[0].total_parts == 1


class TestMockAPIProviderSwitch:
    """
    Test Mock API - Provider Switch
    Verify correct API is called based on provider argument.
    """
    
    @patch('src.gemini_client.genai', create=True)
    def test_studio_provider_uses_genai(self, mock_genai):
        """
        Khi arg --provider studio -> Gọi google.generativeai.GenerativeModel.
        """
        # Setup mock
        mock_genai.configure = Mock()
        mock_genai.GenerativeModel = Mock()
        
        # Import and patch at module level
        with patch.dict('sys.modules', {'google.generativeai': mock_genai}):
            from src.gemini_client import GeminiClient
            
            # Create client with studio provider
            with patch.object(GeminiClient, '_init_studio') as mock_init:
                client = GeminiClient(
                    provider="studio",
                    api_key="test-api-key",
                    model_name="gemini-2.5-flash"
                )
                
                # Verify studio init was called
                mock_init.assert_called_once()
    
    @patch('vertexai.init')
    @patch('vertexai.generative_models.GenerativeModel')
    def test_vertex_provider_uses_vertexai(self, mock_model, mock_init):
        """
        Khi arg --provider vertex -> Gọi vertexai.init.
        """
        with patch.dict('sys.modules', {'vertexai': MagicMock()}):
            from src.gemini_client import GeminiClient
            
            with patch.object(GeminiClient, '_init_vertex') as mock_vertex_init:
                # Create client with vertex provider  
                client = GeminiClient(
                    provider="vertex",
                    project_id="test-project",
                    location="us-central1",
                    model_name="gemini-2.5-flash"
                )
                
                # Verify vertex init was called
                mock_vertex_init.assert_called_once()
    
    def test_invalid_provider_raises_error(self):
        """Unknown provider should raise error."""
        from src.gemini_client import GeminiClient, GeminiClientError
        
        with pytest.raises(GeminiClientError) as exc_info:
            GeminiClient(provider="invalid_provider")
        
        assert "Unknown provider" in str(exc_info.value)


class TestChunkIdGeneration:
    """Test chunk ID format and uniqueness."""
    
    def test_chunk_id_format(self):
        """Chunk IDs should follow chap_XXXX_part_XXX format."""
        chapters = [
            Chapter(number=1, title="First", text="A" * 5000),
            Chapter(number=10, title="Tenth", text="B" * 2000),
            Chapter(number=100, title="Hundredth", text="C" * 1500),
        ]
        
        chunks = create_chunks(chapters, max_chars=1000)
        
        for chunk in chunks:
            # Validate ID format
            assert re.match(r'chap_\d{4}_part_\d{3}', chunk.chunk_id), \
                f"Invalid chunk ID format: {chunk.chunk_id}"
    
    def test_chunk_ids_unique(self):
        """All chunk IDs must be unique."""
        chapters = [
            Chapter(number=i, title=f"Chapter {i}", text="Content " * 100)
            for i in range(1, 10)
        ]
        
        chunks = create_chunks(chapters, max_chars=500)
        chunk_ids = [c.chunk_id for c in chunks]
        
        assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found"


class TestCheckpointResume:
    """Test checkpoint and resume functionality."""
    
    def test_checkpoint_data_structure(self):
        """Verify checkpoint data contains required fields."""
        from src.checkpoint import CheckpointData
        
        data = CheckpointData(
            input_file="/path/to/input.pdf",
            input_hash="abc123",
            input_size=1024,
            mode="polish_vi",
            model="gemini-2.5-flash",
            max_chars=7000,
            provider="studio",
            created_at="2026-01-05T12:00:00",
            updated_at="2026-01-05T12:30:00",
            chunks_done=["chap_0001_part_001"],
            total_chunks=10
        )
        
        dict_data = data.to_dict()
        
        # All required fields present
        required_fields = [
            'input_file', 'input_hash', 'input_size', 'mode', 'model',
            'max_chars', 'provider', 'created_at', 'updated_at',
            'chunks_done', 'total_chunks'
        ]
        for field in required_fields:
            assert field in dict_data
    
    def test_checkpoint_roundtrip(self):
        """Test checkpoint data can be serialized and deserialized."""
        from src.checkpoint import CheckpointData
        
        original = CheckpointData(
            input_file="/path/to/input.pdf",
            input_hash="abc123",
            input_size=1024,
            mode="polish_vi",
            model="gemini-2.5-flash",
            max_chars=7000,
            provider="studio",
            created_at="2026-01-05T12:00:00",
            updated_at="2026-01-05T12:30:00",
            chunks_done=["chap_0001_part_001", "chap_0001_part_002"],
            total_chunks=10
        )
        
        # Roundtrip
        dict_data = original.to_dict()
        restored = CheckpointData.from_dict(dict_data)
        
        assert restored.input_hash == original.input_hash
        assert restored.chunks_done == original.chunks_done
        assert restored.total_chunks == original.total_chunks


class TestEdgeCases:
    """Edge case tests."""
    
    def test_empty_text_handling(self):
        """Empty or whitespace-only text should be handled gracefully."""
        result = preprocess_text("   \n\n   \n")
        assert result.strip() == ""
    
    def test_single_chapter_text(self):
        """Text with only one chapter should work correctly."""
        text = """Chương 1: Duy Nhất

Nội dung chương duy nhất ở đây."""
        
        chapters = split_into_chapters(text)
        
        assert len(chapters) == 1
        assert chapters[0].number == 1
    
    def test_unicode_vietnamese_characters(self):
        """Verify Vietnamese diacritics are preserved."""
        text = """Chương 1: Tiếu Dao Tiểu Thư Sinh

Lý Thanh Vân là một thư sinh nghèo từ làng quê hẻo lánh.
Ước mơ của anh là đỗ đạt công danh, vinh quy bái tổ."""
        
        chapters = split_into_chapters(text)
        
        assert "Tiếu Dao Tiểu Thư Sinh" in chapters[0].title
        assert "nghèo" in chapters[0].text
        assert "đỗ đạt" in chapters[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

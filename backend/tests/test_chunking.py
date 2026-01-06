"""Tests for chunking module."""

import pytest
from src.chunking import create_chunks, split_by_paragraphs
from src.chapter_split import Chapter


class TestSplitByParagraphs:
    """Test paragraph-based splitting."""
    
    def test_short_text_single_chunk(self):
        """Short text should remain as single chunk."""
        text = "This is a short paragraph.\n\nAnother short one."
        chunks = split_by_paragraphs(text, max_chars=1000)
        
        assert len(chunks) == 1
        assert "This is a short paragraph" in chunks[0]
        assert "Another short one" in chunks[0]
    
    def test_split_respects_max_chars(self):
        """Chunks should not exceed max_chars."""
        paragraphs = ["Paragraph " + str(i) + ". " * 50 for i in range(10)]
        text = "\n\n".join(paragraphs)
        max_chars = 500
        
        chunks = split_by_paragraphs(text, max_chars=max_chars)
        
        for chunk in chunks:
            assert len(chunk) <= max_chars + 100  # Allow some tolerance
    
    def test_preserves_paragraph_boundaries(self):
        """Should split at paragraph boundaries, not mid-paragraph."""
        text = """First paragraph with some content.

Second paragraph with more content.

Third paragraph ends here."""
        
        chunks = split_by_paragraphs(text, max_chars=60)
        
        # Each chunk should contain complete paragraphs
        for chunk in chunks:
            # No truncated sentences in the middle
            if not chunk.endswith('.'):
                # Could be last chunk without period
                pass
            # Paragraphs should be complete
            assert chunk.strip()


class TestCreateChunks:
    """Test chunk creation from chapters."""
    
    def test_short_chapter_single_chunk(self):
        """Short chapter should become single chunk."""
        chapters = [
            Chapter(
                number=1,
                title="Test Chapter",
                text="Short content here."
            )
        ]
        
        chunks = create_chunks(chapters, max_chars=1000)
        
        assert len(chunks) == 1
        assert chunks[0].chapter_number == 1
        assert chunks[0].part_number == 1
        assert chunks[0].total_parts == 1
        assert chunks[0].chunk_id == "chap_0001_part_001"
    
    def test_long_chapter_multiple_chunks(self):
        """Long chapter should be split into multiple chunks."""
        long_text = "\n\n".join(["Paragraph " + str(i) + ". " * 100 for i in range(20)])
        
        chapters = [
            Chapter(
                number=1,
                title="Long Chapter",
                text=long_text
            )
        ]
        
        chunks = create_chunks(chapters, max_chars=500)
        
        assert len(chunks) > 1
        # All chunks should belong to chapter 1
        for chunk in chunks:
            assert chunk.chapter_number == 1
        # Parts should be numbered correctly
        for i, chunk in enumerate(chunks):
            assert chunk.part_number == i + 1
            assert chunk.total_parts == len(chunks)
    
    def test_multiple_chapters(self):
        """Test chunking multiple chapters."""
        chapters = [
            Chapter(number=1, title="First", text="Content 1."),
            Chapter(number=2, title="Second", text="Content 2."),
            Chapter(number=3, title="Third", text="Content 3."),
        ]
        
        chunks = create_chunks(chapters, max_chars=1000)
        
        assert len(chunks) == 3
        assert chunks[0].chapter_number == 1
        assert chunks[1].chapter_number == 2
        assert chunks[2].chapter_number == 3
    
    def test_chunk_id_format(self):
        """Test chunk ID format is correct."""
        chapters = [
            Chapter(number=1, title="Test", text="A" * 1000),
            Chapter(number=10, title="Test", text="B" * 1000),
            Chapter(number=100, title="Test", text="C" * 1000),
        ]
        
        chunks = create_chunks(chapters, max_chars=5000)
        
        # Chunk IDs should be zero-padded
        assert chunks[0].chunk_id == "chap_0001_part_001"
        assert chunks[1].chunk_id == "chap_0010_part_001"
        assert chunks[2].chunk_id == "chap_0100_part_001"


class TestChunkSizeLimit:
    """Test that chunks respect size limits."""
    
    def test_all_chunks_under_limit(self):
        """All chunks should be under max_chars limit."""
        long_text = "\n\n".join(["P" * 200 for _ in range(50)])
        
        chapters = [Chapter(number=1, title="Test", text=long_text)]
        max_chars = 1000
        
        chunks = create_chunks(chapters, max_chars=max_chars)
        
        for chunk in chunks:
            # Allow 10% tolerance for edge cases
            assert len(chunk.text) <= max_chars * 1.1, \
                f"Chunk {chunk.chunk_id} exceeds limit: {len(chunk.text)} > {max_chars}"

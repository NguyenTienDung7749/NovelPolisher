"""Text chunking module for splitting long chapters into processable parts."""

from dataclasses import dataclass
from typing import List

from .chapter_split import Chapter
from .utils import log_message


@dataclass
class Chunk:
    """Represents a chunk of text to be processed."""
    chapter_number: int
    chapter_title: str
    part_number: int
    total_parts: int
    text: str
    chunk_id: str  # Unique identifier for checkpointing
    
    def __repr__(self) -> str:
        return f"Chunk({self.chunk_id}, {len(self.text)} chars)"


def split_by_paragraphs(text: str, max_chars: int) -> List[str]:
    """
    Split text into chunks by paragraph boundaries.
    
    Args:
        text: Text to split
        max_chars: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    # Split by double newline (paragraph boundary)
    paragraphs = text.split('\n\n')
    
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        para_len = len(para)
        
        # If single paragraph exceeds max, we need to split it
        if para_len > max_chars:
            # First, save current chunk if any
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # Split long paragraph by sentences
            sentences = split_by_sentences(para)
            for sentence in sentences:
                sent_len = len(sentence)
                if current_length + sent_len + 1 > max_chars and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(sentence)
                current_length += sent_len + 2  # +2 for \n\n
        else:
            # Check if adding this paragraph exceeds limit
            if current_length + para_len + 2 > max_chars and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(para)
            current_length += para_len + 2
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def split_by_sentences(text: str) -> List[str]:
    """Split text into sentences for fine-grained splitting."""
    import re
    
    # Split by sentence-ending punctuation followed by space or newline
    # Keep the punctuation with the sentence
    pattern = r'(?<=[.!?…。！？])\s+'
    sentences = re.split(pattern, text)
    
    return [s.strip() for s in sentences if s.strip()]


def create_chunks(chapters: List[Chapter], max_chars: int = 7000) -> List[Chunk]:
    """
    Create processable chunks from chapters.
    
    Args:
        chapters: List of Chapter objects
        max_chars: Maximum characters per chunk (default 7000, must be > 0)
        
    Returns:
        List of Chunk objects
        
    Raises:
        ValueError: If max_chars is not positive
    """
    if max_chars <= 0:
        raise ValueError(f"max_chars must be positive, got {max_chars}")
    
    log_message(f"Creating chunks with max_chars={max_chars}...")
    
    all_chunks: List[Chunk] = []
    
    for chapter in chapters:
        chapter_text = chapter.text.strip()
        
        if len(chapter_text) <= max_chars:
            # Single chunk for this chapter
            chunk_id = f"chap_{chapter.number:04d}_part_001"
            all_chunks.append(Chunk(
                chapter_number=chapter.number,
                chapter_title=chapter.title,
                part_number=1,
                total_parts=1,
                text=chapter_text,
                chunk_id=chunk_id
            ))
        else:
            # Split into multiple chunks
            text_parts = split_by_paragraphs(chapter_text, max_chars)
            total_parts = len(text_parts)
            
            for i, part_text in enumerate(text_parts, start=1):
                chunk_id = f"chap_{chapter.number:04d}_part_{i:03d}"
                all_chunks.append(Chunk(
                    chapter_number=chapter.number,
                    chapter_title=chapter.title,
                    part_number=i,
                    total_parts=total_parts,
                    text=part_text,
                    chunk_id=chunk_id
                ))
    
    log_message(f"Created {len(all_chunks)} chunks from {len(chapters)} chapters")
    
    # Log summary of multi-part chapters (only count, not each one)
    multi_part_chapters = len(set(c.chapter_number for c in all_chunks if c.total_parts > 1))
    if multi_part_chapters > 0:
        log_message(f"  {multi_part_chapters} chapters were split into multiple parts")
    
    return all_chunks


def get_chunk_context(chunk: Chunk) -> str:
    """Get context string for a chunk (used in prompts)."""
    if chunk.total_parts == 1:
        return f"Chương {chunk.chapter_number}: {chunk.chapter_title}"
    else:
        return f"Chương {chunk.chapter_number}: {chunk.chapter_title} — Phần {chunk.part_number}/{chunk.total_parts}"

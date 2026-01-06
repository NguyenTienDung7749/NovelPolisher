"""Checkpoint management for resume support."""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .utils import calculate_file_hash, get_file_size, ensure_dir, log_message


@dataclass
class CheckpointData:
    """Checkpoint data structure."""
    input_file: str
    input_hash: str
    input_size: int
    mode: str
    model: str
    max_chars: int
    provider: str
    created_at: str
    updated_at: str
    chunks_done: List[str]
    total_chunks: int
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointData":
        return cls(**data)


class CheckpointManager:
    """Manages checkpoint saving and loading for resume functionality."""
    
    def __init__(self, checkpoint_path: Path, chunks_dir: Path):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_path: Path to checkpoint.json file
            chunks_dir: Directory to save processed chunks
        """
        self.checkpoint_path = checkpoint_path
        self.chunks_dir = chunks_dir
        self._data: Optional[CheckpointData] = None
        self._chunks_done: Set[str] = set()
        self._dirs_ensured: bool = False  # Cache to avoid repeated ensure_dir calls
    
    def initialize(
        self,
        input_file: Path,
        mode: str,
        model: str,
        max_chars: int,
        provider: str,
        total_chunks: int
    ) -> bool:
        """
        Initialize or load checkpoint.
        
        Returns:
            True if resuming from existing checkpoint, False if starting fresh
        """
        # Calculate input file hash
        input_hash = calculate_file_hash(input_file)
        input_size = get_file_size(input_file)
        
        # Check for existing checkpoint
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                    existing = CheckpointData.from_dict(json.load(f))
                
                # Validate checkpoint matches current run
                if (existing.input_hash == input_hash and
                    existing.mode == mode and
                    existing.model == model and
                    existing.max_chars == max_chars and
                    existing.provider == provider):
                    
                    self._data = existing
                    self._chunks_done = set(existing.chunks_done)
                    log_message(f"Resuming from checkpoint: {len(self._chunks_done)}/{total_chunks} chunks done")
                    return True
                else:
                    log_message("Checkpoint exists but parameters differ. Starting fresh.")
            except Exception as e:
                log_message(f"Could not load checkpoint: {e}. Starting fresh.")
        
        # Create new checkpoint
        now = datetime.now().isoformat()
        self._data = CheckpointData(
            input_file=str(input_file),
            input_hash=input_hash,
            input_size=input_size,
            mode=mode,
            model=model,
            max_chars=max_chars,
            provider=provider,
            created_at=now,
            updated_at=now,
            chunks_done=[],
            total_chunks=total_chunks
        )
        self._chunks_done = set()
        
        # Ensure directories exist
        ensure_dir(self.checkpoint_path.parent)
        ensure_dir(self.chunks_dir)
        
        self._save()
        return False
    
    def is_chunk_done(self, chunk_id: str) -> bool:
        """Check if a chunk has been processed."""
        # Also check if output file exists
        chunk_file = self.chunks_dir / f"{chunk_id}.md"
        return chunk_id in self._chunks_done and chunk_file.exists()
    
    def mark_chunk_done(self, chunk_id: str, output_text: str):
        """Mark a chunk as processed and save its output."""
        # Save chunk output - only ensure dir once for performance
        chunk_file = self.chunks_dir / f"{chunk_id}.md"
        if not self._dirs_ensured:
            ensure_dir(self.chunks_dir)
            self._dirs_ensured = True
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
        
        # Update checkpoint
        self._chunks_done.add(chunk_id)
        if self._data:
            self._data.chunks_done = list(self._chunks_done)
            self._data.updated_at = datetime.now().isoformat()
        
        self._save()
    
    def get_chunk_output(self, chunk_id: str) -> Optional[str]:
        """Get saved output for a chunk."""
        chunk_file = self.chunks_dir / f"{chunk_id}.md"
        if chunk_file.exists():
            with open(chunk_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def get_progress(self) -> tuple:
        """Get current progress as (done, total)."""
        if self._data:
            return len(self._chunks_done), self._data.total_chunks
        return 0, 0
    
    def _save(self):
        """Save checkpoint to file."""
        if self._data:
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(self._data.to_dict(), f, indent=2, ensure_ascii=False)
    
    def clear(self):
        """Clear checkpoint and all chunk files."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
        
        if self.chunks_dir.exists():
            for chunk_file in self.chunks_dir.glob("*.md"):
                chunk_file.unlink()
        
        self._data = None
        self._chunks_done = set()
        log_message("Checkpoint cleared")

"""Utility functions for the backend."""

import hashlib
import sys
from pathlib import Path
from typing import Optional


def calculate_file_hash(filepath: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file for checkpoint validation."""
    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_size(filepath: Path) -> int:
    """Get file size in bytes."""
    return filepath.stat().st_size


def log_status(stage: str, **kwargs) -> None:
    """Print STATUS line for WPF to parse."""
    parts = [f"{k}=\"{v}\"" for k, v in kwargs.items()]
    print(f"STATUS stage={stage} {' '.join(parts)}", flush=True)


def log_progress(percent: int, chapter: int, part: str) -> None:
    """Print PROGRESS line for WPF to parse."""
    print(f"PROGRESS percent={percent} chapter={chapter} part={part}", flush=True)


def log_message(message: str) -> None:
    """Print LOG line for WPF to parse."""
    # Escape quotes in message
    safe_message = message.replace('"', '\\"')
    print(f'LOG message="{safe_message}"', flush=True)


def log_done(outdir: str, docx: str) -> None:
    """Print DONE line for WPF to parse."""
    print(f'DONE outdir="{outdir}" docx="{docx}"', flush=True)


def log_error(code: int, message: str) -> None:
    """Print ERROR line for WPF to parse."""
    safe_message = message.replace('"', '\\"')
    print(f'ERROR code={code} message="{safe_message}"', flush=True)


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str, max_length: int = 50) -> str:
    """Convert string to safe filename."""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        name = name.replace(char, '_')
    # Truncate if too long
    if len(name) > max_length:
        name = name[:max_length]
    return name.strip()

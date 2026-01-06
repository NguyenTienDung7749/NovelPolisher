
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath('src'))

def test_imports():
    print("Testing imports...")
    try:
        from src.pdf_extract import extract_text_from_pdf
        from src.preprocess import preprocess_text
        from src.chapter_split import split_into_chapters
        from src.chunking import create_chunks
        from src.gemini_client import GeminiClient
        from src.exporters import export_to_docx
        from src.utils import calculate_file_hash
        print("✅ All modules imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

def test_chapter_flow():
    print("\nTesting chapter flow...")
    from src.chapter_split import split_into_chapters
    from src.chunking import create_chunks
    
    text = "Chương 1: Test\nContent 1.\nChương 2: Test 2\nContent 2."
    chapters = split_into_chapters(text)
    if len(chapters) == 2:
        print(f"✅ Split chapters: Found {len(chapters)}")
    else:
        print(f"❌ Split chapters failed: Found {len(chapters)}")
        
    chunks = create_chunks(chapters, max_chars=1000)
    if len(chunks) == 2:
        print(f"✅ Chunking: Created {len(chunks)} chunks")
    else:
        print(f"❌ Chunking failed: Created {len(chunks)}")
        
    # Test max_chars validation fix
    try:
        create_chunks(chapters, max_chars=0)
        print("❌ Validation check failed (should raise ValueError)")
    except ValueError:
        print("✅ Validation check passed (raised ValueError as expected)")

if __name__ == "__main__":
    test_imports()
    test_chapter_flow()
    print("\n🎉 Verification Completed")

"""Main CLI entry point for Novel Polisher backend."""

import argparse
import io
import sys
import time
from pathlib import Path
from typing import Optional

# ============================================
# CRITICAL: Force UTF-8 encoding on Windows
# This prevents Vietnamese character corruption
# when WPF C# reads stdout from Python process
# ============================================
if sys.platform == 'win32':
    # Wrap stdout/stderr with UTF-8 encoding
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace',
        line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, 
        encoding='utf-8', 
        errors='replace',
        line_buffering=True
    )

try:
    from src.pdf_extract import extract_text_from_pdf, PDFExtractionError, ScanBasedPDFError
    from src.preprocess import preprocess_text
    from src.chapter_split import split_into_chapters, validate_chapters
    from src.chunking import create_chunks
    from src.prompts import get_system_prompt, build_user_prompt, load_style_file, load_glossary_file
    from src.gemini_client import GeminiClient, GeminiClientError
    from src.checkpoint import CheckpointManager
    from src.exporters import export_to_docx, export_to_markdown, collect_chunk_outputs
    from src.utils import log_status, log_progress, log_message, log_done, log_error, ensure_dir
except ImportError:
    # Fallback for when running as script/PyInstaller without src package
    from pdf_extract import extract_text_from_pdf, PDFExtractionError, ScanBasedPDFError
    from preprocess import preprocess_text
    from chapter_split import split_into_chapters, validate_chapters
    from chunking import create_chunks
    from prompts import get_system_prompt, build_user_prompt, load_style_file, load_glossary_file
    from gemini_client import GeminiClient, GeminiClientError
    from checkpoint import CheckpointManager
    from exporters import export_to_docx, export_to_markdown, collect_chunk_outputs
    from utils import log_status, log_progress, log_message, log_done, log_error, ensure_dir


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Novel Polisher - Polish Vietnamese novels with Gemini AI"
    )
    
    # Required
    parser.add_argument("--input", "-i", required=True, help="Input PDF file path")
    
    # Output options
    parser.add_argument("--outdir", "-o", default="out", help="Output directory (default: out)")
    parser.add_argument("--export", choices=["docx", "md", "all"], default="docx",
                       help="Export format (default: docx)")
    
    # Processing mode
    parser.add_argument("--mode", "-m", choices=["polish_vi", "translate_en"],
                       default="polish_vi", help="Processing mode (default: polish_vi)")
    
    # Provider options
    parser.add_argument("--provider", choices=["studio", "vertex"], default="studio",
                       help="AI provider (default: studio)")
    parser.add_argument("--api-key", help="API key for AI Studio")
    parser.add_argument("--project-id", help="GCP Project ID for Vertex AI")
    parser.add_argument("--location", default="us-central1", help="GCP location for Vertex AI")
    parser.add_argument("--auth-file", help="Service account JSON path for Vertex AI")
    
    # Model options
    parser.add_argument("--model", default="gemini-1.5-pro", help="Model name")
    
    # Page range
    parser.add_argument("--start-page", type=int, default=1, help="Start page (default: 1)")
    parser.add_argument("--end-page", type=int, default=0, help="End page (0 = to end)")
    
    # Processing options
    parser.add_argument("--max-chars", type=int, default=7000,
                       help="Max characters per chunk (default: 7000)")
    parser.add_argument("--sleep-ms", type=int, default=250,
                       help="Sleep between API calls in ms (default: 250)")
    
    # Style and glossary
    parser.add_argument("--style", help="Path to style.yaml file")
    parser.add_argument("--glossary", help="Path to glossary.json file")
    
    # Checkpoint
    parser.add_argument("--checkpoint", help="Path to checkpoint.json (default: outdir/checkpoint.json)")
    parser.add_argument("--overwrite", action="store_true",
                       help="Clear checkpoint and start fresh")
    
    return parser.parse_args()


def find_default_style_glossary(input_path: Path) -> tuple:
    """Find default style.yaml and glossary.json in script or input directory."""
    style_path = None
    glossary_path = None
    
    # Check script directory first (for bundled exe)
    # Handle PyInstaller frozen executables
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        script_dir = Path(sys.executable).parent
    else:
        # Running as normal Python script
        script_dir = Path(__file__).parent.parent
    
    for search_dir in [script_dir, input_path.parent, Path.cwd()]:
        if not style_path:
            candidate = search_dir / "style.yaml"
            if candidate.exists():
                style_path = candidate
        if not glossary_path:
            candidate = search_dir / "glossary.json"
            if candidate.exists():
                glossary_path = candidate
    
    return style_path, glossary_path


def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate input
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        log_error(1, f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Setup output directory
    outdir = Path(args.outdir).resolve()
    ensure_dir(outdir)
    chunks_dir = outdir / "chunks"
    
    # Checkpoint path
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else outdir / "checkpoint.json"
    
    # Find style and glossary files
    style_path = Path(args.style) if args.style else None
    glossary_path = Path(args.glossary) if args.glossary else None
    
    if not style_path or not glossary_path:
        default_style, default_glossary = find_default_style_glossary(input_path)
        if not style_path and default_style:
            style_path = default_style
            log_message(f"Using default style: {style_path}")
        if not glossary_path and default_glossary:
            glossary_path = default_glossary
            log_message(f"Using default glossary: {glossary_path}")
    
    # Log start
    log_status("START", input=str(input_path), outdir=str(outdir))
    
    try:
        # Step 1: Extract PDF text
        log_message("Extracting text from PDF...")
        full_text, page_texts = extract_text_from_pdf(
            input_path,
            start_page=args.start_page,
            end_page=args.end_page
        )
        
        # Step 2: Preprocess text
        log_message("Preprocessing text...")
        clean_text = preprocess_text(full_text, page_texts)
        
        # Step 3: Split into chapters
        log_message("Splitting into chapters...")
        chapters = split_into_chapters(clean_text)
        
        # Validate chapters
        warnings = validate_chapters(chapters)
        for warning in warnings:
            log_message(f"Warning: {warning}")
        
        # Step 4: Create chunks
        chunks = create_chunks(chapters, max_chars=args.max_chars)
        total_chunks = len(chunks)
        
        # Step 5: Initialize checkpoint
        checkpoint = CheckpointManager(checkpoint_path, chunks_dir)
        
        if args.overwrite:
            log_message("Overwrite flag set - clearing existing checkpoint")
            checkpoint.clear()
        
        is_resuming = checkpoint.initialize(
            input_file=input_path,
            mode=args.mode,
            model=args.model,
            max_chars=args.max_chars,
            provider=args.provider,
            total_chunks=total_chunks
        )
        
        # Step 6: Initialize Gemini client
        log_message(f"Initializing {args.provider.upper()} client...")
        client = GeminiClient(
            provider=args.provider,
            model_name=args.model,
            api_key=args.api_key,
            project_id=args.project_id,
            location=args.location,
            auth_file=args.auth_file,
            temperature=0.2,
            max_output_tokens=8192
        )
        
        # Set system prompt
        system_prompt = get_system_prompt(args.mode)
        client.set_system_instruction(system_prompt)
        
        # Load style and glossary content
        style_content = load_style_file(style_path)
        glossary_content = load_glossary_file(glossary_path)
        
        # Step 7: Process chunks
        log_message("Processing chunks with AI...")
        sleep_seconds = args.sleep_ms / 1000.0
        
        processed_count = 0
        for i, chunk in enumerate(chunks):
            # Check if already done
            if checkpoint.is_chunk_done(chunk.chunk_id):
                processed_count += 1
                percent = int((processed_count / total_chunks) * 100)
                log_progress(percent, chunk.chapter_number, f"{chunk.part_number}/{chunk.total_parts}")
                continue
            
            # Build prompt
            user_prompt = build_user_prompt(chunk, style_content, glossary_content)
            
            # Call API
            log_message(f"Processing: Chapter {chunk.chapter_number}, Part {chunk.part_number}/{chunk.total_parts}")
            
            try:
                output_text = client.generate(user_prompt)
                
                # Save result
                checkpoint.mark_chunk_done(chunk.chunk_id, output_text)
                processed_count += 1
                
                percent = int((processed_count / total_chunks) * 100)
                log_progress(percent, chunk.chapter_number, f"{chunk.part_number}/{chunk.total_parts}")
                
                # Sleep between requests
                if i < len(chunks) - 1:
                    time.sleep(sleep_seconds)
                    
            except GeminiClientError as e:
                log_error(2, f"API error on chunk {chunk.chunk_id}: {e}")
                sys.exit(2)
        
        # Step 8: Export results
        log_message("Exporting results...")
        
        # Get input filename for title
        title = input_path.stem
        
        # Collect all chunk outputs
        chunk_outputs = collect_chunk_outputs(chunks, chunks_dir)
        
        docx_path = None
        md_path = None
        
        # Export DOCX (default)
        if args.export in ["docx", "all"]:
            docx_path = outdir / "polished.docx"
            export_to_docx(chunks, chunk_outputs, docx_path, title=title, mode=args.mode)
        
        # Export Markdown
        if args.export in ["md", "all"]:
            md_path = outdir / "polished.md"
            export_to_markdown(chunks, chunk_outputs, md_path, title=title, mode=args.mode)
        
        # Always create backup MD even if not explicitly requested
        if args.export == "docx":
            md_path = outdir / "polished.md"
            export_to_markdown(chunks, chunk_outputs, md_path, title=title, mode=args.mode)
        
        # Final output
        output_file = docx_path if docx_path else md_path
        log_done(str(outdir), str(output_file))
        
        log_message("Processing complete!")
        
    except PDFExtractionError as e:
        log_error(10, str(e))
        sys.exit(10)
    except ScanBasedPDFError as e:
        log_error(11, str(e))
        sys.exit(11)
    except GeminiClientError as e:
        log_error(20, str(e))
        sys.exit(20)
    except KeyboardInterrupt:
        log_message("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        log_error(99, f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(99)


if __name__ == "__main__":
    main()

"""
Script to convert all PDF files in the data directory to TXT format.
This script extracts text from PDFs and saves them as .txt files.
"""
import os
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader


def get_data_dir() -> Path:
    """Get the data directory path."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = project_root / "backend" / "data"
    return data_dir


def convert_pdf_to_txt(pdf_path: Path, output_dir: Optional[Path] = None) -> bool:
    """
    Convert a single PDF file to TXT format.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the TXT file (defaults to same directory as PDF)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Converting: {pdf_path.name}")
        
        # Load PDF
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        
        # Combine all pages into a single text
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        # Determine output path
        if output_dir is None:
            output_dir = pdf_path.parent
        
        # Create output filename (replace .pdf with .txt)
        txt_filename = pdf_path.stem + ".txt"
        txt_path = output_dir / txt_filename
        
        # Write text to file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        # Count pages and characters
        page_count = len(documents)
        char_count = len(full_text)
        print(f"  [OK] Converted: {txt_filename} ({page_count} pages, {char_count:,} characters)")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to convert {pdf_path.name}: {e}")
        return False


def convert_all_pdfs(data_dir: Path, overwrite: bool = False) -> dict:
    """
    Convert all PDF files in the data directory to TXT format.
    
    Args:
        data_dir: Directory containing PDF files
        overwrite: If True, overwrite existing TXT files
    
    Returns:
        Dictionary with conversion statistics
    """
    if not data_dir.exists():
        print(f"Error: Data directory does not exist: {data_dir}")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    print(f"Found {len(pdf_files)} PDF file(s) to convert...\n")
    
    stats = {"success": 0, "failed": 0, "skipped": 0}
    
    for pdf_path in pdf_files:
        txt_path = data_dir / (pdf_path.stem + ".txt")
        
        # Check if TXT already exists
        if txt_path.exists() and not overwrite:
            print(f"Skipping: {pdf_path.name} (TXT already exists, use --overwrite to replace)")
            stats["skipped"] += 1
            continue
        
        # Convert PDF to TXT
        if convert_pdf_to_txt(pdf_path, data_dir):
            stats["success"] += 1
        else:
            stats["failed"] += 1
    
    print(f"\n{'='*60}")
    print(f"Conversion Summary:")
    print(f"  Success: {stats['success']}")
    print(f"  Failed:  {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"{'='*60}")
    
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert PDF files to TXT format")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing TXT files"
    )
    args = parser.parse_args()
    
    data_dir = get_data_dir()
    convert_all_pdfs(data_dir, overwrite=args.overwrite)

"""
Script to download NYSC official documents from URLs and save them to backend/data.

Usage:
    python backend/scripts/download_nysc_docs.py
    
    Or with specific URLs:
    python backend/scripts/download_nysc_docs.py --urls "https://nysc.gov.ng/doc1.pdf" "https://nysc.gov.ng/doc2.pdf"
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Optional


# Default NYSC document URLs (update these with actual URLs from nysc.gov.ng)
DEFAULT_NYSC_URLS = [
    # Add official NYSC document URLs here when you find them
    # Example:
    # "https://www.nysc.gov.ng/downloads/nysc-handbook.pdf",
    # "https://www.nysc.gov.ng/downloads/redeployment-guidelines.pdf",
]


def get_data_dir() -> Path:
    """Get the backend/data directory path."""
    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def download_pdf(url: str, output_dir: Path, timeout: int = 30, force: bool = False) -> Optional[str]:
    """
    Download a PDF from a URL and save it to the output directory.
    
    Returns:
        The filename if successful, None if failed.
    """
    try:
        print(f"Downloading: {url}")
        
        # Make request with headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            print(f"  ⚠️  Warning: Content-Type is {content_type}, not PDF. Downloading anyway...")
        
        # Extract filename from URL or use a default
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or not filename.endswith(".pdf"):
            # Generate a filename from the URL
            filename = f"nysc_document_{hash(url) % 10000}.pdf"
        
        # Sanitize filename (remove invalid characters)
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        
        output_path = output_dir / filename
        
        # Skip if file already exists (unless force is True)
        if output_path.exists() and not force:
            print(f"  ⏭️  File already exists: {filename} (use --force to overwrite)")
            return filename
        
        # Download and save
        total_size = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        file_size_mb = total_size / (1024 * 1024)
        print(f"  ✓ Downloaded: {filename} ({file_size_mb:.2f} MB)")
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to download {url}: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Error processing {url}: {e}")
        return None


def download_from_urls(urls: List[str], output_dir: Path, force: bool = False) -> dict:
    """
    Download multiple PDFs from a list of URLs.
    
    Returns:
        Dictionary with success/failure counts.
    """
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for url in urls:
        url = url.strip()
        if not url or url.startswith("#"):
            continue
            
        result = download_pdf(url, output_dir, force=force)
        if result:
            results["success"] += 1
        else:
            results["failed"] += 1
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Download NYSC official documents from URLs and save to backend/data"
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="URLs of PDF documents to download",
        default=None,
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing URLs (one per line)",
        default=None,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
        default=False,
    )
    
    args = parser.parse_args()
    
    data_dir = get_data_dir()
    print(f"📁 Saving documents to: {data_dir}\n")
    
    # Collect URLs
    urls = []
    
    if args.urls:
        urls.extend(args.urls)
    elif args.file:
        file_path = Path(args.file)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                urls.extend([line.strip() for line in f if line.strip()])
        else:
            print(f"✗ Error: File not found: {args.file}")
            sys.exit(1)
    else:
        # Use default URLs if provided
        if DEFAULT_NYSC_URLS:
            urls.extend(DEFAULT_NYSC_URLS)
        else:
            print("ℹ️  No URLs provided. Use --urls or --file to specify documents to download.")
            print("\nExample usage:")
            print("  python backend/scripts/download_nysc_docs.py --urls https://nysc.gov.ng/doc.pdf")
            print("  python backend/scripts/download_nysc_docs.py --file urls.txt")
            sys.exit(0)
    
    if not urls:
        print("✗ No URLs to download.")
        sys.exit(1)
    
    print(f"📥 Downloading {len(urls)} document(s)...\n")
    
    # Download all URLs
    results = download_from_urls(urls, data_dir, force=args.force)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   ✓ Successfully downloaded: {results['success']}")
    print(f"   ✗ Failed: {results['failed']}")
    print(f"   📁 Files saved to: {data_dir}")
    print(f"{'='*60}\n")
    
    if results["success"] > 0:
        print("✅ Documents are ready! Restart your backend to index them.")
    else:
        print("⚠️  No documents were downloaded. Check the URLs and try again.")


if __name__ == "__main__":
    main()

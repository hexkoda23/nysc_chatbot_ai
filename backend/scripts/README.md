# NYSC Document Download Script

This script downloads official NYSC PDF documents from URLs and saves them to `backend/data/`.

## Installation

Make sure you have the required dependencies:

```bash
pip install requests
```

(Or install all requirements: `pip install -r backend/requirements.txt`)

## Usage

### Option 1: Download from specific URLs

```bash
python backend/scripts/download_nysc_docs.py --urls "https://nysc.gov.ng/doc1.pdf" "https://nysc.gov.ng/doc2.pdf"
```

### Option 2: Download from a URLs file

1. Create a text file (e.g., `nysc_urls.txt`) with one URL per line:
   ```
   https://www.nysc.gov.ng/downloads/nysc-handbook.pdf
   https://www.nysc.gov.ng/downloads/redeployment-guidelines.pdf
   https://www.nysc.gov.ng/downloads/camp-rules.pdf
   ```

2. Run the script:
   ```bash
   python backend/scripts/download_nysc_docs.py --file nysc_urls.txt
   ```

### Option 3: Use default URLs (edit the script)

Edit `backend/scripts/download_nysc_docs.py` and add URLs to the `DEFAULT_NYSC_URLS` list, then run:

```bash
python backend/scripts/download_nysc_docs.py
```

## Options

- `--urls`: Space-separated list of PDF URLs to download
- `--file`: Path to a text file containing URLs (one per line)
- `--force`: Overwrite existing files (default: skip if file exists)

## Examples

```bash
# Download a single document
python backend/scripts/download_nysc_docs.py --urls "https://www.nysc.gov.ng/downloads/handbook.pdf"

# Download multiple documents
python backend/scripts/download_nysc_docs.py --urls \
  "https://www.nysc.gov.ng/downloads/doc1.pdf" \
  "https://www.nysc.gov.ng/downloads/doc2.pdf"

# Download from a file list
python backend/scripts/download_nysc_docs.py --file my_urls.txt

# Force re-download (overwrite existing files)
python backend/scripts/download_nysc_docs.py --urls "https://..." --force
```

## After Downloading

1. **Restart your backend** to index the new documents:
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```

2. The RAG engine will automatically load and index all PDFs in `backend/data/` on startup.

## Finding NYSC Document URLs

Visit the official NYSC website: https://www.nysc.gov.ng

Look for:
- **Downloads** section
- **Publications** or **Resources** pages
- **Guidelines** or **Policies** sections

Right-click on PDF links and "Copy link address" to get the URL.

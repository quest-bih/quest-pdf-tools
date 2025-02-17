# Quest PDF Tools

A FastAPI-based service for processing PDF documents, providing comprehensive document analysis and content extraction capabilities.

## Features

- **PDF Layout Analysis**: Detects and annotates different document elements including titles, text blocks, figures, tables, and formulas
- **Irrelevant Content Removal**: Automatically identifies and removes headers, footers, and other irrelevant content from PDFs
- **Figure Extraction**: Extracts and exports figures from PDFs into separate image files
- **Table Extraction**: Identifies and exports tables from PDFs into separate files
- **Text Extraction**: Extracts plain text content from PDFs with preserved formatting
- **Markdown Conversion**: Converts PDF content into markdown format for easy integration with documentation systems
- **REST API Interface**: Simple HTTP endpoints for processing PDFs
- **YOLO-based Detection**: Utilizes DocLayout-YOLO model for accurate document layout analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/quest-bih/quest-pdf-tools.git
cd quest-pdf-tools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Start the API server:
```bash
python api.py
```

The server will start on `http://0.0.0.0:8000`

## API Endpoints

### 1. Process PDF Layout

**Endpoint**: `POST /process-pdf/`

Analyzes the PDF layout and returns an annotated version with detected elements highlighted in different colors:
- Title (Red)
- Plain Text (Green)
- Figures (Blue)
- Figure Captions (Orange)
- Tables (Purple)
- Table Captions (Teal)
- Table Footnotes (Magenta)
- Formulas (Brown)
- Formula Captions (Cyan)

```bash
curl -X POST "http://localhost:8000/process-pdf/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

### 2. Remove Irrelevant Content

**Endpoint**: `POST /remove-irrelevant/`

Identifies and removes irrelevant content (headers, footers, etc.) from the PDF.

```bash
curl -X POST "http://localhost:8000/remove-irrelevant/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

### 3. Extract Figures

Endpoint : `POST /extract-figures/`

Extracts all figures from the PDF and returns them as a ZIP file.

```bash
curl -X POST "http://localhost:8000/extract-figures/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

### 4. Extract Tables

Endpoint : `POST /extract-tables/`

Extracts all tables from the PDF and returns them as a ZIP file.

```bash
curl -X POST "http://localhost:8000/extract-tables/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

### 5. Extract Text

Endpoint : `POST /extract-text/`

Extracts all text content from the PDF and returns it as JSON.

```bash
curl -X POST "http://localhost:8000/extract-text/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

### 6. Extract Markdown

Endpoint : `POST /extract-markdown/`

Converts the PDF content to markdown format and returns it as JSON.

```bash
curl -X POST "http://localhost:8000/extract-markdown/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

## Dependencies

- FastAPI
- PyMuPDF
- DocLayout-YOLO
- Torch
- Uvicorn
- Other dependencies listed in `requirements.txt`

## License

This project is licensed under the terms of the LICENSE file included in the repository.
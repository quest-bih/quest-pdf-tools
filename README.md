# Quest PDF Tools

A FastAPI-based service for processing PDF documents, providing layout analysis and irrelevant content removal capabilities.

## Features

- **PDF Layout Analysis**: Detects and annotates different document elements including titles, text blocks, figures, tables, and formulas
- **Irrelevant Content Removal**: Automatically identifies and removes headers, footers, and other irrelevant content from PDFs
- **REST API Interface**: Simple HTTP endpoints for processing PDFs
- **YOLO-based Detection**: Utilizes DocLayout-YOLO model for accurate document layout analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quest-pdf-tools.git
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

## Dependencies

- FastAPI
- PyMuPDF
- DocLayout-YOLO
- Torch
- Uvicorn
- Other dependencies listed in `requirements.txt`

## License

This project is licensed under the terms of the LICENSE file included in the repository.
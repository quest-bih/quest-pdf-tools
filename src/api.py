from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import zipfile
import io
from pathlib import Path
import uvicorn
import shutil
import logging
from doc_layout import PDFLayoutProcessor
from pdf_processor import PDFProcessor
from dotenv import load_dotenv
import os

"""
FastAPI application for PDF processing and content extraction.

This API provides endpoints for:
- Processing PDF layouts and analyzing document structure
- Removing irrelevant content (headers, footers)
- Extracting figures, tables, text, and markdown content from PDFs
- Extracting specific sections from PDF documents

The API uses PDFLayoutProcessor and PDFProcessor classes to handle PDF operations.
All uploaded files are stored in a unique directory under the 'pdfs' folder.
"""

app = FastAPI(
    title="PDF Layout Processing API",
    description="API for processing PDF layouts and removing irrelevant boxes (headers,footers,...)",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("pdfs")
UPLOADS_DIR.mkdir(exist_ok=True)

processor = PDFLayoutProcessor()
@app.post("/process-pdf/")
async def process_pdf(file: UploadFile):
    """
    Process a PDF file to detect and analyze its layout.
    
    Args:
        file (UploadFile): The uploaded PDF file to process. Must be a valid PDF document.
        
    Returns:
        FileResponse: The processed PDF file with layout analysis results.
                     The file will have the same name as the input with '_processed' suffix.
        
    Raises:
        HTTPException (500): If processing fails due to invalid PDF or processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process PDF
        output_pdf, output_json = processor.process_pdf(str(file_path))
        
        return FileResponse(
            output_pdf,
            media_type='application/pdf',
            filename=Path(output_pdf).name
        )
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove-irrelevant/")
async def remove_irrelevant(file: UploadFile):
    """
    Remove irrelevant content (headers, footers) from a PDF file.
    
    Args:
        file (UploadFile): The uploaded PDF file to process. Must be a valid PDF document.
        
    Returns:
        FileResponse: The cleaned PDF file with irrelevant content removed.
                     The file will have the same name as the input with '_cleaned' suffix.
        
    Raises:
        HTTPException (500): If processing fails due to invalid PDF or processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process detections JSON path
        results_csv = str(file_path).replace('.pdf', '_detections.csv')
        output_pdf = str(file_path).replace('.pdf', '_cleaned.pdf')
        
        # Process PDF (convert to strings when passing to PDFProcessor)
        processor = PDFProcessor(str(file_path), str(results_csv), str(output_pdf))
        if processor.remove_irrelevant_boxes():
            return FileResponse(
                str(output_pdf),
                media_type='application/pdf',
                filename=output_pdf
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to process PDF")
    except Exception as e:
        logger.error(f"Error removing irrelevant boxes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-figures/")
async def extract_figures(file: UploadFile):
    """
    Extract figures from a PDF file and save them as individual image files.
    
    This endpoint processes a PDF file to identify and extract any figures/images
    present in the document. The extracted figures are saved as separate files
    and bundled into a ZIP archive for download.
    
    Args:
        file (UploadFile): The PDF file to extract figures from. Must be a valid PDF document.
        
    Returns:
        FileResponse: A ZIP archive containing all extracted figures as separate image files.
                     The response includes appropriate headers for file download.
        JSONResponse: A 404 status with message if no figures are found.
        
    Raises:
        HTTPException (404): If no figures are found in the PDF document.
        HTTPException (500): If figure extraction fails due to processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        output_dir = str(pdf_dir) + "/figures"

        # Create PDFProcessor instance
        processor = PDFProcessor(file_path)
        
        # Extract figures
        extracted_figures = processor.extract_figures()
        
        if not extracted_figures:
            return JSONResponse(
                status_code=404,
                content={"message": "No figures found in the PDF"}
            )

        # Create ZIP file in the PDF directory
        zip_path = pdf_dir / f"{Path(file_path).stem}_figures.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for figure_path in extracted_figures:
                zip_file.write(figure_path, Path(figure_path).name)
        
        logging.info(f"Figures extracted and saved to {output_dir}")
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_path.name
        )
    
    except Exception as e:
        logger.error(f"Error extracting figures: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-tables/")
async def extract_tables(file: UploadFile):
    """
    Extract tables from a PDF file and return them as a ZIP archive.
    
    This endpoint processes a PDF file to identify and extract any tables present in the document.
    The extracted tables are saved as individual files and bundled into a ZIP archive for download.
    
    Args:
        file (UploadFile): The PDF file to extract tables from. Must be a valid PDF document.
        
    Returns:
        FileResponse: A ZIP archive containing all extracted tables as separate files.
                     The response includes appropriate headers for file download.
        
    Raises:
        HTTPException (404): If no tables are found in the PDF document.
        HTTPException (500): If table extraction fails due to processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        output_dir = str(pdf_dir) + "/tables"

        # Create PDFProcessor instance
        processor = PDFProcessor(file_path)
        
        # Extract tables
        extracted_tables = processor.extract_tables()
        
        if not extracted_tables:
            return JSONResponse(
                status_code=404,
                content={"message": "No tables found in the PDF"}
            )

        # Create ZIP file in the PDF directory
        zip_path = pdf_dir / f"{Path(file_path).stem}_tables.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for table_path in extracted_tables:
                zip_file.write(table_path, Path(table_path).name)
        
        logging.info(f"Tables extracted and saved to {output_dir}")
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_path.name
        )
    
    except Exception as e:
        logger.error(f"Error extracting tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-text/")
async def extract_text(file: UploadFile):
    """
    Extract text content from a PDF file.
    
    This endpoint processes a PDF file to extract all text content while preserving
    the document's structure and formatting.
    
    Args:
        file (UploadFile): The PDF file to extract text from. Must be a valid PDF document.
        
    Returns:
        JSONResponse: Dictionary containing extracted text in the format:
                     {"text": "extracted text content"}
        
    Raises:
        HTTPException (404): If no text content is found in the PDF.
        HTTPException (500): If text extraction fails due to processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create PDFProcessor instance
        processor = PDFProcessor(file_path)  # Empty strings for unused parameters
        
        # Extract text
        extracted_text = processor.extract_text()
        
        if not extracted_text:
            return JSONResponse(
                status_code=404,
                content={"message": "No text found in the PDF"}
            )
        
        return JSONResponse(
            content={"text": extracted_text}
        )
    
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-markdown/")
async def extract_markdown(file: UploadFile):
    """
    Convert PDF content to markdown format.
    
    This endpoint extracts all content (text, figures, tables, formulas)
    from the PDF and converts it to markdown syntax while preserving the
    document's structure and formatting.
    
    Args:
        file (UploadFile): The PDF file to convert. Must be a valid PDF document.
        
    Returns:
        JSONResponse: Dictionary containing markdown text in the format:
                     {"markdown": "converted markdown content"}
        
    Raises:
        HTTPException (404): If no content could be converted to markdown.
        HTTPException (500): If conversion fails due to processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create PDFProcessor instance
        processor = PDFProcessor(file_path)  # Empty strings for unused parameters
        
        # Process markdown
        markdown_text = processor.extract_markdown()
        
        if not markdown_text:
            return JSONResponse(
                status_code=404,
                content={"message": "Could not convert PDF to markdown"}
            )
        
        return JSONResponse(
            content={"markdown": markdown_text}
        )
    
    except Exception as e:
        logger.error(f"Error converting to markdown: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-sections/")
async def extract_sections(
    file: UploadFile, 
    section_type: str = None
):
    """
    Extract specific sections from a PDF file.
    
    This endpoint processes a PDF file to extract specific sections based on the
    provided section type. It can extract individual sections or all available sections.
    
    Args:
        file (UploadFile): The PDF file to extract sections from. Must be a valid PDF document.
        section_type (str, optional): Type of section to extract. Valid values are:
                                    - "methods": Extracts methods section
                                    - "discussion": Extracts discussion section
                                    - "results": Extracts results section
                                    - "das": Extracts data analysis section
                                    - "all": Extracts all available sections
                                    If None or empty, extracts all sections.
        
    Returns:
        JSONResponse: Dictionary containing extracted section(s):
                     - For specific section: {section_type: "extracted text"}
                     - For all sections: {"sections": {"section_type": "extracted text", ...}}
        
    Raises:
        HTTPException (400): If an invalid section type is provided.
        HTTPException (500): If section extraction fails due to processing errors.
    """
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create PDFProcessor instance
        processor = PDFProcessor(file_path)
        
        # Validate section type if provided
        valid_sections = ["methods", "discussion", "results", "das", "all"]
        if section_type and section_type.lower() not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section type. Must be one of: {', '.join(valid_sections)}"
            )
        
        # Extract sections
        extracted_content = processor.extract_sections(
            section_type=section_type,
        )
        
        # Return appropriate response based on extraction mode
        if section_type == "all" or section_type is None or section_type.strip() == "":
            return JSONResponse(content={"sections": extracted_content})
        else:
            return JSONResponse(content={section_type: extracted_content})
    
    except Exception as e:
        logger.error(f"Error extracting sections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get port from environment variables, default to 8000 if not set
    port = int(os.getenv('FAST_API_PORT', 8000))
    backend_workers = int(os.getenv('FAST_API_WORKERS', 1))
    
    uvicorn.run("api:app", host="0.0.0.0", port=port, workers=backend_workers)

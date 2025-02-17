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
# from doc_layout_surya import PDFLayoutProcessor

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
async def extract_figures(file: UploadFile, output_dir: str = None):
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # If no output_dir specified, use the PDF directory
        if not output_dir:
            output_dir = str(pdf_dir) + "/figures"

        # Create PDFProcessor instance
        processor = PDFProcessor(file_path, "", "")  # Empty strings for unused parameters
        
        # Extract figures
        extracted_figures = processor.extract_figures(file_path, output_dir)
        
        if not extracted_figures:
            return JSONResponse(
                status_code=404,
                content={"message": "No figures found in the PDF"}
            )
        # Create a ZIP file containing all extracted figures
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for figure_path in extracted_figures:
                zip_file.write(figure_path, Path(figure_path).name)  # Use just the filename
        
        zip_buffer.seek(0)
        logging.info(f"Figures extracted and saved to {output_dir}")
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={Path(file_path).stem}_figures.zip"
            }
        )
    
    except Exception as e:
        logger.error(f"Error extracting figures: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-tables/")
async def extract_tables(file: UploadFile, output_dir: str = None):
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # If no output_dir specified, use the PDF directory
        if not output_dir:
            output_dir = str(pdf_dir) + "/tables"

        # Create PDFProcessor instance
        processor = PDFProcessor(file_path, "", "")  # Empty strings for unused parameters
        
        # Extract tables
        extracted_tables = processor.extract_tables(file_path, output_dir)
        
        if not extracted_tables:
            return JSONResponse(
                status_code=404,
                content={"message": "No tables found in the PDF"}
            )

        # Create a ZIP file containing all extracted tables
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for table_path in extracted_tables:
                zip_file.write(table_path, Path(table_path).name)  # Use just the filename
        
        zip_buffer.seek(0)
        logging.info(f"Tables extracted and saved to {output_dir}")
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={Path(file_path).stem}_tables.zip"
            }
        )
    
    except Exception as e:
        logger.error(f"Error extracting tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-text/")
async def extract_text(file: UploadFile):
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create PDFProcessor instance
        processor = PDFProcessor(file_path, "", "")  # Empty strings for unused parameters
        
        # Extract text
        extracted_text = processor.extract_text(file_path)
        
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
    try:
        # Create a unique directory for this PDF
        pdf_dir = UPLOADS_DIR / Path(file.filename).stem
        pdf_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = pdf_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create PDFProcessor instance
        processor = PDFProcessor(file_path, "", "")  # Empty strings for unused parameters
        
        # Process markdown
        markdown_text = processor.extract_markdown(file_path)
        
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import shutil
import logging
from doc_layout import PDFLayoutProcessor
from remove_irrelevant import PDFProcessor

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
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

processor = PDFLayoutProcessor()
@app.post("/process-pdf/")
async def process_pdf(file: UploadFile):
    try:
        # Save uploaded file
        file_path = file.filename
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
        # Save uploaded file
        file_path = file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process detections JSON path
        results_json = str(file_path).replace('.pdf', '_detections.json')
        output_pdf = str(file_path).replace('.pdf', '_cleaned.pdf')
        
        # Process PDF
        processor = PDFProcessor(str(file_path), results_json, output_pdf)
        if processor.remove_irrelevant_boxes():
            return FileResponse(
                output_pdf,
                media_type='application/pdf',
                filename=Path(output_pdf).name
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to process PDF")
    except Exception as e:
        logger.error(f"Error removing irrelevant boxes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    # finally:
    #     # Cleanup files
    #     for path in [file_path, Path(results_json), Path(output_pdf)]:
    #         if path.exists():
    #             path.unlink()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
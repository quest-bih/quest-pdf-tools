import os
import csv
import fitz  # PyMuPDF
from typing import List, Tuple
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class PDFProcessor:
    def __init__(self, pdf_path: str, results_csv: str, output_pdf: str):
        """Initialize the PDF processor with file paths."""
        self.pdf_path = pdf_path
        self.results_csv = results_csv
        self.output_pdf = output_pdf
        
        # Get PDF dimensions
        doc = fitz.open(pdf_path)
        self.page_width = doc[0].rect.width
        self.page_height = doc[0].rect.height
        doc.close()
        
    def validate_inputs(self) -> bool:
        """Validate input files and directories exist."""
        if not os.path.exists(self.pdf_path):
            logging.error(f"PDF file not found: {self.pdf_path}")
            return False
        if not os.path.exists(self.results_csv):
            logging.error(f"Results CSV file not found: {self.results_csv}")
            return False
        return True
    
    def scale_coordinates(self, coords: List[float], image_width: int, image_height: int) -> fitz.Rect:
        """Scale coordinates from image space (300 DPI) to PDF space (72 DPI)."""
        # Convert from image coordinates to PDF points
        x0 = coords[0] * self.page_width / image_width
        y0 = coords[1] * self.page_height / image_height
        x1 = coords[2] * self.page_width / image_width
        y1 = coords[3] * self.page_height / image_height
        return fitz.Rect(x0, y0, x1, y1)
    
    def process_detections(self, detection_row: Dict[str, str], page_num: int) -> List[fitz.Rect]:
        """Process detections for a single page and return list of rectangles."""
        redactions = []
        try:
            # Calculate image dimensions for this page (300 DPI)
            image_width = int(self.page_width * 300 / 72)
            image_height = int(self.page_height * 300 / 72)
            
            class_id = int(detection_row.get("class_id", -1))
            confidence = float(detection_row.get("confidence", 0))
            
            # Extract coordinates directly from the CSV columns
            coords = [
                float(detection_row.get("x0", 0)),
                float(detection_row.get("y0", 0)),
                float(detection_row.get("x1", 0)),
                float(detection_row.get("y1", 0))
            ]
            
            if class_id == 2 and confidence >= 0.2:  # Only process class_id 2 with confidence >= 0.2
                rect = self.scale_coordinates(coords, image_width, image_height)
                redactions.append(rect)
                
        except Exception as e:
            logging.error(f"Error processing detections for page {page_num + 1}: {e}")
        return redactions
    
    def remove_irrelevant_boxes(self) -> bool:
        """Process the PDF and remove irrelevant boxes."""
        if not self.validate_inputs():
            return False
        
        try:
            doc = fitz.open(self.pdf_path)
            modifications_made = False
            
            # Create a dictionary to store detections by page
            page_detections = {}
            
            # Read CSV file
            with open(self.results_csv, 'r') as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    page_num = int(row.get("page_number :", 0)) - 1
                    if page_num not in page_detections:
                        page_detections[page_num] = []
                    page_detections[page_num].append(row)
            
            # Process each page
            for page_num in range(len(doc)):
                if page_num in page_detections:
                    page = doc[page_num]
                    detections = page_detections[page_num]
                    
                    all_redactions = []
                    for detection in detections:
                        redactions = self.process_detections(detection, page_num)
                        all_redactions.extend(redactions)
                    
                    if all_redactions:
                        modifications_made = True
                        for rect in all_redactions:
                            page.add_redact_annot(rect, fill=(1, 1, 1))  # White fill
                        page.apply_redactions()
                        logging.info(f"Applied {len(all_redactions)} redactions to page {page_num + 1}")
                else:
                    logging.warning(f"No detection results found for page {page_num + 1}")
            
            if modifications_made:
                doc.save(self.output_pdf)
                logging.info(f"Saved modified PDF to {self.output_pdf}")
            else:
                logging.warning("No modifications were made to the PDF")
            
            doc.close()
            return True
        except Exception as e:
            logging.error(f"Error processing PDF: {e}")
            return False


# def main():
#     # Configuration
#     pdf_path = '10.1002+nbm.1786.pdf'
#     results_csv = pdf_path.replace('.pdf', '_detections.csv')
#     output_pdf = pdf_path.replace('.pdf', '_cleaned.pdf')
    
#     # Initialize and run processor
#     processor = PDFProcessor(pdf_path, results_csv, output_pdf)
#     if processor.remove_irrelevant_boxes():
#         logging.info("PDF processing completed successfully")
#     else:
#         logging.error("PDF processing failed")


# if __name__ == '__main__':
#     main()

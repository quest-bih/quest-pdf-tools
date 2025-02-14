import os
import csv
import fitz  # PyMuPDF
from typing import List, Dict
import logging
from pathlib import Path
from PIL import Image

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
        self.pdf_name = Path(pdf_path).stem
        self.pdf_dir = Path('pdfs') / self.pdf_name
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Update paths to use pdf directory
        self.results_csv = str(self.pdf_dir / Path(results_csv).name)
        self.output_pdf = str(self.pdf_dir / Path(output_pdf).name)
        
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
            with open(self.results_csv, "r") as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    # Fix: Use correct column name from CSV
                    page_num = int(row.get("page_number", 0)) - 1
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


    def extract_figures(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """Extract figures from PDF using detection results."""
        pdf_path = Path(pdf_path)
        pdf_name = pdf_path.stem
        pdf_dir = Path('pdfs') / pdf_name
        
        results_csv = pdf_dir / f'{pdf_name}_detections.csv'
        
        if not Path(results_csv).exists():
            logging.info(f"Detection results not found. Processing PDF: {pdf_path}")
            self.process_pdf(str(pdf_path))

        output_dir = pdf_dir / 'figures' if output_dir is None else Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_figures = []

        try:
            # Read detection results
            page_figures = {}
            with open(results_csv, 'r') as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    if int(row['class_id']) == 3:  # Figure class ID
                        page_num = int(row['page_number']) - 1
                        if page_num not in page_figures:
                            page_figures[page_num] = []
                        page_figures[page_num].append({
                            'x0': float(row['x0']),
                            'y0': float(row['y0']),
                            'x1': float(row['x1']),
                            'y1': float(row['y1'])
                        })

            # Extract figures from PDF
            doc = fitz.open(pdf_path)
            for page_num, figures in page_figures.items():
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                for fig_idx, coords in enumerate(figures):
                    # Convert coordinates from 300 DPI to image coordinates
                    x0 = int(coords['x0'])
                    y0 = int(coords['y0'])
                    x1 = int(coords['x1'])
                    y1 = int(coords['y1'])

                    # Crop and save figure
                    figure = img.crop((x0, y0, x1, y1))
                    figure_name = f"{pdf_path.stem}_page{page_num + 1}_figure{fig_idx + 1}.png"
                    figure_path = output_dir / figure_name
                    figure.save(str(figure_path))
                    extracted_figures.append(str(figure_path))
                    logging.info(f"Extracted figure: {figure_path}")

            return extracted_figures

        except Exception as e:
            logging.error(f"Error extracting figures from PDF: {e}")
            return []


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

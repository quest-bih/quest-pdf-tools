
import logging
import shutil
from doclayout_yolo import YOLOv10
from huggingface_hub import hf_hub_download

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
import csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class PDFLayoutProcessor:
    def __init__(self, model_repo: str = "juliozhao/DocLayout-YOLO-DocStructBench",
                 model_filename: str = "doclayout_yolo_docstructbench_imgsz1024.pt"):
        self.model_dir = Path("./models")
        self.model_path = self.model_dir / model_filename
        self.model = self._load_model(model_repo, model_filename)

    def _load_model(self, model_repo: str, model_filename: str) -> YOLOv10:
        """Load or download the YOLO model."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        if not self.model_path.exists():
            logger.info(f"Downloading model from {model_repo}/{model_filename}")
            hf_hub_download(repo_id=model_repo, filename=model_filename, local_dir=self.model_dir)
        else:
            logger.info(f"Loading existing model from {self.model_path}")
        return YOLOv10(str(self.model_path))

    def _get_pdf_dimensions(self, pdf_path: Path) -> tuple:
        """Get PDF dimensions from the first page."""
        with fitz.open(pdf_path) as pdf_document:
            first_page = pdf_document[0]
            width = int(first_page.rect.width * 300 / 72)  # Convert to pixels at 300 DPI
            height = int(first_page.rect.height * 300 / 72)
        logger.info(f"PDF dimensions: {width}x{height} pixels")
        return width, height

    def _process_detection_results(self, det_res, page_num: int) -> List[Dict[str, Any]]:
        """Process detection results into structured format."""
        detections = []
        for box in det_res[0].boxes:
            detection = {
                "class_id": int(box.cls),
                "confidence": float(box.conf),
                "coordinates": box.xyxy[0].tolist()
            }
            detections.append(detection)
        logger.info(f"Page {page_num}: Found {len(detections)} detections")
        return detections

    def _cleanup_temp_dir(self, temp_dir: Path) -> None:
        """Safely remove temporary directory and all its contents."""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")

    def _save_detection_results(self, pages_data: Dict[str, List[Dict]], output_path: Path) -> None:
        """Save detection results to a CSV file."""
        output_path = output_path.with_suffix('.csv')
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Add order to header
            writer.writerow(['page_number', 'order', 'class_id', 'confidence', 'x0', 'y0', 'x1', 'y1'])
            
            # Write data with order
            for page_key, detections in pages_data.items():
                page_num = int(page_key.split('_')[1])
                for order, detection in enumerate(detections, start=1):
                    coords = detection['coordinates']
                    writer.writerow([
                        page_num,
                        order,
                        detection['class_id'],
                        f"{detection['confidence']:.4f}",
                        f"{coords[0]}",
                        f"{coords[1]}",
                        f"{coords[2]}",
                        f"{coords[3]}"
                    ])
        logger.info(f"Saved detection results to {output_path}")

    def process_pdf(self, pdf_path: str) -> tuple:
        """Process PDF and return paths to output files."""
        pdf_path = Path(pdf_path)
        pdf_name = pdf_path.stem
        temp_dir = Path(f"{pdf_name}_temp")
        
        # Define category names and colors (RGB format)
        category_names = {
            0: 'title', 1: 'plain text', 2: 'abandon', 3: 'figure',
            4: 'figure_caption', 5: 'table', 6: 'table_caption',
            7: 'table_footnote', 8: 'isolate_formula', 9: 'formula_caption'
        }
        category_colors = {
            0: (1, 0, 0),      # Red for title
            1: (0, 0.5, 0),    # Green for plain text
            2: (0.5, 0.5, 0.5),# Gray for abandon
            3: (0, 0, 1),      # Blue for figure
            4: (1, 0.5, 0),    # Orange for figure caption
            5: (0.5, 0, 0.5),  # Purple for table
            6: (0, 0.5, 0.5),  # Teal for table caption
            7: (1, 0, 1),      # Magenta for table footnote
            8: (0.7, 0.3, 0),  # Brown for isolate formula
            9: (0, 0.7, 0.7)   # Cyan for formula caption
        }

        try:
            # Create temporary directory
            temp_dir.mkdir(exist_ok=True)
            width, height = self._get_pdf_dimensions(pdf_path)
            pages_data = {}

            # Open the PDF for modification
            pdf_document = fitz.open(pdf_path)
            output_pdf_path = Path(f"{pdf_name}_processed.pdf")
            
            for page_num in range(len(pdf_document)):
                # Convert PDF page to image for YOLO detection
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                temp_image_path = temp_dir / f'temp_page_{page_num+1}.png'
                pix.save(str(temp_image_path))

                # Perform prediction
                det_res = self.model.predict(
                    str(temp_image_path),
                    imgsz=1024,
                    conf=0.2,
                    device="mps"
                )

                # Process detections
                page_detections = self._process_detection_results(det_res, page_num+1)
                ordered_detections = self._reorder_detections(page_detections)
                pages_data[f"page_{page_num+1}"] = ordered_detections

                # Draw annotations on PDF
                for idx, detection in enumerate(ordered_detections):
                    class_id = detection['class_id']
                    conf = detection['confidence']
                    coords = detection['coordinates']
                    # print(coords)
                    
                    # Convert coordinates from 300 DPI to PDF coordinates (72 DPI)
                    scale = 72 / 300
                    rect = fitz.Rect(
                        (coords[0] - 7) * scale,  # Left with padding
                        (coords[1] - 1) * scale,  # Top with padding
                        (coords[2] + 2) * scale,  # Right with padding
                        (coords[3] + 1) * scale   # Bottom with padding
                    )
                    
                    color = category_colors[class_id]
                    
                    # Draw rectangle
                    page.draw_rect(rect, color=color, width=1)
                    
                    # Add text annotation with category name and confidence
                    text = f"{idx+1}. {category_names[class_id]} ({conf:.2%})"
                    text_point = fitz.Point(rect.x0, rect.y0)
                    # Create background rectangle for text
                    text_width = fitz.get_text_length(text, fontsize=3)
                    text_height = 2  # Approximate height for the text
                    text_rect = fitz.Rect(
                        text_point.x,
                        text_point.y - text_height,  # Position background above text
                        text_point.x + text_width,
                        text_point.y  # Background ends at text start point
                    )
                    page.draw_rect(text_rect, color=color, fill=color)
                    
                    # Add text in white color over the background
                    page.insert_text(
                        text_point,
                        text,
                        fontsize=3,
                        color=(1, 1, 1)  # White text
                    )

                # Clean up temporary image
                temp_image_path.unlink()

            # Save the modified PDF
            pdf_document.save(str(output_pdf_path))
            pdf_document.close()

            # Save detection results to JSON
            results_path = Path(f"{pdf_name}_detections.csv")
            self._save_detection_results(pages_data, results_path)

            return str(output_pdf_path), str(results_path)

        finally:
            # Clean up temporary directory
            self._cleanup_temp_dir(temp_dir)

    def _reorder_detections(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reorder detections from upper-left to lower-right (reading order)."""
        if not elements:
            return elements

        # Define a y-threshold to consider elements part of the same row
        y_threshold = 50  # Adjust based on document layout

        # Sort primarily by y (top to bottom), then by x (left to right)
        elements.sort(key=lambda e: (e['coordinates'][1], e['coordinates'][0]))

        # Group elements into rows based on y-spacing
        rows = []
        current_row = [elements[0]]

        for i in range(1, len(elements)):
            prev_y = current_row[-1]['coordinates'][1]
            curr_y = elements[i]['coordinates'][1]

            if abs(curr_y - prev_y) < y_threshold:
                current_row.append(elements[i])
            else:
                # Sort the current row left to right and save it
                current_row.sort(key=lambda e: e['coordinates'][0])
                rows.append(current_row)
                current_row = [elements[i]]

        # Sort and append last row
        current_row.sort(key=lambda e: e['coordinates'][0])
        rows.append(current_row)
        # Flatten back into a single list
        return [elem for row in rows for elem in row]

# # Usage example
# if __name__ == "__main__":
#     processor = PDFLayoutProcessor()
#     try:
#         output_pdf, output_json = processor.process_pdf("10.1002+nbm.1786.pdf")
#         logger.info("Processing complete")
#     except Exception as e:
#         logger.error(f"An error occurred during processing: {e}")
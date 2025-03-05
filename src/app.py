import gradio as gr
import base64
import requests
import os
from PIL import Image  # Add this import at the top
from dotenv import load_dotenv

def preview_pdf(file):
    if file is None:
        return None
    
    file_path = file.name if hasattr(file, 'name') else file
    
    with open(file_path, 'rb') as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    embed_html = (
        f"<embed src='data:application/pdf;base64,{pdf_data}#zoom=100' "
        f"type='application/pdf' width='100%' height='800px' "
        f"style='border-radius: 5px; outline: 1px solid lightgrey;' />"
    )
    return embed_html

def update_output_visibility(endpoint):
    if endpoint == "extract-text":
        return gr.TextArea(visible=True), gr.Markdown(visible=False), gr.Gallery(visible=False), gr.Gallery(visible=False), gr.File(visible=False)
    elif endpoint == "extract-markdown":
        return gr.TextArea(visible=False), gr.Markdown(visible=True), gr.Gallery(visible=False), gr.Gallery(visible=False), gr.File(visible=False)
    elif endpoint == "extract-figures":
        return gr.TextArea(visible=False), gr.Markdown(visible=False), gr.Gallery(visible=True), gr.Gallery(visible=False), gr.File(visible=True)
    elif endpoint == "extract-tables":
        return gr.TextArea(visible=False), gr.Markdown(visible=False), gr.Gallery(visible=False), gr.Gallery(visible=True), gr.File(visible=True)
    else:  # process-pdf and remove-irrelevant
        return gr.TextArea(visible=False), gr.Markdown(visible=False), gr.Gallery(visible=False), gr.Gallery(visible=False), gr.File(visible=True)

def process_pdf(file, endpoint):
    if file is None:
        gr.Warning("Please upload a PDF file first.")
        return None, None, None, None, None, None
    
    API_URL = f"http://localhost:8000/{endpoint}"
    input_filename = os.path.basename(file.name)
    files = {"file": (input_filename, open(file.name, "rb"), "application/pdf")}
    
    try:
        response = requests.post(API_URL, files=files)
        response.raise_for_status()
        
        if endpoint in ["extract-text", "extract-markdown"]:
            result = response.json()
            content = result.get("text", "") if "text" in result else result.get("markdown", "")
            if endpoint == "extract-markdown":
                return None, content, preview_pdf(file), None, None, None
            else:
                return content, None, preview_pdf(file), None, None, None
        
        elif endpoint in ["extract-figures", "extract-tables"]:
            # Get the PDF directory path from input file
            pdf_dir = "pdfs"
            pdf_name = os.path.splitext(input_filename)[0]
            
            # Define paths for zip and images based on endpoint
            if endpoint == "extract-figures":
                images_dir = os.path.join(pdf_dir, pdf_name, "figures")
                zip_path = os.path.join(pdf_dir, pdf_name, f"{pdf_name}_figures.zip")
            else:  # extract-tables
                images_dir = os.path.join(pdf_dir, pdf_name, "tables")
                zip_path = os.path.join(pdf_dir, pdf_name, f"{pdf_name}_tables.zip")
            
            # Load images directly from the appropriate directory if it exists
            if os.path.exists(images_dir):
                image_files = []
                # Get all image files and sort them
                img_files = sorted([f for f in os.listdir(images_dir) 
                                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
                                 key=str.lower)
                
                for img_file in img_files:
                    img_path = os.path.join(images_dir, img_file)
                    # Open image using PIL
                    image = Image.open(img_path)
                    image_files.append(image)
                
                if not image_files:
                    gr.Warning(f"No images found in the directory")
                    return None, None, preview_pdf(file), None, None, None
            else:
                gr.Warning(f"No figures/tables found in the directory")
                return None, None, preview_pdf(file), None, None, None
            
            # Return existing zip file if it exists
            if os.path.exists(zip_path):
                if endpoint == "extract-figures":
                    return None, None, preview_pdf(file), zip_path, image_files, None
                else:  # extract-tables
                    return None, None, preview_pdf(file), zip_path, None, image_files
            else:
                gr.Warning(f"No zip file found in the directory")
                return None, None, preview_pdf(file), None, None, None

        else:  # process-pdf and remove-irrelevant
            output_filename = response.headers.get('content-disposition')
            if output_filename:
                output_filename = output_filename.split('filename=')[-1].strip('"').split('/')[-1]
            
            output_path = os.path.join(os.path.dirname(file.name), output_filename)
            with open(output_path, "wb") as f:
                f.write(response.content)
            return None, None, preview_pdf(output_path), output_path, None, None
            
    except requests.exceptions.RequestException as e:
        return f"Error processing PDF: {str(e)}", None, None, None, None, None

def extract_sections_from_pdf(file):
    if file is None:
        gr.Warning("Please upload a PDF file first.")
        return None, None, None, None, None
    
    API_URL = "http://localhost:8000/extract-sections"
    input_filename = os.path.basename(file.name)
    files = {"file": (input_filename, open(file.name, "rb"), "application/pdf")}
    
    try:
        response = requests.post(API_URL, files=files)
        response.raise_for_status()
        
        result = response.json()
        sections = result.get("sections", {})
        
        methods = sections.get("methods", "No methods section found.")
        results = sections.get("results", "No results section found.")
        discussion = sections.get("discussion", "No discussion section found.")
        das = sections.get("das", "No data availability statement found.")
        
        return preview_pdf(file), methods, results, discussion, das
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Error extracting sections: {str(e)}"
        return None, error_msg, error_msg, error_msg, error_msg
css="""
        footer {display: none !important}
        .contain {max-width: 95% !important}
    """
with gr.Blocks(fill_height=True, fill_width=True, theme=gr.themes.Origin(),css=css) as demo:
    with gr.Tabs():
        with gr.TabItem("PDF Processing"):
            with gr.Row():
                with gr.Column(scale=1, variant="panel"):
                    with gr.Row():
                        file_input = gr.File(label="Upload PDF", file_types=[".pdf"],height=150, file_count='single')
                    with gr.Row(): 
                        endpoint = gr.Radio(
                            choices=[
                                ("PDF layout (bboxes) ", "process-pdf"),
                                ("Extract Figures", "extract-figures"),
                                ("Extract Tables", "extract-tables"),
                                ("To Text", "extract-text"),
                                ("To Markdown", "extract-markdown"),
                                ("Remove Irrelevant Content", "remove-irrelevant"),
                            ],
                            label="Select Processing Type",
                            value="process-pdf"
                        )
                    with gr.Row():
                        process_btn = gr.Button("Process PDF", variant="primary")
                        clear_btn = gr.Button("Clear")

                    with gr.Row():
                        output = gr.TextArea(
                            label="Text Output",
                            show_label=True, 
                            interactive=False, 
                            lines=22, 
                            visible=False,
                            show_copy_button=True,
                            autoscroll=False
                        )
                        markdown_output = gr.Markdown(
                            label= "Markdown text",
                            show_label=True,
                            show_copy_button=True,
                            visible=False,
                            container=True,
                            min_height=500,
                            max_height=500
                            )
                        figures_gallery = gr.Gallery(
                            label="Extracted Figures",
                            visible=False,
                            columns=2,
                            height=400,
                            selected_index= 1,
                            allow_preview=True
                        )
                        tables_gallery = gr.Gallery(
                            label="Extracted Tables",
                            visible=False,
                            columns=2,
                            height=400,
                        )
                    
                    with gr.Row():
                        download_output = gr.File(label="Download Output", visible=True, interactive=False)
                    
                    endpoint.change(
                        fn=update_output_visibility,
                        inputs=[endpoint],
                        outputs=[output, markdown_output, figures_gallery, tables_gallery, download_output]
                    )
                    
                with gr.Column(scale=2):
                    preview = gr.HTML(label="PDF Preview", min_height=900)
                    file_input.change(preview_pdf, inputs=[file_input], outputs=[preview])
            
                process_btn.click(
                    process_pdf,
                    inputs=[file_input, endpoint],
                    outputs=[output, markdown_output, preview, download_output, figures_gallery, tables_gallery]
                )
                
                clear_btn.click(
                    lambda: (None, None, None, None, None, None,None), 
                    None, 
                    [file_input, output, markdown_output, preview, figures_gallery, tables_gallery, download_output]
                    )
        
        with gr.TabItem("Extract Sections"):
            with gr.Row():
                with gr.Column(scale=1, variant="panel"):
                    with gr.Row():
                        sections_file_input = gr.File(label="Upload PDF", file_types=[".pdf"], height=150, file_count='single')
                    
                    with gr.Row():
                        extract_sections_btn = gr.Button("Extract Sections", variant="primary")
                        clear_sections_btn = gr.Button("Clear")
                    
                    with gr.Row():
                        methods_output = gr.TextArea(
                            label="Methods Section",
                            show_label=True,
                            interactive=False,
                            lines=5,max_lines=5,
                            show_copy_button=True,
                            autoscroll=False
                        )
                    
                    with gr.Row():
                        results_output = gr.TextArea(
                            label="Results Section",
                            show_label=True,
                            interactive=False,
                            lines=5,max_lines=5,
                            show_copy_button=True,
                            autoscroll=False
                        )
                    
                    with gr.Row():
                        discussion_output = gr.TextArea(
                            label="Discussion Section",
                            show_label=True,
                            interactive=False,
                            lines=5,max_lines=5,
                            show_copy_button=True,
                            autoscroll=False
                        )
                    
                    with gr.Row():
                        das_output = gr.TextArea(
                            label="Data Availability Statement",
                            show_label=True,
                            interactive=False,
                            lines=2,max_lines=2,
                            show_copy_button=True,
                            autoscroll=False
                        )
                
                with gr.Column(scale=2):
                    sections_preview = gr.HTML(label="PDF Preview", min_height=900)
                    sections_file_input.change(preview_pdf, inputs=[sections_file_input], outputs=[sections_preview])
            
            extract_sections_btn.click(
                extract_sections_from_pdf,
                inputs=[sections_file_input],
                outputs=[sections_preview, methods_output, results_output, discussion_output, das_output]
            )
            
            clear_sections_btn.click(
                lambda: (None, None, None, None, None, None),
                None,
                [sections_file_input, sections_preview, methods_output, results_output, discussion_output, das_output]
            )

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    # Get port from environment variables, default to 7860 if not set
    port = int(os.getenv('GRADIO_PORT', 7860))  
    
    demo.launch(share=False, server_port=port, show_api=False, server_name="0.0.0.0")

import gradio as gr
import markdown
import threading
import time
import logging
from converter import convert_file, set_cancellation_flag
from docling_chat import chat_with_document
from parser_registry import ParserRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add a global variable to track cancellation state
conversion_cancelled = threading.Event()

# Pass the cancellation flag to the converter module
set_cancellation_flag(conversion_cancelled)

def format_markdown_content(content):
    if not content:
        return content
    
    # Convert the content to HTML using markdown library
    html_content = markdown.markdown(str(content), extensions=['tables'])
    return html_content


def split_content_into_pages(content, chars_per_page=6000):
    if not content:
        return ["No content to display"]
    
    # Split by natural breaks (double newlines) first
    sections = str(content).split('\n\n')
    pages = []
    current_page = []
    current_length = 0
    
    for section in sections:
        section_length = len(section) + 2  # +2 for double newline
        
        if current_length + section_length > chars_per_page and current_page:
            # Format each page with markdown
            page_content = '\n\n'.join(current_page)
            pages.append(format_markdown_content(page_content))
            current_page = [section]
            current_length = section_length
        else:
            current_page.append(section)
            current_length += section_length
    
    if current_page:
        # Format the last page with markdown
        page_content = '\n\n'.join(current_page)
        pages.append(format_markdown_content(page_content))
    
    return pages


def update_page_content(pages, page_number):
    if not pages or page_number < 1 or page_number > len(pages):
        return "Invalid page", page_number, "Page 0/0"
    return str(pages[page_number - 1]), page_number, f"Page {page_number}/{len(pages)}"


def handle_convert(file_path, parser_name, ocr_method_name, output_format, is_cancelled):
    """Handle file conversion."""
    global conversion_cancelled
    
    # Check if we should cancel before starting
    if is_cancelled:
        logger.info("Conversion cancelled before starting")
        return "Conversion cancelled.", None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
    
    # Reset the cancellation flag at the start of conversion
    conversion_cancelled.clear()
    logger.info("Starting conversion with cancellation flag cleared")
    
    try:
        # Perform the conversion
        content, download_file = convert_file(file_path, parser_name, ocr_method_name, output_format)
        
        # Check if the conversion was cancelled
        if conversion_cancelled.is_set() or is_cancelled:
            logger.info("Conversion was cancelled during processing")
            return "Conversion cancelled.", None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
        
        # If conversion returned a cancellation message
        if content == "Conversion cancelled.":
            logger.info("Converter returned cancellation message")
            return content, None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
        
        # Process results
        pages = split_content_into_pages(str(content))
        page_info = f"Page 1/{len(pages)}"
        
        logger.info("Conversion completed successfully")
        return str(pages[0]) if pages else "", download_file, pages, 1, page_info, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        return f"Error: {str(e)}", None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)


def handle_page_navigation(direction, current, pages):
    new_page = current + direction
    if new_page < 1:
        new_page = 1
    elif new_page > len(pages):
        new_page = len(pages)
    content, page_num, page_info = update_page_content(pages, new_page)
    return content, new_page, page_info


def create_ui():
    with gr.Blocks(css="""
        .page-navigation { text-align: center; margin-top: 1rem; }
        .page-navigation button { margin: 0 0.5rem; }
        .page-info { display: inline-block; margin: 0 1rem; }
        .processing-controls { display: flex; justify-content: center; gap: 10px; margin-top: 10px; }
    """) as demo:
        gr.Markdown("Markit: Convert any documents to Markdown")
        
        # State to track if cancellation is requested
        cancel_requested = gr.State(False)

        with gr.Tabs():
            with gr.Tab("Upload and Convert"):
                file_input = gr.File(label="Upload PDF", type="filepath")
                
                # Content display with navigation
                content_pages = gr.State([])
                current_page = gr.State(1)
                file_display = gr.Markdown(label="Converted Markdown")
                
                with gr.Row(visible=False) as navigation_row:
                    with gr.Column(scale=1):
                        prev_btn = gr.Button("←", elem_classes=["page-navigation"])
                    with gr.Column(scale=1):
                        page_info = gr.Markdown("Page 1/1", elem_classes=["page-info"])
                    with gr.Column(scale=1):
                        next_btn = gr.Button("→", elem_classes=["page-navigation"])
                
                file_download = gr.File(label="Download File")
                
                # Processing controls row
                with gr.Row(elem_classes=["processing-controls"]):
                    convert_button = gr.Button("Convert", variant="primary")
                    cancel_button = gr.Button("Cancel", variant="stop", visible=False)

            with gr.Tab("Config ⚙️"):
                with gr.Group(elem_classes=["settings-group"]):
                    with gr.Row():
                        with gr.Column(scale=1):
                            parser_names = ParserRegistry.get_parser_names()
                            default_parser = parser_names[0] if parser_names else "PyPdfium"
                            
                            provider_dropdown = gr.Dropdown(
                                label="Provider",
                                choices=parser_names,
                                value=default_parser,
                                interactive=True
                            )
                        with gr.Column(scale=1):
                            default_ocr_options = ParserRegistry.get_ocr_options(default_parser)
                            default_ocr = default_ocr_options[0] if default_ocr_options else "No OCR"
                            
                            ocr_dropdown = gr.Dropdown(
                                label="OCR Options",
                                choices=default_ocr_options,
                                value=default_ocr,
                                interactive=True
                            )
                    
                    output_format = gr.Radio(
                        label="Output Format",
                        choices=["Markdown", "JSON", "Text", "Document Tags"],
                        value="Markdown"
                    )

            with gr.Tab("Chat with Document"):
                document_text_state = gr.State("")
                chatbot = gr.Chatbot(label="Chat", type="messages")
                text_input = gr.Textbox(placeholder="Type here...")
                clear_btn = gr.Button("Clear")

        # Event handlers
        provider_dropdown.change(
            lambda p: gr.Dropdown(choices=ParserRegistry.get_ocr_options(p), 
                                value=ParserRegistry.get_ocr_options(p)[0] if ParserRegistry.get_ocr_options(p) else None),
            inputs=[provider_dropdown],
            outputs=[ocr_dropdown]
        )

        # Reset cancel flag when starting conversion
        def start_conversion():
            global conversion_cancelled
            conversion_cancelled.clear()
            logger.info("Starting conversion with cancellation flag cleared")
            return gr.update(visible=False), gr.update(visible=True), False

        # Set cancel flag when cancel button is clicked
        def request_cancellation():
            global conversion_cancelled
            conversion_cancelled.set()
            logger.info("Cancel button clicked, cancellation flag set")
            # Add immediate feedback to the user
            return gr.update(visible=True), gr.update(visible=False), True

        # Start conversion sequence
        convert_button.click(
            fn=start_conversion,
            inputs=[],
            outputs=[convert_button, cancel_button, cancel_requested],
            queue=False  # Execute immediately
        ).then(
            fn=handle_convert,
            inputs=[file_input, provider_dropdown, ocr_dropdown, output_format, cancel_requested],
            outputs=[file_display, file_download, content_pages, current_page, page_info, navigation_row, convert_button, cancel_button]
        )
        
        # Handle cancel button click
        cancel_button.click(
            fn=request_cancellation,
            inputs=[],
            outputs=[convert_button, cancel_button, cancel_requested],
            queue=False  # Execute immediately
        )

        prev_btn.click(
            fn=lambda curr, pages: handle_page_navigation(-1, curr, pages),
            inputs=[current_page, content_pages],
            outputs=[file_display, current_page, page_info]
        )

        next_btn.click(
            fn=lambda curr, pages: handle_page_navigation(1, curr, pages),
            inputs=[current_page, content_pages],
            outputs=[file_display, current_page, page_info]
        )

        file_display.change(
            lambda text: text,
            inputs=[file_display],
            outputs=[document_text_state]
        )

        text_input.submit(
            fn=chat_with_document,
            inputs=[text_input, chatbot, document_text_state],
            outputs=[chatbot, chatbot]
        )

        clear_btn.click(
            lambda: ([], []),
            None,
            [chatbot, chatbot]
        )

    return demo


def launch_ui(server_name="0.0.0.0", server_port=7860, share=False):
    demo = create_ui()
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        root_path="",
        show_error=True,
        share=share
    ) 
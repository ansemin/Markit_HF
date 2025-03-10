import gradio as gr
import markdown
import threading
import time
import logging
from src.core.converter import convert_file, set_cancellation_flag, is_conversion_in_progress
from src.services.docling_chat import chat_with_document
from src.parsers.parser_registry import ParserRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add a global variable to track cancellation state
conversion_cancelled = threading.Event()

# Pass the cancellation flag to the converter module
set_cancellation_flag(conversion_cancelled)

# Add a background thread to monitor cancellation
def monitor_cancellation():
    """Background thread to monitor cancellation and update UI if needed"""
    logger.info("Starting cancellation monitor thread")
    while is_conversion_in_progress():
        if conversion_cancelled.is_set():
            logger.info("Cancellation detected by monitor thread")
        time.sleep(0.1)  # Check every 100ms
    logger.info("Cancellation monitor thread ending")

def format_markdown_content(content):
    if not content:
        return content
    
    # Convert the content to HTML using markdown library
    html_content = markdown.markdown(str(content), extensions=['tables'])
    return html_content

# Function to run conversion in a separate thread
def run_conversion_thread(file_path, parser_name, ocr_method_name, output_format):
    """Run the conversion in a separate thread and return the thread object"""
    global conversion_cancelled
    
    # Reset the cancellation flag
    conversion_cancelled.clear()
    
    # Create a container for the results
    results = {"content": None, "download_file": None, "error": None}
    
    def conversion_worker():
        try:
            content, download_file = convert_file(file_path, parser_name, ocr_method_name, output_format)
            results["content"] = content
            results["download_file"] = download_file
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            results["error"] = str(e)
    
    # Create and start the thread
    thread = threading.Thread(target=conversion_worker)
    thread.daemon = True
    thread.start()
    
    return thread, results

def handle_convert(file_path, parser_name, ocr_method_name, output_format, is_cancelled):
    """Handle file conversion."""
    global conversion_cancelled
    
    # Check if we should cancel before starting
    if is_cancelled:
        logger.info("Conversion cancelled before starting")
        return "Conversion cancelled.", None, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), None
    
    logger.info("Starting conversion with cancellation flag cleared")
    
    # Start the conversion in a separate thread
    thread, results = run_conversion_thread(file_path, parser_name, ocr_method_name, output_format)
    
    # Start the monitoring thread
    monitor_thread = threading.Thread(target=monitor_cancellation)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Wait for the thread to complete or be cancelled
    while thread.is_alive():
        # Check if cancellation was requested
        if conversion_cancelled.is_set():
            logger.info("Cancellation detected, waiting for thread to finish")
            # Give the thread a chance to clean up
            thread.join(timeout=0.5)
            if thread.is_alive():
                logger.warning("Thread did not finish within timeout")
            return "Conversion cancelled.", None, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), None
        
        # Sleep briefly to avoid busy waiting
        time.sleep(0.1)
    
    # Thread has completed, check results
    if results["error"]:
        return f"Error: {results['error']}", None, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), None
    
    content = results["content"]
    download_file = results["download_file"]
    
    # If conversion returned a cancellation message
    if content == "Conversion cancelled.":
        logger.info("Converter returned cancellation message")
        return content, None, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), None
    
    # Format the content
    formatted_content = format_markdown_content(str(content))
    
    logger.info("Conversion completed successfully")
    return formatted_content, download_file, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), None

def create_ui():
    with gr.Blocks(css="""
        .markdown-display { 
            height: 600px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .processing-controls { 
            display: flex; 
            justify-content: center; 
            gap: 10px; 
            margin-top: 10px; 
        }
    """) as demo:
        gr.Markdown("Markit: Convert any documents to Markdown")
        
        # State to track if cancellation is requested
        cancel_requested = gr.State(False)
        # State to store the conversion thread
        conversion_thread = gr.State(None)

        with gr.Tabs():
            with gr.Tab("Upload and Convert"):
                file_input = gr.File(label="Upload PDF", type="filepath")
                
                # Single scrollable content display
                file_display = gr.HTML(label="Converted Markdown", elem_classes=["markdown-display"])
                
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

        # Set cancel flag and terminate thread when cancel button is clicked
        def request_cancellation(thread):
            global conversion_cancelled
            conversion_cancelled.set()
            logger.info("Cancel button clicked, cancellation flag set")
            
            # Try to join the thread with a timeout
            if thread is not None:
                logger.info(f"Attempting to join conversion thread: {thread}")
                thread.join(timeout=0.5)
                if thread.is_alive():
                    logger.warning("Thread did not finish within timeout")
            
            # Add immediate feedback to the user
            return gr.update(visible=True), gr.update(visible=False), True, None

        # Start conversion sequence
        convert_button.click(
            fn=start_conversion,
            inputs=[],
            outputs=[convert_button, cancel_button, cancel_requested],
            queue=False  # Execute immediately
        ).then(
            fn=handle_convert,
            inputs=[file_input, provider_dropdown, ocr_dropdown, output_format, cancel_requested],
            outputs=[file_display, file_download, convert_button, cancel_button, conversion_thread]
        )
        
        # Handle cancel button click
        cancel_button.click(
            fn=request_cancellation,
            inputs=[conversion_thread],
            outputs=[convert_button, cancel_button, cancel_requested, conversion_thread],
            queue=False  # Execute immediately
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
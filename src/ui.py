import gradio as gr
import markdown
import threading
import time
from converter import convert_file
from docling_chat import chat_with_document
from parser_registry import ParserRegistry


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


def handle_convert(file_path, parser_name, ocr_method_name, output_format):
    """Handle file conversion."""
    content, download_file = convert_file(file_path, parser_name, ocr_method_name, output_format)
    pages = split_content_into_pages(str(content))
    page_info = f"Page 1/{len(pages)}"
    return str(pages[0]) if pages else "", download_file, pages, 1, page_info, gr.update(visible=True)


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
        gr.Markdown("Doc2Md: Convert any documents to Markdown")

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
                with gr.Row(elem_classes=["processing-controls"]) as processing_controls:
                    convert_button = gr.Button("Convert", variant="primary")
                    # Cancel button that will only be visible during processing
                    cancel_button = gr.Button("Cancel", variant="stop", visible=False)
                
                # Add a progress indicator
                progress = gr.Progress()

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

        # Update the convert button click handler to be cancellable and show/hide the cancel button
        def start_conversion(file_path, parser_name, ocr_method_name, output_format, progress=gr.Progress()):
            # Show cancel button when processing starts
            yield "", None, [], 1, "Processing...", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)
            
            # Simulate progress updates (this will be replaced by actual progress from converter)
            for i in range(10):
                # Check if the task has been cancelled
                if progress.cancelled:
                    yield "Conversion cancelled.", None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
                    return
                
                progress(i/10, desc=f"Processing document ({i*10}%)")
                time.sleep(0.2)  # Simulate work
            
            # Actual conversion
            try:
                content, download_file = convert_file(file_path, parser_name, ocr_method_name, output_format)
                pages = split_content_into_pages(str(content))
                page_info = f"Page 1/{len(pages)}"
                
                # Return results and update UI
                yield str(pages[0]) if pages else "", download_file, pages, 1, page_info, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
            except Exception as e:
                yield f"Error: {str(e)}", None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)

        convert_button.click(
            fn=start_conversion,
            inputs=[file_input, provider_dropdown, ocr_dropdown, output_format],
            outputs=[file_display, file_download, content_pages, current_page, page_info, navigation_row, convert_button, cancel_button],
            cancellable=True,  # Make this operation cancellable
        )
        
        # When cancel button is clicked, it should reset the UI
        cancel_button.click(
            fn=lambda: ("Conversion cancelled.", None, [], 1, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)),
            inputs=[],
            outputs=[file_display, file_download, content_pages, current_page, page_info, navigation_row, convert_button, cancel_button],
            cancels=["convert"]  # This will cancel the running convert task
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
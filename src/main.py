import gradio as gr
import markdown
from converter import convert_file
from docling_chat import chat_with_document

# Use relative imports
from parser_registry import ParserRegistry

# Import all parsers to ensure they're registered
import parsers


def get_ocr_options(parser_name):
    """Get OCR options for a parser."""
    return ParserRegistry.get_ocr_options(parser_name)


def handle_convert(file_path, parser_name, ocr_method_name, output_format):
    """Handle file conversion."""
    content, download_file = convert_file(file_path, parser_name, ocr_method_name, output_format)
    pages = split_content_into_pages(str(content))
    page_info = f"Page 1/{len(pages)}"
    return str(pages[0]) if pages else "", download_file, pages, 1, page_info, gr.update(visible=True)


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


def main():
    with gr.Blocks(css="""
        .page-navigation { text-align: center; margin-top: 1rem; }
        .page-navigation button { margin: 0 0.5rem; }
        .page-info { display: inline-block; margin: 0 1rem; }
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
                
                convert_button = gr.Button("Convert")

            with gr.Tab("Config ⚙️"):
                with gr.Group(elem_classes=["settings-group"]):
                    with gr.Row():
                        with gr.Column(scale=1):
                            parser_names = ParserRegistry.get_parser_names()
                            default_parser = parser_names[0] if parser_names else "PyPdfium"
                            
                            provider_btns = gr.Radio(
                                label="Provider",
                                choices=parser_names,
                                value=default_parser,
                                interactive=True
                            )
                        with gr.Column(scale=3):
                            default_ocr_options = get_ocr_options(default_parser)
                            default_ocr = default_ocr_options[0] if default_ocr_options else "No OCR"
                            
                            ocr_btns = gr.Radio(
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
        provider_btns.change(
            lambda p: gr.Radio(choices=get_ocr_options(p), value=get_ocr_options(p)[0] if get_ocr_options(p) else None),
            inputs=[provider_btns],
            outputs=[ocr_btns]
        )

        convert_button.click(
            fn=handle_convert,
            inputs=[file_input, provider_btns, ocr_btns, output_format],
            outputs=[file_display, file_download, content_pages, current_page, page_info, navigation_row]
        )

        def handle_page_navigation(direction, current, pages):
            new_page = current + direction
            if new_page < 1:
                new_page = 1
            elif new_page > len(pages):
                new_page = len(pages)
            content, page_num, page_info = update_page_content(pages, new_page)
            return content, new_page, page_info

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

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()

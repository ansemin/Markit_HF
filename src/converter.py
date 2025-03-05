import tempfile
import logging
import time
import os
import threading
from pathlib import Path

# Use relative imports instead of absolute imports
from parser_factory import ParserFactory

# Import all parsers to ensure they're registered
import parsers

# Reference to the cancellation flag from ui.py
# This will be set by the UI when the cancel button is clicked
conversion_cancelled = None

def set_cancellation_flag(flag):
    """Set the reference to the cancellation flag from ui.py"""
    global conversion_cancelled
    conversion_cancelled = flag


def convert_file(file_path, parser_name, ocr_method_name, output_format):
    """
    Convert a file using the specified parser and OCR method.
    
    Args:
        file_path: Path to the file
        parser_name: Name of the parser to use
        ocr_method_name: Name of the OCR method to use
        output_format: Output format (Markdown, JSON, Text, Document Tags)
        
    Returns:
        tuple: (content, download_file_path)
    """
    global conversion_cancelled
    
    if not file_path:
        return "Please upload a file.", None

    # Check for cancellation
    if conversion_cancelled and conversion_cancelled.is_set():
        return "Conversion cancelled.", None

    # Create a temporary file with English filename
    try:
        original_ext = Path(file_path).suffix
        with tempfile.NamedTemporaryFile(suffix=original_ext, delete=False) as temp_input:
            # Copy the content of original file to temp file
            with open(file_path, 'rb') as original:
                temp_input.write(original.read())
        file_path = temp_input.name
    except Exception as e:
        return f"Error creating temporary file: {e}", None

    # Check for cancellation again
    if conversion_cancelled and conversion_cancelled.is_set():
        # Clean up temp file
        try:
            os.unlink(temp_input.name)
        except:
            pass
        return "Conversion cancelled.", None

    try:
        # Use the parser factory to parse the document
        start = time.time()
        
        # We need to modify the parsing process to check for cancellation
        # This requires changes to the parser implementation, but we can add a hook here
        
        # Pass the cancellation flag to the parser factory
        content = ParserFactory.parse_document(
            file_path=file_path,
            parser_name=parser_name,
            ocr_method_name=ocr_method_name,
            output_format=output_format.lower(),
            cancellation_flag=conversion_cancelled  # Pass the flag to parsers
        )
        
        duration = time.time() - start
        logging.info(f"Processed in {duration:.2f} seconds.")
        
        # Check for cancellation after processing
        if conversion_cancelled and conversion_cancelled.is_set():
            # Clean up temp file
            try:
                os.unlink(temp_input.name)
            except:
                pass
            return "Conversion cancelled.", None
            
    except Exception as e:
        # Clean up temp file
        try:
            os.unlink(temp_input.name)
        except:
            pass
        return f"Error: {e}", None

    # Determine the file extension based on the output format
    if output_format == "Markdown":
        ext = ".md"
    elif output_format == "JSON":
        ext = ".json"
    elif output_format == "Text":
        ext = ".txt"
    elif output_format == "Document Tags":
        ext = ".doctags"
    else:
        ext = ".txt"

    # Check for cancellation again
    if conversion_cancelled and conversion_cancelled.is_set():
        # Clean up temp file
        try:
            os.unlink(temp_input.name)
        except:
            pass
        return "Conversion cancelled.", None

    try:
        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Clean up the temporary input file
        try:
            os.unlink(temp_input.name)
        except:
            pass
            
        return content, tmp_path
    except Exception as e:
        # Clean up temp file
        try:
            os.unlink(temp_input.name)
        except:
            pass
        return f"Error: {e}", None

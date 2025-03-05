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
conversion_cancelled = None

def set_cancellation_flag(flag):
    """Set the reference to the cancellation flag from ui.py"""
    global conversion_cancelled
    conversion_cancelled = flag
    logging.info(f"Cancellation flag set: {flag}")


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

    # Log cancellation state at the start
    if conversion_cancelled:
        logging.info(f"Starting conversion. Cancellation flag state: {conversion_cancelled.is_set()}")
    
    # Create a temporary file with English filename
    temp_input = None
    try:
        # Check for early cancellation
        if conversion_cancelled and conversion_cancelled.is_set():
            logging.info("Conversion cancelled before file preparation")
            return "Conversion cancelled.", None
            
        original_ext = Path(file_path).suffix
        with tempfile.NamedTemporaryFile(suffix=original_ext, delete=False) as temp_input:
            # Copy the content of original file to temp file
            with open(file_path, 'rb') as original:
                temp_input.write(original.read())
        file_path = temp_input.name
        
        # Check for cancellation after file preparation
        if conversion_cancelled and conversion_cancelled.is_set():
            logging.info("Conversion cancelled after file preparation")
            cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None

        # Use the parser factory to parse the document
        start = time.time()
        
        # Pass the cancellation flag to the parser factory
        content = ParserFactory.parse_document(
            file_path=file_path,
            parser_name=parser_name,
            ocr_method_name=ocr_method_name,
            output_format=output_format.lower(),
            cancellation_flag=conversion_cancelled
        )
        
        # Check if the content indicates cancellation
        if content == "Conversion cancelled.":
            logging.info("Parser reported cancellation")
            cleanup_temp_file(temp_input.name)
            return content, None
            
        # Check for cancellation after parsing
        if conversion_cancelled and conversion_cancelled.is_set():
            logging.info("Conversion cancelled after parsing")
            cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None
            
        duration = time.time() - start
        logging.info(f"Processed in {duration:.2f} seconds.")

        # Check for cancellation before file creation
        if conversion_cancelled and conversion_cancelled.is_set():
            logging.info("Conversion cancelled before file creation")
            cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None

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

        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Clean up the temporary input file
        cleanup_temp_file(temp_input.name)
            
        return content, tmp_path
        
    except Exception as e:
        logging.error(f"Error during conversion: {str(e)}")
        if temp_input and hasattr(temp_input, 'name'):
            cleanup_temp_file(temp_input.name)
        return f"Error: {e}", None


def cleanup_temp_file(file_path):
    """Helper function to clean up temporary files"""
    try:
        os.unlink(file_path)
        logging.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logging.error(f"Failed to clean up temporary file {file_path}: {str(e)}")


def get_output_extension(output_format):
    """Helper function to get the appropriate file extension"""
    if output_format == "Markdown":
        return ".md"
    elif output_format == "JSON":
        return ".json"
    elif output_format == "Text":
        return ".txt"
    elif output_format == "Document Tags":
        return ".doctags"
    return ".txt"

import tempfile
import logging
import time
import os
import threading
import signal
from pathlib import Path

# Use relative imports instead of absolute imports
from parser_factory import ParserFactory

# Import all parsers to ensure they're registered
import parsers

# Reference to the cancellation flag from ui.py
conversion_cancelled = None
# Track the current process for cancellation
current_conversion_thread = None

def set_cancellation_flag(flag):
    """Set the reference to the cancellation flag from ui.py"""
    global conversion_cancelled
    conversion_cancelled = flag
    logging.info(f"Cancellation flag set: {flag}")


def check_cancellation():
    """Check if cancellation is requested and interrupt if needed"""
    global conversion_cancelled
    if conversion_cancelled and conversion_cancelled.is_set():
        logging.info("Cancellation detected, raising interrupt")
        # This will raise a KeyboardInterrupt exception in the current thread
        return True
    return False


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
    
    # Record start time for logging
    start_time = time.time()
    logging.info(f"Starting conversion of {file_path}")
    
    if not file_path:
        return "Please upload a file.", None

    # Check immediately for cancellation
    if check_cancellation():
        return "Conversion cancelled.", None
    
    # Create a temporary file with English filename
    temp_input = None
    try:
        original_ext = Path(file_path).suffix
        with tempfile.NamedTemporaryFile(suffix=original_ext, delete=False) as temp_input:
            # Copy the content of original file to temp file
            with open(file_path, 'rb') as original:
                temp_input.write(original.read())
        file_path = temp_input.name
        
        # Check for cancellation after file preparation
        if check_cancellation():
            cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None

        # Use the parser factory to parse the document
        logging.info(f"Starting document parsing with {parser_name} and {ocr_method_name}")
        
        def interruptible_parser():
            """Run parser in a way that can be checked for cancellation"""
            try:
                # Log starting
                logging.info("Parser thread started")
                return ParserFactory.parse_document(
                    file_path=file_path,
                    parser_name=parser_name,
                    ocr_method_name=ocr_method_name,
                    output_format=output_format.lower(),
                    cancellation_flag=conversion_cancelled
                )
            except Exception as e:
                logging.error(f"Parser thread error: {str(e)}")
                if conversion_cancelled and conversion_cancelled.is_set():
                    return "Conversion cancelled."
                raise

        # Regular parsing, but periodically check for cancellation
        content = None
        parse_start = time.time()
        
        # Perform the actual parsing
        content = interruptible_parser()
        
        # If we got here, parsing is complete
        logging.info(f"Parsing completed in {time.time() - parse_start:.2f} seconds")
        
        # Check cancellation immediately after parsing
        if check_cancellation() or content == "Conversion cancelled.":
            cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None

        # Determine the file extension
        ext = get_output_extension(output_format)

        # Final cancellation check before file creation
        if check_cancellation():
            cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None

        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Clean up temporary files
        cleanup_temp_file(temp_input.name)
        
        # Log completion time
        total_time = time.time() - start_time
        logging.info(f"Conversion completed in {total_time:.2f} seconds")
            
        return content, tmp_path
        
    except Exception as e:
        logging.error(f"Error during conversion: {str(e)}")
        
        # Check if this was a cancellation
        if conversion_cancelled and conversion_cancelled.is_set():
            if temp_input and hasattr(temp_input, 'name'):
                cleanup_temp_file(temp_input.name)
            return "Conversion cancelled.", None
            
        # Other error
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

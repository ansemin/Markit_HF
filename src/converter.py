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
        logging.info("Cancellation detected at start of convert_file")
        return "Conversion cancelled.", None

    # Create a temporary file with English filename
    try:
        original_ext = Path(file_path).suffix
        with tempfile.NamedTemporaryFile(suffix=original_ext, delete=False) as temp_input:
            # Copy the content of original file to temp file
            with open(file_path, 'rb') as original:
                # Read in smaller chunks and check for cancellation between chunks
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    # Check for cancellation frequently
                    if conversion_cancelled and conversion_cancelled.is_set():
                        temp_input.close()
                        os.unlink(temp_input.name)
                        logging.info("Cancellation detected during file copy")
                        return "Conversion cancelled.", None
                    
                    chunk = original.read(chunk_size)
                    if not chunk:
                        break
                    temp_input.write(chunk)
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
        logging.info("Cancellation detected after file preparation")
        return "Conversion cancelled.", None

    try:
        # Use the parser factory to parse the document
        start = time.time()
        
        # Pass the cancellation flag to the parser factory
        content = ParserFactory.parse_document(
            file_path=file_path,
            parser_name=parser_name,
            ocr_method_name=ocr_method_name,
            output_format=output_format.lower(),
            cancellation_flag=conversion_cancelled  # Pass the flag to parsers
        )
        
        # If content indicates cancellation, return early
        if content == "Conversion cancelled.":
            logging.info("Parser reported cancellation")
            try:
                os.unlink(temp_input.name)
            except:
                pass
            return content, None
        
        duration = time.time() - start
        logging.info(f"Processed in {duration:.2f} seconds.")
        
        # Check for cancellation after processing
        if conversion_cancelled and conversion_cancelled.is_set():
            # Clean up temp file
            try:
                os.unlink(temp_input.name)
            except:
                pass
            logging.info("Cancellation detected after processing")
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
        logging.info("Cancellation detected before output file creation")
        return "Conversion cancelled.", None

    try:
        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as tmp:
            # Write in chunks and check for cancellation
            chunk_size = 10000  # characters
            for i in range(0, len(content), chunk_size):
                # Check for cancellation
                if conversion_cancelled and conversion_cancelled.is_set():
                    tmp.close()
                    os.unlink(tmp.name)
                    try:
                        os.unlink(temp_input.name)
                    except:
                        pass
                    logging.info("Cancellation detected during output file writing")
                    return "Conversion cancelled.", None
                
                tmp.write(content[i:i+chunk_size])
            
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

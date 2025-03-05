from typing import Optional, Dict, Any, Union
from pathlib import Path
import threading
from docling.datamodel.document import Document

from parser_interface import DocumentParser
from parser_registry import ParserRegistry


class ParserFactory:
    """Factory for creating parser instances."""
    
    @classmethod
    def create_parser(cls, parser_name: str) -> Optional[DocumentParser]:
        """
        Create a parser instance.
        
        Args:
            parser_name: Name of the parser to create
            
        Returns:
            An instance of the requested parser or None if not found
        """
        parser_class = ParserRegistry.get_parser_class(parser_name)
        if not parser_class:
            return None
            
        # Instantiate the parser
        return parser_class()
    
    @classmethod
    def parse_document(cls, 
                      file_path: Union[str, Path], 
                      parser_name: str, 
                      ocr_method_name: str,
                      cancellation_flag: Optional[threading.Event] = None,
                      **kwargs) -> str:
        """
        Parse a document using the specified parser and OCR method.
        
        Args:
            file_path: Path to the document
            parser_name: Name of the parser to use
            ocr_method_name: Display name of the OCR method to use
            cancellation_flag: Optional flag to check for cancellation
            **kwargs: Additional parser-specific options
            
        Returns:
            str: The parsed content
        """
        parser = cls.create_parser(parser_name)
        if not parser:
            raise ValueError(f"Unknown parser: {parser_name}")
        
        # Get the internal OCR method ID
        ocr_method_id = ParserRegistry.get_ocr_method_id(parser_name, ocr_method_name)
        if not ocr_method_id:
            raise ValueError(f"Unknown OCR method: {ocr_method_name} for parser {parser_name}")
        
        # Check for cancellation
        if cancellation_flag and cancellation_flag.is_set():
            return "Conversion cancelled."
        
        # Parse the document, passing the cancellation flag
        kwargs['cancellation_flag'] = cancellation_flag
        return parser.parse(file_path, ocr_method=ocr_method_id, **kwargs) 

class BaseParser:
    def __init__(self):
        self._cancellation_check = lambda: False
    
    def set_cancellation_check(self, check_func):
        """Set a function that will be called to check for cancellation."""
        self._cancellation_check = check_func
    
    def is_cancelled(self):
        """Check if processing should be cancelled."""
        return self._cancellation_check()
    
    def parse(self, file_path):
        """Parse the file and return the content."""
        # Initialize document
        document = Document()
        
        # Check for cancellation
        if self.is_cancelled():
            return document
        
        # Open the file
        # ...
        
        # Process each page
        for page_num in range(num_pages):
            # Check for cancellation before processing each page
            if self.is_cancelled():
                return document
            
            # Process page
            # ...
            
            # Check for cancellation after processing each page
            if self.is_cancelled():
                return document
        
        return document
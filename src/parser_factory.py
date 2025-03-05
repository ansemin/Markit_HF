from typing import Optional, Dict, Any, Union
from pathlib import Path
import threading

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
                      output_format: str = "markdown",
                      cancellation_flag: Optional[threading.Event] = None,
                      **kwargs) -> str:
        """
        Parse a document using the specified parser and OCR method.
        
        Args:
            file_path: Path to the document
            parser_name: Name of the parser to use
            ocr_method_name: Display name of the OCR method to use
            output_format: Output format (markdown, json, text, document_tags)
            cancellation_flag: Optional flag to check for cancellation
            **kwargs: Additional parser-specific options
            
        Returns:
            str: The parsed content
        """
        # Check for cancellation immediately
        if cancellation_flag and cancellation_flag.is_set():
            return "Conversion cancelled."
        
        parser = cls.create_parser(parser_name)
        if not parser:
            raise ValueError(f"Unknown parser: {parser_name}")
        
        # Get the internal OCR method ID
        ocr_method_id = ParserRegistry.get_ocr_method_id(parser_name, ocr_method_name)
        if not ocr_method_id:
            raise ValueError(f"Unknown OCR method: {ocr_method_name} for parser {parser_name}")
        
        # Check for cancellation again before starting the parsing
        if cancellation_flag and cancellation_flag.is_set():
            return "Conversion cancelled."
        
        # Parse the document, passing the cancellation flag
        kwargs['cancellation_flag'] = cancellation_flag
        kwargs['output_format'] = output_format
        
        # Add a wrapper to check for cancellation periodically during parsing
        result = parser.parse(file_path, ocr_method=ocr_method_id, **kwargs)
        
        # Check one more time after parsing completes
        if cancellation_flag and cancellation_flag.is_set():
            return "Conversion cancelled."
        
        return result 
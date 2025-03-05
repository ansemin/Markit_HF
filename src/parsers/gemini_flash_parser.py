from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import os
import json
import tempfile
import base64
from PIL import Image
import io

from src.parsers.parser_interface import DocumentParser
from src.parsers.parser_registry import ParserRegistry

# Import the Google Gemini API client
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiFlashParser(DocumentParser):
    """Parser implementation using Gemini Flash 2.0."""
    
    @classmethod
    def get_name(cls) -> str:
        return "Gemini Flash"
    
    @classmethod
    def get_supported_ocr_methods(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "none",
                "name": "None",
                "default_params": {}
            }
        ]
    
    @classmethod
    def get_description(cls) -> str:
        return "Gemini Flash 2.0 parser for converting documents and images to markdown"
    
    def parse(self, file_path: Union[str, Path], ocr_method: Optional[str] = None, **kwargs) -> str:
        """Parse a document using Gemini Flash 2.0."""
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "The Google Gemini API client is not installed. "
                "Please install it with 'pip install google-genai'."
            )
        
        # Get API key from environment variable
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Please set it to your Gemini API key."
            )
        
        # Initialize the Gemini client
        client = genai.Client(api_key=api_key)
        
        # Determine file type based on extension
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        # Read the file content
        file_content = file_path.read_bytes()
        
        # Determine MIME type based on file extension
        mime_type = self._get_mime_type(file_extension)
        
        # Create system prompt for document conversion
        system_prompt = (
            "You are an expert document converter that transforms documents into well-formatted markdown. "
            "Preserve the original structure, formatting, and content as accurately as possible. "
            "Include headers, lists, tables, and other formatting elements appropriately in markdown syntax. "
            "Ignore watermarks, page numbers, and other non-content elements."
        )
        
        # Create user prompt for document conversion
        user_prompt = "Convert the following document to markdown (.md file) format, preserving its structure and formatting."
        
        try:
            # For smaller files (< 20MB), use inline data
            if len(file_content) < 20 * 1024 * 1024:  # 20MB
                # Create a Part object from the file content
                file_part = types.Part.from_bytes(data=file_content, mime_type=mime_type)
                
                # Generate content with the updated format
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        system_prompt,
                        [file_part, user_prompt]
                    ]
                )
            else:
                # For larger files, use the File API
                uploaded_file = client.files.upload(
                    file=io.BytesIO(file_content),
                    config=dict(mime_type=mime_type)
                )
                
                # Generate content with the updated format
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        system_prompt,
                        [uploaded_file, user_prompt]
                    ]
                )
            
            # Format the content based on the requested output format
            output_format = kwargs.get("output_format", "markdown")
            content = response.text
            
            if output_format.lower() == "json":
                return json.dumps({"content": content}, ensure_ascii=False, indent=2)
            elif output_format.lower() == "text":
                # Remove markdown formatting for plain text
                return content.replace("#", "").replace("*", "").replace("_", "")
            elif output_format.lower() == "document_tags":
                return f"<doc>\n{content}\n</doc>"
            else:
                return content
                
        except Exception as e:
            raise Exception(f"Error processing document with Gemini Flash: {str(e)}")
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get the MIME type based on file extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".html": "text/html",
            ".htm": "text/html",
            ".xml": "text/xml",
            ".csv": "text/csv",
            ".md": "text/markdown",
            ".rtf": "text/rtf",
            ".js": "application/javascript",
            ".py": "text/x-python",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            # Add support for Office documents
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ppt": "application/vnd.ms-powerpoint",
            # Add support for other common document types
            ".json": "application/json",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
            ".tex": "application/x-tex",
            ".odt": "application/vnd.oasis.opendocument.text",
            ".ods": "application/vnd.oasis.opendocument.spreadsheet",
            ".odp": "application/vnd.oasis.opendocument.presentation",
        }
        
        return mime_types.get(file_extension, "application/pdf")  # Default to PDF if unknown


# Register the parser with the registry
if GEMINI_AVAILABLE:
    ParserRegistry.register(GeminiFlashParser)
else:
    print("Gemini Flash parser not registered: google-genai package not installed") 
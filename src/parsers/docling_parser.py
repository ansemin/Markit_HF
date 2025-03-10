from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json
import os
import shutil

from src.parsers.parser_interface import DocumentParser
from src.parsers.parser_registry import ParserRegistry
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.models.tesseract_ocr_model import TesseractOcrOptions
from docling.models.tesseract_ocr_cli_model import TesseractCliOcrOptions
from docling.models.ocr_mac_model import OcrMacOptions


class DoclingParser(DocumentParser):
    """Parser implementation using Docling."""
    
    @classmethod
    def get_name(cls) -> str:
        return "Docling"
    
    @classmethod
    def get_supported_ocr_methods(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "no_ocr",
                "name": "No OCR",
                "default_params": {}
            },
            {
                "id": "easyocr",
                "name": "EasyOCR",
                "default_params": {"languages": ["en"]}
            },
            {
                "id": "easyocr_cpu",
                "name": "EasyOCR (CPU only)",
                "default_params": {"languages": ["en"], "use_gpu": False}
            },
            {
                "id": "tesseract",
                "name": "Tesseract",
                "default_params": {}
            },
            {
                "id": "tesseract_cli",
                "name": "Tesseract CLI",
                "default_params": {}
            },
            {
                "id": "ocrmac",
                "name": "ocrmac",
                "default_params": {}
            },
            {
                "id": "full_force_ocr",
                "name": "Full Force OCR",
                "default_params": {}
            }
        ]
    
    def parse(self, file_path: Union[str, Path], ocr_method: Optional[str] = None, **kwargs) -> str:
        """Parse a document using Docling."""
        # Special case for full force OCR
        if ocr_method == "full_force_ocr":
            return self._apply_full_force_ocr(file_path)
        
        # Regular Docling parsing
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        
        # Configure OCR based on the method
        if ocr_method == "no_ocr":
            pipeline_options.do_ocr = False
        elif ocr_method == "easyocr":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options.lang = kwargs.get("languages", ["en"])
            pipeline_options.accelerator_options = AcceleratorOptions(
                num_threads=4, device=AcceleratorDevice.AUTO
            )
        elif ocr_method == "easyocr_cpu":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options.lang = kwargs.get("languages", ["en"])
            pipeline_options.ocr_options.use_gpu = False
        elif ocr_method == "tesseract":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = TesseractOcrOptions()
        elif ocr_method == "tesseract_cli":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = TesseractCliOcrOptions()
        elif ocr_method == "ocrmac":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = OcrMacOptions()
        
        # Create the converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )
        
        # Convert the document
        result = converter.convert(Path(file_path))
        doc = result.document
        
        # Return the content in the requested format
        output_format = kwargs.get("output_format", "markdown")
        if output_format.lower() == "json":
            return json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2)
        elif output_format.lower() == "text":
            return doc.export_to_text()
        elif output_format.lower() == "document_tags":
            return doc.export_to_document_tokens()
        else:
            return doc.export_to_markdown()
    
    def _apply_full_force_ocr(self, file_path: Union[str, Path]) -> str:
        """Apply full force OCR to a document."""
        input_doc = Path(file_path)
        file_extension = input_doc.suffix.lower()
        
        # Debug information
        print(f"Applying full force OCR to file: {input_doc} (type: {file_extension})")
        
        # Set up pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        
        # Find tesseract executable
        tesseract_cmd = None
        tesseract_paths = [
            "tesseract",  # Default PATH
            "/usr/bin/tesseract",  # Common Linux location
            "/app/tesseract/tesseract",  # Possible custom location in Hugging Face
            "/opt/conda/bin/tesseract",  # Possible Conda env in Hugging Face
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows location
        ]
        
        for path in tesseract_paths:
            if shutil.which(path) or (os.path.isfile(path) and os.access(path, os.X_OK)):
                tesseract_cmd = path
                print(f"Found tesseract at: {tesseract_cmd}")
                break
        
        if not tesseract_cmd:
            print("Warning: Tesseract executable not found. Using default configuration.")
            tesseract_cmd = "tesseract"  # Use default as fallback
        
        # Configure OCR options with explicit tesseract path
        ocr_options = TesseractCliOcrOptions(
            force_full_page_ocr=True,
            tesseract_cmd=tesseract_cmd
        )
        pipeline_options.ocr_options = ocr_options
        
        # Set up format options for both PDF and image formats
        format_options = {}
        
        # Always include PDF format option
        format_options[InputFormat.PDF] = PdfFormatOption(
            pipeline_options=pipeline_options,
        )
        
        # For image files, we need to handle them differently
        if file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']:
            # For image files, we'll use the same pipeline options
            # but we need to specify the input format as IMAGE
            print(f"Processing as image file: {file_extension}")
            # Note: InputFormat.IMAGE is used for image files in Docling
            format_options[InputFormat.IMAGE] = PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        
        # Create converter with appropriate format options
        converter = DocumentConverter(format_options=format_options)
        
        try:
            # Convert the document
            result = converter.convert(input_doc)
            doc = result.document
            return doc.export_to_markdown()
        except Exception as e:
            # Provide detailed error information
            print(f"Error during full force OCR: {e}")
            print(f"File type: {file_extension}, File exists: {input_doc.exists()}")
            
            # Try fallback to regular OCR if full force fails
            try:
                print("Attempting fallback to regular tesseract_cli OCR...")
                return self.parse(file_path, ocr_method="tesseract_cli")
            except Exception as fallback_error:
                print(f"Fallback OCR also failed: {fallback_error}")
                return f"OCR failed for {input_doc}. Error: {str(e)}"


# Register the parser with the registry
ParserRegistry.register(DoclingParser) 
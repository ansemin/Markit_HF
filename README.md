---
title: Doc2Md
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.14.0
app_file: app.py
build_script: build.sh
startup_script: setup.sh
pinned: false
---

# Doc2Md: Document to Markdown Converter

## Overview
Doc2Md is a tool that converts various document formats (PDF, DOCX, etc.) to Markdown format. It uses different parsing engines and OCR methods to extract text from documents and convert them to clean, readable Markdown.

## Features
- Convert documents to Markdown, JSON, Text, or Document Tags format
- Multiple parsing engines: PyPdfium, Docling, Marker, and Gemini Flash
- Various OCR options depending on the selected parser
- Page navigation for large documents
- Chat with your documents using AI

## Installation

### For Development (Windows)
```bash
pip install -e .
```

### Gemini Flash Parser
To use the Gemini Flash parser, you need to:
1. Install the Google Gemini API client: `pip install google-genai`
2. Set the `GOOGLE_API_KEY` environment variable with your Gemini API key
   ```bash
   # On Windows
   set GOOGLE_API_KEY=your_api_key_here
   
   # On Linux/Mac
   export GOOGLE_API_KEY=your_api_key_here
   ```
3. You can obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## How to Use

### 1. Upload and Convert
- Upload your document using the file uploader
- Select a parser provider (PyPdfium, Docling, Marker, or Gemini Flash)
- Choose an OCR option based on your selected provider
  - Note: Gemini Flash automatically handles OCR, so no OCR option is needed
- Select your desired output format
- Click "Convert" to process your document
- Navigate through pages using the arrow buttons
- Download the converted file

### 2. Chat with Document
- After converting a document, switch to the "Chat with Document" tab
- Type your questions about the document in the text box
- The AI will respond based on the content of your document
- Use the "Clear" button to reset the conversation

### 3. Configuration
- In the "Config ⚙️" tab, you can adjust:
  - Parser provider
  - OCR options
  - Output format

## Technical Details
This application is built with Python using Gradio for the web interface. It leverages various document parsing libraries to handle different document formats and extraction methods.

## Credits
Developed as an open-source tool for document conversion and analysis.

# Markit

This project uses Tesseract OCR for document processing. The setup is handled automatically through the following scripts:

1. `build.sh` - Runs during the build process to install Tesseract and dependencies
2. `setup.sh` - Runs at startup to configure Tesseract and download language files

## Deployment

When deploying to Hugging Face Spaces, ensure the Space configuration includes:

```yaml
build:
  dockerfile: Dockerfile
  python_version: "3.10" 
  system_packages:
    - "tesseract-ocr"
    - "libtesseract-dev"
```

## Development

For local development, ensure you have Tesseract OCR installed and the TESSDATA_PREFIX environment variable set correctly.

## Recommended Folder Structure

```
markit/
├── app.py                  # Main application entry point
├── setup.sh                # Setup script
├── build.sh                # Build script
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── .env                    # Environment variables
├── .gitignore              # Git ignore file
├── .gitattributes          # Git attributes file
├── src/                    # Source code
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Main module
│   ├── core/               # Core functionality
│   │   ├── __init__.py     # Package initialization
│   │   ├── converter.py    # Document conversion logic
│   │   └── parser_factory.py # Parser factory
│   ├── parsers/            # Parser implementations
│   │   ├── __init__.py     # Package initialization
│   │   ├── parser_interface.py # Parser interface
│   │   ├── parser_registry.py # Parser registry
│   │   ├── docling_parser.py # Docling parser
│   │   ├── marker_parser.py # Marker parser
│   │   └── pypdfium_parser.py # PyPDFium parser
│   ├── ui/                 # User interface
│   │   ├── __init__.py     # Package initialization
│   │   └── ui.py           # Gradio UI implementation
│   └── services/           # External services
│       ├── __init__.py     # Package initialization
│       └── docling_chat.py # Chat service
└── tests/                  # Tests
    └── __init__.py         # Package initialization
```

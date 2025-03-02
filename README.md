
---
title: Doc2Md
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.14.0
app_file: app.py
pinned: false
---

# Doc2Md: Document to Markdown Converter

## Overview
Doc2Md is a tool that converts various document formats (PDF, DOCX, etc.) to Markdown format. It uses different parsing engines and OCR methods to extract text from documents and convert them to clean, readable Markdown.

## Features
- Convert documents to Markdown, JSON, Text, or Document Tags format
- Multiple parsing engines: PyPdfium, Docling, and Marker
- Various OCR options depending on the selected parser
- Page navigation for large documents
- Chat with your documents using AI

## How to Use

### 1. Upload and Convert
- Upload your document using the file uploader
- Select a parser provider (PyPdfium, Docling, or Marker)
- Choose an OCR option based on your selected provider
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

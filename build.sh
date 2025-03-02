#!/bin/bash

# Install system dependencies for tesseract
apt-get update && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev

# Install tesserocr separately with specific options
pip install --no-cache-dir tesserocr

# Install Python dependencies
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
fi
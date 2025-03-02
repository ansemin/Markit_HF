#!/bin/bash

# Install system dependencies for tesseract with more specific packages
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev pkg-config

# Set TESSDATA_PREFIX environment variable
TESSDATA_PREFIX=$(dpkg -L tesseract-ocr-eng | grep tessdata$)
echo "Set TESSDATA_PREFIX=${TESSDATA_PREFIX}"
export TESSDATA_PREFIX

# Uninstall any existing tesserocr and install from source
pip uninstall -y tesserocr
pip install --no-binary :all: tesserocr

# Install ocrmac
pip install ocrmac

# Install Python dependencies
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
fi
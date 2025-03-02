#!/bin/bash

# Exit on error
set -e

# Create tessdata directory if it doesn't exist
TESSDATA_DIR="/usr/share/tesseract-ocr/4.00/tessdata"
mkdir -p "$TESSDATA_DIR"

# Download traineddata files if they don't exist
if [ ! -f "$TESSDATA_DIR/eng.traineddata" ]; then
    echo "Downloading eng.traineddata..."
    wget -O "$TESSDATA_DIR/eng.traineddata" "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata"
fi

if [ ! -f "$TESSDATA_DIR/osd.traineddata" ]; then
    echo "Downloading osd.traineddata..."
    wget -O "$TESSDATA_DIR/osd.traineddata" "https://github.com/tesseract-ocr/tessdata/raw/main/osd.traineddata"
fi

# Set TESSDATA_PREFIX
export TESSDATA_PREFIX="$TESSDATA_DIR"
echo "TESSDATA_PREFIX=${TESSDATA_PREFIX}" >> /etc/environment

# Test Tesseract functionality
echo "Testing Tesseract..."
echo "Hello World" > test.png
tesseract test.png stdout
rm test.png

# Print Tesseract version and available languages
echo "Tesseract version:"
tesseract --version
echo "Available languages:"
tesseract --list-langs 
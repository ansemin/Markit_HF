#!/bin/bash

# Exit on error
set -e

echo "Setting up Tesseract OCR environment..."

# Install google-genai package
echo "Installing Google Gemini API client..."
pip install -q -U google-genai
echo "Google Gemini API client installed successfully"

# Create tessdata directory if it doesn't exist
mkdir -p tessdata

# Set TESSDATA_PREFIX environment variable
export TESSDATA_PREFIX="$(pwd)/tessdata"
echo "TESSDATA_PREFIX set to: $TESSDATA_PREFIX"

# Download eng.traineddata if it doesn't exist
if [ ! -f "tessdata/eng.traineddata" ]; then
  echo "Downloading eng.traineddata..."
  wget -O tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
  echo "Downloaded eng.traineddata"
else
  echo "eng.traineddata already exists"
fi

# Also copy to system location
if [ -d "/usr/local/share/tessdata" ]; then
  echo "Copying eng.traineddata to system location..."
  sudo cp -f tessdata/eng.traineddata /usr/local/share/tessdata/ || echo "Failed to copy to system location, continuing anyway"
fi

# Verify Tesseract installation
echo "Verifying Tesseract installation..."
tesseract --version || echo "Tesseract not found in PATH"

# Test Tesseract functionality
echo "Testing Tesseract functionality..."
echo "Hello World" > test.txt
convert -size 100x30 xc:white -font Arial -pointsize 12 -fill black -annotate +10+20 "Hello World" test.png || echo "ImageMagick convert not available, skipping test image creation"

if [ -f "test.png" ]; then
  tesseract test.png test_output || echo "Tesseract test failed, but continuing"
  if [ -f "test_output.txt" ]; then
    echo "Tesseract test output:"
    cat test_output.txt
  fi
fi

echo "Setup completed"

# Add these diagnostic commands at the end of your setup.sh
echo "Checking Tesseract location:"
which tesseract || echo "Tesseract not found in PATH"
whereis tesseract
echo "Current PATH: $PATH"
echo "TESSDATA_PREFIX: $TESSDATA_PREFIX"
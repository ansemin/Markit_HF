#!/bin/bash

# Exit on error
set -e

echo "Starting build process..."

# Install system dependencies for tesseract with more specific packages
echo "Installing Tesseract and dependencies..."
apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    build-essential

# Create tessdata directory if it doesn't exist
mkdir -p /usr/share/tesseract-ocr/4.00/tessdata

# Verify tesseract installation
if ! command -v tesseract &> /dev/null; then
    echo "Tesseract installation failed!"
    exit 1
fi
echo "Tesseract version: $(tesseract --version)"

# Set and export TESSDATA_PREFIX
export TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata"
echo "Set TESSDATA_PREFIX=${TESSDATA_PREFIX}"

# Add TESSDATA_PREFIX to environment for persistence
echo "TESSDATA_PREFIX=${TESSDATA_PREFIX}" >> /etc/environment

# Verify tessdata directory and contents
if [ ! -d "$TESSDATA_PREFIX" ]; then
    echo "Creating tessdata directory..."
    mkdir -p "$TESSDATA_PREFIX"
fi

echo "Tessdata directory contents:"
ls -l $TESSDATA_PREFIX

# Test Tesseract functionality
echo "Testing Tesseract functionality..."
echo "Hello World" > test.png
if ! tesseract test.png stdout; then
    echo "Tesseract test failed!"
    exit 1
fi
rm test.png

# Clean any existing tesserocr installation
echo "Cleaning existing tesserocr installation..."
pip uninstall -y tesserocr || true

# Install tesserocr from source with proper configuration
echo "Installing tesserocr from source..."
CPPFLAGS=-I/usr/include/tesseract/ LDFLAGS=-L/usr/lib/x86_64-linux-gnu/ pip install --no-binary :all: tesserocr

# Verify tesserocr installation
echo "Verifying tesserocr installation..."
python3 -c "import tesserocr; print(f'tesserocr version: {tesserocr.__version__}')"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env || echo "Warning: .env.example not found"
fi

echo "Build process completed successfully!"
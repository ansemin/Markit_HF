#!/bin/bash

# Exit on error
set -e

echo "Starting build process..."

# Install system dependencies for tesseract with more specific packages
echo "Installing Tesseract and dependencies..."
apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config

# Verify tesseract installation
if ! command -v tesseract &> /dev/null; then
    echo "Tesseract installation failed!"
    exit 1
fi
echo "Tesseract version: $(tesseract --version)"

# Set TESSDATA_PREFIX environment variable
TESSDATA_PREFIX=$(dpkg -L tesseract-ocr-eng | grep tessdata$)
if [ -z "$TESSDATA_PREFIX" ]; then
    echo "Could not find tessdata directory!"
    exit 1
fi
echo "Set TESSDATA_PREFIX=${TESSDATA_PREFIX}"
export TESSDATA_PREFIX

# Add TESSDATA_PREFIX to environment for persistence
echo "TESSDATA_PREFIX=${TESSDATA_PREFIX}" >> /etc/environment

# Verify tessdata directory
if [ ! -d "$TESSDATA_PREFIX" ]; then
    echo "Tessdata directory does not exist!"
    exit 1
fi
echo "Tessdata directory contents:"
ls -l $TESSDATA_PREFIX

# Uninstall any existing tesserocr and install from source
echo "Installing tesserocr from source..."
pip uninstall -y tesserocr || true
pip install --no-binary :all: tesserocr

# Install ocrmac
echo "Installing ocrmac..."
pip install ocrmac

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

echo "Build process completed successfully!"
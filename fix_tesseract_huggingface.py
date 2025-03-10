#!/usr/bin/env python
"""
Script to diagnose and fix Tesseract issues in Hugging Face environments.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import urllib.request

def diagnose_tesseract():
    """Diagnose Tesseract installation and configuration issues."""
    print("=== Tesseract Diagnostics ===")
    
    # Check OS
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    # Check if tesseract is in PATH
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        print(f"✅ Tesseract found in PATH: {tesseract_path}")
        try:
            version = subprocess.check_output(["tesseract", "--version"], 
                                             stderr=subprocess.STDOUT, 
                                             universal_newlines=True)
            print(f"✅ Tesseract version info:\n{version.splitlines()[0]}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"❌ Error running tesseract: {e}")
    else:
        print("❌ Tesseract not found in PATH")
    
    # Check common installation locations
    common_locations = [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/conda/bin/tesseract",
        "/app/tesseract/tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    ]
    
    for location in common_locations:
        if os.path.isfile(location) and os.access(location, os.X_OK):
            print(f"✅ Tesseract executable found at: {location}")
    
    # Check TESSDATA_PREFIX
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if tessdata_prefix:
        print(f"✅ TESSDATA_PREFIX is set to: {tessdata_prefix}")
        if os.path.exists(tessdata_prefix):
            print(f"✅ TESSDATA_PREFIX directory exists")
            eng_traineddata = os.path.join(tessdata_prefix, "eng.traineddata")
            if os.path.exists(eng_traineddata):
                print(f"✅ eng.traineddata found at: {eng_traineddata}")
            else:
                print(f"❌ eng.traineddata not found at: {eng_traineddata}")
        else:
            print(f"❌ TESSDATA_PREFIX directory does not exist: {tessdata_prefix}")
    else:
        print("❌ TESSDATA_PREFIX environment variable not set")
    
    # Check pytesseract
    try:
        import pytesseract
        print(f"✅ pytesseract is installed")
        print(f"✅ pytesseract.tesseract_cmd = {pytesseract.pytesseract.tesseract_cmd}")
    except ImportError:
        print("❌ pytesseract is not installed")
    
    # Check tesserocr
    try:
        import tesserocr
        print(f"✅ tesserocr is installed")
        print(f"✅ tesserocr version: {tesserocr.tesseract_version()}")
    except ImportError:
        print("❌ tesserocr is not installed")
    except Exception as e:
        print(f"❌ Error importing tesserocr: {e}")

def fix_tesseract():
    """Fix common Tesseract issues."""
    print("\n=== Fixing Tesseract Issues ===")
    
    # Create local tessdata directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tessdata_dir = os.path.join(current_dir, "tessdata")
    os.makedirs(tessdata_dir, exist_ok=True)
    print(f"✅ Created local tessdata directory: {tessdata_dir}")
    
    # Set TESSDATA_PREFIX to our local directory
    os.environ['TESSDATA_PREFIX'] = tessdata_dir
    print(f"✅ Set TESSDATA_PREFIX to: {tessdata_dir}")
    
    # Download eng.traineddata
    eng_traineddata = os.path.join(tessdata_dir, "eng.traineddata")
    if not os.path.exists(eng_traineddata):
        try:
            print("Downloading eng.traineddata...")
            url = "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata"
            urllib.request.urlretrieve(url, eng_traineddata)
            print("✅ Downloaded eng.traineddata")
        except Exception as e:
            print(f"❌ Error downloading eng.traineddata: {e}")
    else:
        print("✅ eng.traineddata already exists")
    
    # Configure pytesseract
    try:
        import pytesseract
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✅ Set pytesseract.tesseract_cmd to {tesseract_path}")
        else:
            # Try common locations
            common_locations = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/app/tesseract/tesseract"
            ]
            for location in common_locations:
                if os.path.isfile(location) and os.access(location, os.X_OK):
                    pytesseract.pytesseract.tesseract_cmd = location
                    print(f"✅ Set pytesseract.tesseract_cmd to {location}")
                    break
    except ImportError:
        print("❌ pytesseract not installed, please install it with: pip install pytesseract")
    
    # Add TESSDATA_PREFIX to .env file for persistence
    try:
        with open(".env", "a") as f:
            f.write(f"\nTESSDATAFIX_PREFIX={tessdata_dir}\n")
        print("✅ Added TESSDATA_PREFIX to .env file")
    except Exception as e:
        print(f"❌ Error adding TESSDATA_PREFIX to .env file: {e}")
    
    print("\n=== Tesseract Fix Complete ===")
    print("Please restart your application for changes to take effect.")

if __name__ == "__main__":
    diagnose_tesseract()
    fix_tesseract() 
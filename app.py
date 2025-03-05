import sys
import os
import subprocess
import shutil
from pathlib import Path
import urllib.request

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, skipping .env file loading")

# Set TESSDATA_PREFIX if not already set
if not os.environ.get('TESSDATA_PREFIX'):
    tessdata_dir = "/usr/share/tesseract-ocr/4.00/tessdata"
    if os.path.exists(tessdata_dir):
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        print(f"Set TESSDATA_PREFIX to {tessdata_dir}")

# Load Gemini API key from environment variable
gemini_api_key = os.getenv("GOOGLE_API_KEY")

# Check if API key is available and print a message if not
if not gemini_api_key:
    print("Warning: GOOGLE_API_KEY environment variable not found. Gemini Flash parser may not work.")
else:
    print(f"Found Gemini API key: {gemini_api_key[:5]}...{gemini_api_key[-5:] if len(gemini_api_key) > 10 else ''}")

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to the Python path
sys.path.append(current_dir)

# Try different import approaches
try:
    # First attempt - standard import
    from src.main import main
except ModuleNotFoundError:
    try:
        # Second attempt - adjust path and try again
        sys.path.append(os.path.join(current_dir, "src"))
        from main import main
    except ModuleNotFoundError:
        # Third attempt - create __init__.py if it doesn't exist
        init_path = os.path.join(current_dir, "src", "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                pass  # Create empty __init__.py file
        # Try import again
        from src.main import main

# Function to setup Tesseract
def setup_tesseract():
    """Setup Tesseract OCR environment."""
    # Create tessdata directory if it doesn't exist
    tessdata_dir = os.path.join(current_dir, "tessdata")
    os.makedirs(tessdata_dir, exist_ok=True)
    
    # Set TESSDATA_PREFIX environment variable if not already set
    if not os.environ.get('TESSDATA_PREFIX'):
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        print(f"Set TESSDATA_PREFIX to {tessdata_dir}")
    
    # Download eng.traineddata if it doesn't exist
    eng_traineddata = os.path.join(tessdata_dir, "eng.traineddata")
    if not os.path.exists(eng_traineddata):
        try:
            print("Downloading eng.traineddata...")
            url = "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata"
            urllib.request.urlretrieve(url, eng_traineddata)
            print("Downloaded eng.traineddata")
        except Exception as e:
            print(f"Error downloading eng.traineddata: {e}")

# Call setup function at import time
setup_tesseract()

if __name__ == "__main__":
    main()
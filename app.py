import sys
import os
import subprocess
import shutil
from pathlib import Path
import urllib.request

# Set TESSDATA_PREFIX if not already set
if not os.environ.get('TESSDATA_PREFIX'):
    tessdata_dir = "/usr/share/tesseract-ocr/4.00/tessdata"
    if os.path.exists(tessdata_dir):
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        print(f"Set TESSDATA_PREFIX to {tessdata_dir}")

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

# Set up Tesseract environment
def setup_tesseract():
    # Create tessdata directory if it doesn't exist
    tessdata_dir = os.path.join(os.getcwd(), "tessdata")
    os.makedirs(tessdata_dir, exist_ok=True)
    
    # Set TESSDATA_PREFIX environment variable
    os.environ["TESSDATA_PREFIX"] = tessdata_dir
    print(f"TESSDATA_PREFIX set to: {os.environ.get('TESSDATA_PREFIX')}")
    
    # Check if eng.traineddata exists, if not download it
    eng_traineddata = os.path.join(tessdata_dir, "eng.traineddata")
    if not os.path.exists(eng_traineddata):
        print("Downloading eng.traineddata...")
        url = "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata"
        try:
            urllib.request.urlretrieve(url, eng_traineddata)
            print(f"Successfully downloaded eng.traineddata to {eng_traineddata}")
        except Exception as e:
            print(f"Failed to download eng.traineddata: {e}")
    else:
        print(f"eng.traineddata already exists at {eng_traineddata}")
    
    # Also check system location as a fallback
    system_tessdata = "/usr/local/share/tessdata"
    if os.path.exists(system_tessdata):
        print(f"System tessdata directory exists at {system_tessdata}")
        # Copy eng.traineddata to system location if it doesn't exist there
        system_eng_traineddata = os.path.join(system_tessdata, "eng.traineddata")
        if not os.path.exists(system_eng_traineddata) and os.path.exists(eng_traineddata):
            try:
                shutil.copy(eng_traineddata, system_eng_traineddata)
                print(f"Copied eng.traineddata to {system_eng_traineddata}")
            except Exception as e:
                print(f"Failed to copy eng.traineddata to system location: {e}")

# Call setup function at import time
setup_tesseract()

if __name__ == "__main__":
    main()
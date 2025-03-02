import sys
import os

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

if __name__ == "__main__":
    main()
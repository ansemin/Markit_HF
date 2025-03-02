import sys
import os

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.append(src_path)

# Import the main function from the main module
from src.main import main

# Call the main function when the script is executed
if __name__ == "__main__":
    main()
import sys
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to the Python path
sys.path.append(current_dir)

# Now import from src
from src.main import main

if __name__ == "__main__":
    main()
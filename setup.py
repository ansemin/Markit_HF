import os
import sys
from setuptools import setup, find_packages

# Define platform-specific dependencies
if sys.platform.startswith('win'):
    # Windows-specific dependencies
    platform_deps = []
else:
    # Linux/Mac dependencies for Hugging Face
    platform_deps = [
        'tesserocr>=2.5.0',  # Use pip version on Linux
    ]
    
    # For Linux environments, try to install system dependencies
    if os.path.exists('/usr/bin/apt-get'):
        print("Installing system dependencies for tesseract...")
        os.system("apt-get update && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev")

setup(
    name="doc2md",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core dependencies from requirements.txt
        "docling==2.18.0",
        "gradio==5.14.0",
        "grpcio-status==1.70.0",
        "markdown==3.7",
        "marker-pdf==1.3.5",
        "multiprocess==0.70.17",
        "openai==1.61.1",
        "pipdeptree==2.25.0",
        "pytesseract==0.3.13",
        "semchunk==2.2.2",
        "tesseract==0.1.3",
    ] + platform_deps,
)
# Document Processor with OCR and LaTeX Recognition

A Flask-based web application that processes PDF documents to extract text, images, and LaTeX formulas using Tesseract OCR and pix2tex.

## Table of Contents
- [Features](#features)
- [GitHub Setup](#github-setup)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)

## Features

- **Document Upload**: Upload PDF files for processing
- **Text Extraction**: Extract text content from documents using Tesseract OCR
- **Image Extraction**: Extract embedded images from PDFs
- **LaTeX Formula Recognition**: Detect and extract mathematical formulas using pix2tex
- **Searchable History**: View and download previously processed documents
- **Multiple Output Formats**: Download extracted content as text or JSON

## GitHub Setup

Follow these steps to add this project to your GitHub repository:

1. **Initialize Git** (if not already initialized):
   ```bash
   git init
   ```

2. **Add all files to Git**:
   ```bash
   git add .
   ```

3. **Commit your files**:
   ```bash
   git commit -m "Initial commit"
   ```

4. **Add your GitHub repository as the remote origin**:
   ```bash
   git remote add origin https://github.com/sheezan2021/ocr_pdf_text_image.git
   ```

5. **Rename the default branch to main** (if needed):
   ```bash
   git branch -M main
   ```

6. **Push your code to GitHub**:
   ```bash
   git push -u origin main
   ```

7. **Enter your GitHub credentials** when prompted

## Prerequisites

A Flask-based web application that processes PDF documents to extract text, images, and LaTeX formulas using Tesseract OCR and pix2tex.

## Features

- **Document Upload**: Upload PDF files for processing
- **Text Extraction**: Extract text content from documents using Tesseract OCR
- **Image Extraction**: Extract embedded images from PDFs
- **LaTeX Formula Recognition**: Detect and extract mathematical formulas using pix2tex
- **Searchable History**: View and download previously processed documents
- **Multiple Output Formats**: Download extracted content as text or JSON

## Prerequisites

- Python 3.8+
- Tesseract OCR installed on your system
- Poppler (for PDF to image conversion on Linux/Mac)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd DocProcessor_pytesseract
   ```

2. Install Tesseract OCR:
   - **Windows**: Download and install from [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Update the Tesseract path in `app.py` if needed:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path
   ```

2. Configure database (SQLite is used by default):
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ocr_data.db'
   ```

## Usage

1. Run the Flask application:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload a PDF document and wait for processing

4. View the extracted content and download results in your preferred format

## Project Structure

- `app.py`: Main application file with all routes and processing logic
- `templates/`: HTML templates for the web interface
  - `index.html`: Main upload page
  - `result.html`: Results display page
  - `history.html`: Processed documents history
- `static/`: Static files including extracted images
- `uploads/`: Temporary storage for uploaded files
- `outputs/`: Processed text and JSON output files
- `migrations/`: Database migration files

## Dependencies

- **Flask**: Web application framework
- **PyTesseract**: Python wrapper for Tesseract OCR
- **PyMuPDF (fitz)**: PDF processing and image extraction
- **pix2tex**: LaTeX formula recognition
- **SQLAlchemy**: Database ORM
- **Pillow**: Image processing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Notes

- For best results with LaTeX formula recognition, ensure good image quality
- Large PDFs may take longer to process
- The application is configured to handle files up to 16MB by default

import os
import json
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, send_file, redirect, url_for, send_from_directory
from PyPDF2 import PdfReader
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime
import fitz  # PyMuPDF
from pix2tex.cli import LatexOCR

# Initialize LaTeX OCR model
try:
    latex_ocr_model = LatexOCR()
except Exception as e:
    print(f"Warning: Could not initialize LaTeX OCR model: {e}")
    latex_ocr_model = None

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Setup
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
EXTRACTED_IMAGES_FOLDER = 'static/extracted_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_IMAGES_FOLDER, exist_ok=True)

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ocr_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class OCRData(db.Model):
    __tablename__ = 'ocr_data'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    extracted_json = db.Column(db.Text)
    extracted_images = db.Column(db.Text)  # Store JSON list of image paths
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf'}

def extract_images_from_pdf(pdf_path, output_folder):
    images = []
    try:
        # Ensure output directory exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Counter for naming extracted images
        img_count = 0
        
        # Iterate through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Get the page's image list
            image_list = page.get_images(full=True)
            
            # If images are found in the page
            if image_list:
                for img_index, img in enumerate(image_list, 1):
                    try:
                        # Get the image
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Always use .jpeg extension and forward slashes for web
                        img_count += 1
                        img_filename = f"{base_filename}_img_{img_count}.jpeg"
                        img_path = os.path.join(output_folder, img_filename)
                        
                        # Save the image as JPEG
                        with open(img_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        # Store web-friendly path (forward slashes)
                        rel_path = f"extracted_images/{img_filename}"
                        images.append(rel_path)
                        
                        print(f"Extracted image: {img_path}")
                        
                    except Exception as img_err:
                        print(f"Error extracting image {img_index} from page {page_num + 1}: {img_err}")
                        import traceback
                        traceback.print_exc()
        
        pdf_document.close()
        
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return images
def extract_formulas_from_image(image_path):
    """Extract LaTeX formulas from an image using pix2tex."""
    if not latex_ocr_model:
        return None
        
    try:
        # Open and preprocess the image
        img = Image.open(image_path)
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Extract formula
        formula = latex_ocr_model(img)
        return formula
    except Exception as e:
        print(f"Error extracting formula: {e}")
        return None
def process_file(file_path):
    import re
    text = ''
    extracted_images = []
    json_lines = []
    image_counter = 0
    try:
        if file_path.lower().endswith('.pdf'):
            doc = fitz.open(file_path)
            pages_json = []
            for page_num, page in enumerate(doc, 1):
                page_dict = page.get_text("dict", sort=True)
                page_width = page.rect.width
                page_height = page.rect.height
                page_blocks = []
                for block in page_dict["blocks"]:
                    if block["type"] == 0:  # text block
                        for line in block["lines"]:
                            spans = []
                            for span in line["spans"]:
                                span_text = span.get("text", "")
                                bbox = span.get("bbox", None)
                                if span_text.strip() and bbox:
                                    spans.append({
                                        "text": span_text,
                                        "bbox": bbox
                                    })
                            if not spans:
                                continue
                            line_text = "".join(s["text"] for s in spans)
                            min_x = min(s["bbox"][0] for s in spans)
                            min_y = min(s["bbox"][1] for s in spans)
                            max_x = max(s["bbox"][2] for s in spans)
                            max_y = max(s["bbox"][3] for s in spans)
                            page_blocks.append({
                                "type": "text",
                                "content": line_text,
                                "x": min_x,
                                "y": min_y,
                                "width": max_x - min_x,
                                "height": max_y - min_y
                            })
                    elif block["type"] == 1:  # image block
                        image_bytes = block.get("image")
                        bbox = block.get("bbox", None)
                        if image_bytes:
                            image_counter += 1
                            img_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_img_{image_counter}.png"
                            img_path = os.path.join(EXTRACTED_IMAGES_FOLDER, img_filename)
                            with open(img_path, "wb") as img_file:
                                img_file.write(image_bytes)
                            rel_path = f"extracted_images/{img_filename}"
                            extracted_images.append(rel_path)
                            page_blocks.append({
                                "type": "image",
                                "path": rel_path,
                                "x": bbox[0] if bbox else None,
                                "y": bbox[1] if bbox else None,
                                "width": (bbox[2] - bbox[0]) if bbox else None,
                                "height": (bbox[3] - bbox[1]) if bbox else None
                            })
                pages_json.append({
                    "page_num": page_num,
                    "width": page_width,
                    "height": page_height,
                    "blocks": page_blocks
                })
            doc.close()
            # Compose text output for legacy display and .txt file
            def line_to_text(line):
                if line.get("type") == "text":
                    return line.get("content", "")
                elif line.get("type") == "formula":
                    return line.get("latex", "")
                elif line.get("type") == "image":
                    return f"[IMAGE: {line.get('path', '')}]"
                elif line.get("type") == "mixed":
                    return "".join(line_to_text(p) for p in line.get("parts", []))
                else:
                    return ""
            text = "\n".join(line_to_text(line) for page in pages_json for line in page["blocks"])
            json_data = pages_json
        else:
            image = Image.open(file_path)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image)
            formula = extract_formulas_from_image(file_path)
            formulas = []
            if formula:
                formulas.append({
                    'latex': formula,
                    'type': 'formula',
                    'source_image': None
                })
            img_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.jpeg"
            img_save_path = os.path.join(EXTRACTED_IMAGES_FOLDER, img_filename)
            os.makedirs(EXTRACTED_IMAGES_FOLDER, exist_ok=True)
            image.save(img_save_path, 'JPEG')
            rel_path = f"extracted_images/{img_filename}"
            extracted_images = [rel_path]
            json_data = [{"type": "image", "path": rel_path}]
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        json_data = []
        text = ''
    return text, json.dumps(json_data, indent=2, ensure_ascii=False), extracted_images

@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        text_output, json_output, extracted_images = process_file(file_path)
        
        # Save to files
        txt_path = os.path.join(OUTPUT_FOLDER, filename + '.txt')
        json_path = os.path.join(OUTPUT_FOLDER, filename + '.json')

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_output)
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_output)

        # Save to DB
        db_entry = OCRData(
            filename=filename,
            extracted_text=text_output,
            extracted_json=json_output,
            extracted_images=json.dumps(extracted_images)
        )
        db.session.add(db_entry)
        db.session.commit()

        return render_template('result.html', 
                             filename=filename,
                             text=text_output,
                             json_data=json.loads(json_output) if json_output else {},
                             extracted_images=extracted_images,
                             entry_id=db_entry.id,
                             now=datetime.datetime.utcnow())

    return 'Invalid file type'

@app.route('/download/<filename>/<filetype>')
def download_file(filename, filetype):
    file_path = os.path.join(OUTPUT_FOLDER, filename + ('.txt' if filetype == 'text' else '.json'))
    return send_file(file_path, as_attachment=True)

@app.route('/history')
def history():
    entries = OCRData.query.order_by(OCRData.uploaded_at.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/view/<int:entry_id>')
def view_entry(entry_id):
    entry = OCRData.query.get_or_404(entry_id)
    print(f"\n=== DEBUG: Processing entry {entry_id} ===")
    print(f"Filename: {entry.filename}")
    
    # Parse JSON data
    json_data = []
    if entry.extracted_json:
        try:
            json_data = json.loads(entry.extracted_json)
            print(f"Loaded JSON data, type: {type(json_data)}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            json_data = []
    else:
        print("No JSON data found in entry")
        json_data = []
    
    # No longer process images or text_blocks as keys
    # Just pass the list to the template
    return render_template('view.html', 
        entry=entry,
        json_data=json_data,
        debugInfo=True)

# Route to serve extracted images
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

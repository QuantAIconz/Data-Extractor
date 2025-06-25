import os
import re
import fitz
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from validators import DataValidator
from dashboard import DataVisualizer
import PyPDF2
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from nameparser import HumanName
import requests
import logging
import spacy

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['STATIC_FOLDER'] = 'static'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'dashboard'), exist_ok=True)

# Regular expressions for different types of data
PATTERNS = {
    'full_name': r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b',
    'date_of_birth': r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b',
    'mobile_number': r'(?:\+91[- ]?)?[6-9]\d{9}',
    'telephone_number': r'(?:\+?\d{1,4}[- ]?)?\d{2,4}[- ]?\d{3,4}[- ]?\d{3,4}',
    'email_address': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'residential_address': r'\b\d+\s+[A-Za-z\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl)[,\s]+[A-Za-z\s,.-]+(?:[A-Z]{2})\s+\d{5}(?:-\d{4})?\b',
    'aadhar_number': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    'pan_number': r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
    'passport_number': r'\b[A-Z0-9]{6,9}\b',
    'voter_id_number': r'\b[A-Z]{3}[0-9]{7}\b',
    'driving_license_number': r'\b[A-Z]{2}[0-9]{2}[- ]?[A-Z0-9]{1,2}[- ]?\d{4,7}\b',
    'bank_account_number': r'\b[0-9]{8,18}\b',
    'credit_debit_card_number': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})\b',
    'ip_address': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
    'custom_search': None
}

# Store extracted data in memory (in a real application, use a database)
extracted_data = []

# Load spaCy model globally
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    import subprocess
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

def validate_and_format_full_name(name):
    try:
        logger.info(f"Validating name: {name}")
        
        # Remove extra spaces and special characters
        name = re.sub(r'[^\w\s]', '', name.strip())
        name = ' '.join(name.split())
        
        logger.info(f"Cleaned name: {name}")
        
        if not name:
            logger.warning("Empty name after cleaning")
            return None, "Name cannot be empty"
        
        # Parse the name
        parsed_name = HumanName(name)
        logger.info(f"Parsed name components: {parsed_name.as_dict()}")
        
        # Check if we have at least a first name
        if not parsed_name.first:
            logger.warning("No first name found")
            return None, "Invalid name format"
        
        # Format the name
        formatted_name = ' '.join(filter(None, [
            parsed_name.first,
            parsed_name.middle,
            parsed_name.last
        ]))
        
        logger.info(f"Formatted name: {formatted_name}")
        
        # Validate with genderize.io API
        try:
            response = requests.get(f'https://api.genderize.io/?name={parsed_name.first}')
            if response.status_code == 200:
                data = response.json()
                if data.get('probability', 0) > 0.6:
                    logger.info(f"Name validated by genderize.io: {data}")
                    return formatted_name, None
        except Exception as e:
            logger.warning(f"Genderize API error: {str(e)}")
        
        # If API validation fails, use basic validation
        if len(formatted_name.split()) >= 1 and all(len(part) >= 2 for part in formatted_name.split()):
            logger.info("Name passed basic validation")
            return formatted_name, None
        
        logger.warning("Name failed all validation checks")
        return None, "Invalid name format"
        
    except Exception as e:
        logger.error(f"Error in name validation: {str(e)}")
        return None, str(e)

def validate_and_format_mobile_number(number):
    try:
        # Remove any non-digit characters
        number = re.sub(r'\D', '', number)
        
        # Check if the number starts with a valid country code
        if not number.startswith('+'):
            if number.startswith('91'):
                number = '+' + number
            else:
                number = '+91' + number
        
        # Parse the number
        parsed_number = phonenumbers.parse(number)
        
        # Validate the number
        if phonenumbers.is_valid_number(parsed_number):
            # Format the number
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted_number, None
        else:
            return None, "Invalid mobile number"
    except Exception as e:
        return None, str(e)

def validate_and_format_email(email):
    try:
        # Validate and normalize the email
        valid = validate_email(email)
        return valid.email, None
    except EmailNotValidError as e:
        return None, str(e)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    page_texts = []  # Store text for each page
    for page in doc:
        page_text = page.get_text()
        text += page_text
        page_texts.append(page_text)
    return text, page_texts

def extract_data(text, pattern_type, page_texts=None, search_term=None):
    """Extract data using the specified pattern."""
    results = []
    seen_values = set()  # Set to keep track of seen values
    validator = DataValidator.get_validator_for_type(pattern_type)

    if pattern_type == 'custom_search':
        # For custom search, find all occurrences with page numbers
        search_term = re.escape(search_term)  # Escape special characters
        pattern = re.compile(search_term, re.IGNORECASE)

        for page_num, page_text in enumerate(page_texts, 1):
            matches = pattern.finditer(page_text)
            for match in matches:
                value = match.group()
                if value not in seen_values:
                    seen_values.add(value)
                    results.append({
                        'value': value,
                        'page': page_num,
                        'is_valid': True,
                        'validation_message': None,
                        'status': 'correct',
                        'pattern_type': pattern_type
                    })
        return results
    else:
        # For other patterns, return unique matches with page numbers
        pattern = PATTERNS[pattern_type]
        results = []  # Re-initialize results for non-custom patterns
        seen_values = set()  # Re-initialize seen_values

        for page_num, page_text in enumerate(page_texts, 1):
            matches = re.finditer(pattern, page_text, re.MULTILINE)
            for match in matches:
                value = match.group().strip()
                if value not in seen_values:
                    seen_values.add(value)
                    
                    # Validate and format the value if a validator exists
                    if validator:
                        formatted_value, error_message, status = validator(value)
                        results.append({
                            'value': formatted_value if formatted_value else value,
                            'page': page_num,
                            'is_valid': status == 'correct',
                            'validation_message': error_message,
                            'status': status,
                            'pattern_type': pattern_type
                        })
                    else:
                        results.append({
                            'value': value,
                            'page': page_num,
                            'is_valid': True,
                            'validation_message': None,
                            'status': 'correct',
                            'pattern_type': pattern_type
                        })
        return results

def extract_data_from_pdf(pdf_path, pattern_type, search_term=None):
    results = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            if not text or text.strip() == '':
                logger.warning(f"No extractable text found on page {page_num+1} of {pdf_path}")
                continue

            if pattern_type == 'full_name':
                # Use spaCy NER to extract PERSON entities
                doc_spacy = nlp(text)
                seen_names = set()
                for ent in doc_spacy.ents:
                    if ent.label_ == 'PERSON':
                        name = ent.text.strip()
                        if name and name not in seen_names:
                            seen_names.add(name)
                            formatted_name, error = validate_and_format_full_name(name)
                            if formatted_name:
                                results.append({
                                    'value': formatted_name,
                                    'page': page_num + 1,
                                    'status': 'correct',
                                    'validation_message': None,
                                    'pattern_type': pattern_type
                                })
                            elif error:
                                results.append({
                                    'value': name,
                                    'page': page_num + 1,
                                    'status': 'incorrect',
                                    'validation_message': error,
                                    'pattern_type': pattern_type
                                })
            elif pattern_type == 'mobile_number':
                mobile_patterns = [
                    r'(?:\+91|91)?[6-9]\d{9}',
                    r'(?:\+91|91)?[789]\d{9}'
                ]
                for pattern in mobile_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        number = match.group()
                        formatted_number, error = validate_and_format_mobile_number(number)
                        if formatted_number:
                            results.append({
                                'value': formatted_number,
                                'page': page_num + 1,
                                'status': 'correct',
                                'validation_message': None,
                                'pattern_type': pattern_type
                            })
                        elif error:
                            results.append({
                                'value': number,
                                'page': page_num + 1,
                                'status': 'incorrect',
                                'validation_message': error,
                                'pattern_type': pattern_type
                            })
            elif pattern_type == 'email_address':
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                matches = re.finditer(email_pattern, text)
                for match in matches:
                    email = match.group()
                    formatted_email, error = validate_and_format_email(email)
                    if formatted_email:
                        results.append({
                            'value': formatted_email,
                            'page': page_num + 1,
                            'status': 'correct',
                            'validation_message': None,
                            'pattern_type': pattern_type
                        })
                    elif error:
                        results.append({
                            'value': email,
                            'page': page_num + 1,
                            'status': 'incorrect',
                            'validation_message': error,
                            'pattern_type': pattern_type
                        })
            elif pattern_type == 'custom_search' and search_term:
                pattern = re.escape(search_term)
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    results.append({
                        'value': match.group(),
                        'page': page_num + 1,
                        'status': 'correct',
                        'validation_message': None,
                        'pattern_type': pattern_type
                    })
        return results
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}")
        return []

@app.route('/')
def root():
    return redirect(url_for('landing'))

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Read the latest results from extracted_data
    if extracted_data:
        # Convert extracted_data to the format expected by DataVisualizer
        formatted_data = []
        for item in extracted_data:
            formatted_item = {
                'type': item.get('pattern_type', 'unknown'),
                'value': item.get('value', ''),
                'page': item.get('page', 1),
                'status': item.get('status', 'unknown'),
                'validation_message': item.get('validation_message', ''),
                'filename': item.get('filename', 'Unknown File'),
                'timestamp': datetime.now()
            }
            formatted_data.append(formatted_item)
        
        visualizer = DataVisualizer(formatted_data)
        dashboard_path = visualizer.export_dashboard()
        return redirect(url_for('static', filename=f'dashboard/index_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'))
    
    return jsonify({'error': 'No data available for visualization'}), 404

@app.route('/dashboard-data')
def dashboard_data():
    try:
        # Calculate summary statistics
        total = len(extracted_data)
        valid = sum(1 for item in extracted_data if item['status'] == 'correct')
        invalid = total - valid
        success_rate = round((valid / total * 100) if total > 0 else 0, 2)
        
        # Group by filename if available
        files_processed = {}
        for item in extracted_data:
            filename = item.get('filename', 'Unknown File')
            if filename not in files_processed:
                files_processed[filename] = {'total': 0, 'valid': 0, 'invalid': 0}
            
            files_processed[filename]['total'] += 1
            if item['status'] == 'correct':
                files_processed[filename]['valid'] += 1
            else:
                files_processed[filename]['invalid'] += 1
        
        return jsonify({
            'success': True,
            'data': extracted_data,
            'summary': {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'success_rate': success_rate,
                'files_processed': len(files_processed),
                'files_breakdown': files_processed
            }
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'})

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            pattern_type = request.form.get('pattern_type', 'full_name')
            search_term = request.form.get('search_term')
            
            # Extract data from PDF
            results = extract_data_from_pdf(filepath, pattern_type, search_term)
            
            # Add filename to each result for tracking
            for result in results:
                result['filename'] = filename
            
            # Store results
            extracted_data.extend(results)
            
            # Clean up
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'data': results,
                'filename': filename,
                'dashboard_url': '/dashboard'
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """Handle multiple file uploads in a single request"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files part'})
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'No selected files'})
        
        pattern_type = request.form.get('pattern_type', 'full_name')
        search_term = request.form.get('search_term')
        
        all_results = []
        processed_files = []
        errors = []
        
        for file in files:
            if file and file.filename.endswith('.pdf'):
                try:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    # Extract data from PDF
                    results = extract_data_from_pdf(filepath, pattern_type, search_term)
                    
                    # Add filename to each result for tracking
                    for result in results:
                        result['filename'] = filename
                    
                    all_results.extend(results)
                    processed_files.append({
                        'filename': filename,
                        'results_count': len(results)
                    })
                    
                    # Clean up
                    os.remove(filepath)
                    
                except Exception as e:
                    errors.append({
                        'filename': file.filename,
                        'error': str(e)
                    })
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
            else:
                errors.append({
                    'filename': file.filename,
                    'error': 'Invalid file type (only PDF files are supported)'
                })

        # Store all results
        extracted_data.extend(all_results)
        
        return jsonify({
            'success': True,
            'data': all_results,
            'processed_files': processed_files,
            'errors': errors,
            'total_files': len(files),
            'successful_files': len(processed_files),
            'failed_files': len(errors),
            'dashboard_url': '/dashboard'
        })

    except Exception as e:
        logger.error(f"Error processing multiple files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download')
def download_results():
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'results.csv')
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name='extracted_data.csv')
    return jsonify({'error': 'No results file found'}), 404

if __name__ == '__main__':
    app.run(debug=True) 
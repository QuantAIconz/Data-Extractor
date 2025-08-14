# Data-Extractor

A Python/Flask application for extracting and validating structured data (names, phone numbers, emails, etc.) from PDF files. The app supports single and multiple PDF uploads, robust validation, and provides a dashboard for data visualization.

## Features

- Extracts structured data from PDF files (names, phone numbers, emails, dates, etc.)
- Validates extracted data using advanced logic and external libraries
- Supports single and multiple PDF uploads
- Interactive dashboard for data visualization (using Plotly/Dash)
- Downloadable CSV of extracted results
- User-friendly web interface

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repo-url>
cd Data-Extractor
```

### 2. Create and Activate a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000/`.

## Usage

1. Go to the home page and upload one or more PDF files.
2. The app will extract and validate data from the PDFs.
3. View the results in a table and access the dashboard for visual analytics.
4. Download the extracted data as a CSV file if needed.

## File Structure

- `app.py` - Main Flask application
- `api/index.py` - (Optional) API endpoints
- `dashboard.py` - Dashboard logic and visualization
- `validators.py` - Data validation logic
- `templates/` - HTML templates
- `static/` - Static files (JS, CSS, images, dashboards)
- `uploads/` - Uploaded and processed files
- `requirements.txt` - Python dependencies

## Dependencies

- Flask
- PyPDF2
- phonenumbers
- email-validator
- nameparser
- pandas
- PyMuPDF
- Plotly, Dash
- Werkzeug

(See `requirements.txt` for the full list.)

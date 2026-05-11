# Smart KYC Document Processor – Mukiyassh

## Project Title

Smart KYC Document Processor – AI-Based Banking Onboarding System

---

## Project Overview

The Smart KYC Document Processor is an AI-based full-stack application designed to automate the extraction and validation of customer KYC details from different document formats. The system supports image files, PDF files, and Excel files, and converts them into a structured KYC output.

The project focuses on reducing manual work in bank onboarding by using OCR, NLP-based extraction, rule-based validation, backend API processing, and an interactive dashboard.

The system extracts important customer details such as:

- NAMES
- DATE_OF_BIRTH
- LOCATION
- ID_NUMBER

It also validates each extracted field and marks the record as either Valid or Needs Review.

---

## Problem Statement

Bank onboarding and KYC verification often require manual checking of customer documents such as Aadhaar cards, passports, PDF forms, and Excel records. This process can be slow, repetitive, and error-prone.

Manual KYC verification may lead to:

- Increased processing time
- Human errors during data entry
- Difficulty in handling bulk documents
- Inconsistent customer data format
- Delay in customer onboarding

This project solves the problem by building an AI-powered KYC document processing system that extracts, validates, and displays customer information in a structured format.

---

## Objectives

The main objectives of this project are:

- To accept multiple KYC document formats such as images, PDFs, and Excel files.
- To extract text from documents using OCR.
- To extract important KYC fields from OCR text.
- To support Aadhaar-like, passport-style, and Excel-style records.
- To validate extracted customer information.
- To provide a clean Streamlit-based user interface.
- To use FastAPI as a backend processing layer.
- To generate structured output tables and enriched KYC profiles.
- To allow users to download results in CSV, Excel, and PDF formats.

---

## Features

- User login and signup system
- Multi-page Streamlit interface
- Upload and process multiple KYC documents
- Image file support: PNG, JPG, JPEG
- PDF file support using Poppler and pdf2image
- Excel file support: XLSX and XLS
- OCR extraction using PyTesseract
- NLP-assisted and rule-based field extraction
- Aadhaar-like document extraction
- Passport-style document extraction
- Synthetic KYC data generation
- Synthetic document image generation
- FastAPI backend integration
- Validation of extracted fields
- Results dashboard with metrics
- Enriched KYC profile generation
- CSV output download
- Excel output download
- PDF profile download
- Light and dark theme support
- Interactive document preview
- OCR Preview tab
- Extracted Schema tab

---

## UI Enhancements

The Smart KYC Document Processor includes an upgraded multi-page user interface designed for a more professional and demo-ready experience.

### Login and Signup Interface

The authentication pages use a split-screen glassmorphism layout. The left side presents the project name, workflow summary, and major platform features, while the right side contains the login or signup form. This gives the project a cleaner first impression and makes the application feel closer to a real banking AI workspace.

### Home Page

The home page includes a product-style landing section with navigation buttons, platform highlights, project workflow, and technology stack badges. The workflow visually explains the complete process from login to document upload, OCR extraction, validation, and final export.

### Upload and Process Page

The Upload and Process page supports a more dashboard-like layout. Uploaded files are displayed using compact file status cards showing file name, file type, preview type, and processing status. The page also includes extraction mode selection, backend connection status, OCR preview, document preview, and extracted schema viewing.

### Results Page

The Results page presents extracted KYC records in a structured dashboard format. It includes output metrics, field coverage progress indicators, structured KYC output, validation table, enriched KYC profile view, and download options for CSV, Excel, and PDF reports.

---

## Tech Stack

| Category | Technology Used |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| OCR Engine | PyTesseract |
| NLP | spaCy |
| Data Handling | Pandas |
| Image Processing | Pillow, OpenCV |
| PDF Processing | pdf2image, Poppler |
| Database | SQLite |
| Authentication | bcrypt |
| API Communication | requests |
| Synthetic Data | Faker |
| Report Generation | ReportLab |
| UI Components | streamlit-extras, streamlit-lottie, streamlit-antd-components |

---

## Project Timeline

| Week | Work Completed |
|---|---|
| Weeks 1–2 | Data collection and Streamlit UI development |
| Weeks 3–4 | OCR processing and NLP/rule-based extraction |
| Weeks 5–6 | Synthetic data generation and synthetic document creation |
| Weeks 7–8 | FastAPI integration, validation, dashboard, and deployment preparation |

---

## System Architecture

```text
User Login / Signup
        ↓
Home Page
        ↓
Upload KYC Documents
        ↓
Streamlit Frontend
        ↓
FastAPI Backend
        ↓
OCR Processing using PyTesseract
        ↓
Field Extraction using Rules and spaCy
        ↓
Validation Module
        ↓
Structured KYC Output
        ↓
Results Dashboard
        ↓
CSV / Excel / PDF Download
```

---

## Workflow

1. User logs in or creates an account.
2. User uploads one or more KYC documents.
3. Streamlit sends the uploaded files to the FastAPI backend.
4. FastAPI receives and processes the documents.
5. Images and PDFs are processed using OCR.
6. Excel files are processed row by row using Pandas.
7. Extracted text is passed to the field extraction module.
8. Required fields are extracted into a standard schema.
9. The validation module checks the quality of extracted fields.
10. Results are displayed in the Streamlit dashboard.
11. User can download CSV, Excel, or enriched KYC profile PDF.

---

## Supported File Formats

The system supports the following file formats:

```text
PNG
JPG
JPEG
PDF
XLSX
XLS
```

---

## Extracted Output Fields

The project extracts the following fields from KYC documents:

| Field Name | Description |
|---|---|
| NAMES | Customer name extracted from the document |
| DATE_OF_BIRTH | Customer date of birth or year of birth |
| LOCATION | Address, place of birth, or place of issue |
| ID_NUMBER | Aadhaar number, passport number, or document ID |

---

## Validation Output Fields

The validation module generates the following status fields:

| Field Name | Description |
|---|---|
| NAME_STATUS | Validation status of extracted name |
| DOB_STATUS | Validation status of extracted DOB |
| LOCATION_STATUS | Validation status of extracted location |
| ID_STATUS | Validation status of extracted ID |
| OVERALL_STATUS | Final record status |
| REVIEW_REQUIRED | Indicates whether manual review is needed |

---

## Project Folder Structure

```text
Smart_KYC_Document_Processor/
│
├── KYC.py
├── UI.py
├── API.py
├── api_client.py
├── extractor.py
├── validator.py
├── auth.py
├── auth_db.py
├── SDG.py
├── doc_gen.py
├── requirements.txt
├── Testing_Report.md
├── README.md
│
├── pages/
│   ├── U_P.py
│   └── Results.py
│
├── assets/
│
├── synthetic_outputs/
│   ├── synthetic_kyc_data.csv
│   ├── synthetic_kyc_data.xlsx
│   ├── synthetic_preview_samples.txt
│   └── generated_images/
│
└── users.db
```

---

## Main Files Description

| File Name | Description |
|---|---|
| KYC.py | Main Streamlit home page |
| UI.py | Common UI components, theme, navigation, and styling |
| U_P.py | Upload and Process page |
| Results.py | Results dashboard and download page |
| API.py | FastAPI backend routes |
| api_client.py | Connects Streamlit frontend with FastAPI backend |
| extractor.py | OCR, PDF, Excel, and field extraction logic |
| validator.py | KYC field validation logic |
| auth.py | Login, signup, logout, and session handling |
| auth_db.py | SQLite user database functions |
| SDG.py | Synthetic KYC data generator |
| doc_gen.py | Synthetic document image generator |
| Testing_Report.md | Testing documentation |
| requirements.txt | Required Python packages |

---

## Installation

### 1. Clone or Download the Project

Download the project folder and open it in Visual Studio Code.

---

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:

For Windows PowerShell:

```bash
.venv\Scripts\activate
```

---

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

---

### 4. Install spaCy English Model

```bash
python -m spacy download en_core_web_sm
```

---

### 5. Install Tesseract OCR

Install Tesseract OCR and update the path in `extractor.py`.

Example path used in this project:

```text
C:\TESS\tesseract.exe
```

In `extractor.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\TESS\tesseract.exe"
```

---

### 6. Install Poppler for PDF Processing

Install Poppler and update the Poppler path in `extractor.py` and `U_P.py`.

Example path used in this project:

```text
C:\Poppler\poppler-25.07.0\Library\bin
```

In the code:

```python
POPPLER_PATH = r"C:\Poppler\poppler-25.07.0\Library\bin"
```

---

## How to Run the Project

This project uses both FastAPI and Streamlit. Run them in two separate terminals.

---

### Terminal 1: Start FastAPI Backend

```bash
uvicorn API:app --reload
```

After running this command, the backend will start at:

```text
http://127.0.0.1:8000
```

You can check API documentation at:

```text
http://127.0.0.1:8000/docs
```

---

### Terminal 2: Start Streamlit Frontend

```bash
streamlit run KYC.py
```

The Streamlit application will open in the browser.

---

## FastAPI Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | API home route |
| `/health` | GET | Checks backend health |
| `/extract` | POST | Extracts KYC fields from one file |
| `/extract-batch` | POST | Extracts KYC fields from multiple files |
| `/validate-json` | POST | Validates already extracted JSON data |

---

## Synthetic Data Generation

The project includes synthetic data generation for testing.

### Generate Synthetic KYC Data

Run:

```bash
python SDG.py
```

This creates:

```text
synthetic_outputs/synthetic_kyc_data.csv
synthetic_outputs/synthetic_kyc_data.xlsx
synthetic_outputs/synthetic_preview_samples.txt
```

---

### Generate Synthetic Document Images

Run:

```bash
python doc_gen.py
```

This creates image-based test documents inside:

```text
synthetic_outputs/generated_images/
```

Generated document types include:

- Aadhaar-like images
- Passport-like images
- Excel-style record images

---

## Output Downloads

The Results page supports the following downloads:

| Download Option | Description |
|---|---|
| Output CSV | Downloads extracted KYC output |
| Validation CSV | Downloads validation status table |
| Excel File | Downloads output and validation sheets |
| Enriched KYC Profile PDF | Downloads selected customer profile as PDF |

---

## Testing

Testing was performed for:

- Login and signup
- Image upload
- PDF upload
- Excel upload
- OCR extraction
- Aadhaar-like extraction
- Passport-style extraction
- Batch upload
- Validation
- Results dashboard
- CSV download
- Excel download
- PDF profile download

The detailed testing report is available in:

```text
Testing_Report.md
```

Overall testing result:

```text
Final Result: PASS
Project Status: Working Prototype
Completion Level: Approximately 88% to 90%
```

---

## Current Project Completion

The current completion level of the project is approximately:

```text
88% to 90%
```

Completed work includes:

- Streamlit frontend
- FastAPI backend
- OCR extraction
- PDF extraction
- Excel extraction
- Synthetic data generation
- Authentication
- Validation
- Results dashboard
- Export options
- Testing report

Remaining work includes:

- Final screenshots
- Final project report
- PPT or demo video
- Final review and submission packaging

---

## Advantages

- Reduces manual KYC data entry
- Supports multiple file formats
- Provides structured output
- Includes validation and review status
- Supports batch processing
- Provides dashboard-based review
- Includes downloadable reports
- Demonstrates full-stack AI workflow
- Suitable for portfolio and academic project presentation

---

## Limitations

- OCR accuracy depends on document quality.
- Blurred or rotated images may reduce extraction accuracy.
- Tesseract and Poppler paths are currently configured locally.
- FastAPI backend must be started separately.
- Batch upload is currently limited to 10 files per API request.
- The system is designed as a project prototype and not a production banking system.

---

## Future Enhancements

- Add manual correction option for extracted fields
- Add OCR confidence score
- Add automatic image rotation correction
- Store processed KYC records in a database
- Add admin dashboard
- Add Docker support
- Deploy frontend and backend to cloud
- Add support for more KYC document types
- Improve real-world document layout handling
- Add advanced document classification model
- Add audit logs for processed records

---

## Conclusion

The Smart KYC Document Processor is a full-stack AI-based banking onboarding prototype. It combines OCR, NLP-assisted extraction, FastAPI backend processing, Streamlit frontend dashboard, validation logic, and export features.

The system successfully processes image, PDF, and Excel-based KYC documents and converts them into a structured customer profile. It reduces manual effort in KYC processing and provides a useful demonstration of banking AI and full-stack deployment.

---

## Author

```text
Name: Mukiyassh
Project: Smart KYC Document Processor
Domain: Banking AI / OCR / NLP / Full-Stack AI Application
```
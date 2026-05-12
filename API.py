import io
import re
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from extractor import (
    extract_fields,
    extract_synthetic_fields_from_row,
    extract_text,
    normalize_excel_columns,
)

from validator import validate_kyc_record, FINAL_COLUMNS


# ---------------- FASTAPI APP CONFIG ----------------
app = FastAPI(
    title="Smart KYC Document Processor API",
    description="FastAPI backend for OCR-based KYC document extraction and validation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- FILE WRAPPER ----------------
class StreamlitLikeFile:
    """
    extractor.py expects a Streamlit uploaded file-like object with:
    - getvalue()
    - name
    - type

    This wrapper lets FastAPI UploadFile work with the same extractor.py code.
    """

    def __init__(self, file_name: str, content_type: str, file_bytes: bytes):
        self.name = file_name
        self.type = content_type or ""
        self._file_bytes = file_bytes

    def getvalue(self):
        return self._file_bytes


# ---------------- AADHAAR-SYNTH HARD FIX ----------------
def is_aadhaar_synth_context(text: str) -> bool:
    """
    Detects Aadhaar-synthetic text from either OCR text or extracted ID field.
    This must not affect passport or Excel-style records.
    """
    upper = str(text).upper()

    has_aadhaar_synth = (
        "AADHAAR / IDENTITY SAMPLE" in upper
        or "AADHAR / IDENTITY SAMPLE" in upper
        or "SYNTHETIC AADHAAR" in upper
        or "SYNTHETIC AADHAR" in upper
        or "AADHAAR-LIKE" in upper
        or "AADHAR-LIKE" in upper
        or "AADHAAR LIKE" in upper
        or "AADHAR LIKE" in upper
        or "KQINEXKXX" in upper
        or "QINEXKXX" in upper
    )

    has_passport = (
        "REPUBLIC OF INDIA" in upper
        or "UNITED ARAB EMIRATES" in upper
        or "P<" in upper
        or "SURNAME" in upper
        or "GIVEN NAME" in upper
    )

    has_excel_style = (
        "EXCEL STYLE KYC RECORD" in upper
        or "EXCEL_RECORD" in upper
        or ("FIELD" in upper and "VALUE" in upper and "DOC_TYPE" in upper)
    )

    return has_aadhaar_synth and not has_passport and not has_excel_style


def clean_aadhaar_synth_id_text(text: str) -> str:
    """
    Removes only the common Aadhaar-synth OCR junk text.
    It does NOT remove digits, so the last 4 digits remain available.

    Example:
        SYNTHETIC AADHAAR-LIKE TES) KQINEXKXX 9958
    becomes:
        9958
    """
    s = str(text)

    noise_patterns = [
        r"SYNTHETIC\s+AADHAAR[-\s]*LIKE\s+TES\)?\s*KQINEXKXX",
        r"SYNTHETIC\s+AADHAR[-\s]*LIKE\s+TES\)?\s*KQINEXKXX",
        r"SYNTHETIC\s+AADHAAR[-\s]*LIKE\s+TESH?O?K?Q?X?INEXKXX",
        r"SYNTHETIC\s+AADHAR[-\s]*LIKE\s+TESH?O?K?Q?X?INEXKXX",
        r"SYNTHETIC\s+AADHAAR[-\s]*LIKE\s+TESH?Q?K?Q?INEXKXX",
        r"SYNTHETIC\s+AADHAR[-\s]*LIKE\s+TESH?Q?K?Q?INEXKXX",
        r"SYNTHETIC\s+AADHAAR[-\s]*LIKE\s+TES\)?\s*QINEXKXX",
        r"SYNTHETIC\s+AADHAR[-\s]*LIKE\s+TES\)?\s*QINEXKXX",
    ]

    for pattern in noise_patterns:
        s = re.sub(pattern, " ", s, flags=re.IGNORECASE)

    # Remove remaining common words, but keep digits.
    s = re.sub(r"SYNTHETIC", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"AADHAAR[-\s]*LIKE", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"AADHAR[-\s]*LIKE", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"KQINEXKXX|QINEXKXX|INEXKXX", " ", s, flags=re.IGNORECASE)

    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_last4_for_aadhaar_synth(text: str):
    """
    Aadhaar-synth rule:
    - Remove common OCR noise.
    - Ignore alphabets.
    - Extract digits only.
    - Keep only the last 4 digits.
    """
    cleaned_text = clean_aadhaar_synth_id_text(text)

    groups = re.findall(r"\b\d{4}\b", cleaned_text)
    if groups:
        return groups[-1]

    digits = re.findall(r"\d", cleaned_text)
    if len(digits) >= 4:
        return "".join(digits[-4:])

    return None


def force_aadhaar_synth_schema(fields: dict, ocr_text: str) -> dict:
    """
    Fixes Aadhaar-synth document ID output.

    Required output:
        XXXX XXXX last4

    Example:
        SYNTHETIC AADHAAR-LIKE TES) KQINEXKXX 9958
        → XXXX XXXX 9958
    """
    fixed_fields = dict(fields)

    current_id_text = str(fixed_fields.get("ID_NUMBER", ""))

    combined_context = f"{ocr_text}\n{current_id_text}"

    if not is_aadhaar_synth_context(combined_context):
        return fixed_fields

    # Try full OCR first because it usually contains the visible last 4 digits.
    last4 = extract_last4_for_aadhaar_synth(ocr_text)

    # If OCR did not include the digits, try extracted ID text.
    if not last4:
        last4 = extract_last4_for_aadhaar_synth(current_id_text)

    if last4:
        fixed_fields["ID_NUMBER"] = f"XXXX XXXX {last4}"
    else:
        fixed_fields["ID_NUMBER"] = "Not Found"

    return fixed_fields


# ---------------- EXCEL-STYLE IMAGE HARD FIX ----------------
def is_excel_style_image_ocr(ocr_text: str) -> bool:
    """
    Detects synthetic Excel-style KYC record images.
    These are PNG/JPG images that look like a table, not actual .xlsx files.
    """
    upper = str(ocr_text).upper()

    return (
        "EXCEL STYLE KYC RECORD" in upper
        or ("FIELD" in upper and "VALUE" in upper and "DATE_OF_BIRTH" in upper and "ID_NUMBER" in upper)
        or "EXCEL_RECORD" in upper
    )


def normalize_date_candidate(date_text: str) -> str:
    """
    Keeps the extracted date format stable where possible.
    Accepts:
    - 1990/12/19
    - 21-06-2001
    - 22/10/1995
    """
    s = str(date_text).strip()
    s = s.replace(".", "/")

    # yyyy/mm/dd or yyyy-mm-dd
    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s)
    if m:
        yyyy, mm, dd = m.groups()
        yyyy, mm, dd = int(yyyy), int(mm), int(dd)

        if 1930 <= yyyy <= 2026 and 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{yyyy:04d}/{mm:02d}/{dd:02d}"

    # dd/mm/yyyy or dd-mm-yyyy
    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", s)
    if m:
        dd, mm, yyyy = m.groups()
        dd, mm, yyyy = int(dd), int(mm), int(yyyy)

        if 1930 <= yyyy <= 2026 and 1 <= mm <= 12 and 1 <= dd <= 31:
            original_sep = "-" if "-" in s else "/"
            return f"{dd:02d}{original_sep}{mm:02d}{original_sep}{yyyy:04d}"

    return s


def extract_dob_from_excel_style_ocr(ocr_text: str):
    """
    Fixes issue where DATE_OF_BIRTH becomes LOCATION because OCR table labels
    are read in a bad order.

    It searches for date patterns in the whole OCR text and selects the most
    likely DOB value.
    """
    raw = str(ocr_text)
    upper = raw.upper()

    # Try to capture near DATE_OF_BIRTH first.
    near_dob_patterns = [
        r"DATE[_\s-]*OF[_\s-]*BIRTH[^\d]{0,40}(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"DATE[_\s-]*OF[_\s-]*BIRTH[^\d]{0,40}(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"DOB[^\d]{0,40}(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"DOB[^\d]{0,40}(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    ]

    for pattern in near_dob_patterns:
        match = re.search(pattern, upper, flags=re.IGNORECASE)
        if match:
            return normalize_date_candidate(match.group(1))

    # General date extraction from full OCR.
    candidates = []

    candidates.extend(re.findall(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b", raw))
    candidates.extend(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", raw))

    valid_candidates = []

    for cand in candidates:
        normalized = normalize_date_candidate(cand)

        # Validate using year presence.
        years = re.findall(r"\d{4}", normalized)
        if not years:
            continue

        year = int(years[0])
        if 1930 <= year <= 2026:
            valid_candidates.append(normalized)

    if valid_candidates:
        return valid_candidates[0]

    return None


def fix_excel_style_image_schema(fields: dict, ocr_text: str) -> dict:
    """
    Fixes Excel-style image schema issues.

    Current issue:
        DATE_OF_BIRTH = LOCATION

    Correct:
        DATE_OF_BIRTH = actual date from OCR table
    """
    fixed_fields = dict(fields)

    if not is_excel_style_image_ocr(ocr_text):
        return fixed_fields

    current_dob = str(fixed_fields.get("DATE_OF_BIRTH", "")).strip().upper()

    bad_dob_values = {
        "LOCATION",
        "ID_NUMBER",
        "NAMES",
        "NAME",
        "FIELD",
        "VALUE",
        "DOC_TYPE",
        "EXCEL_RECORD",
        "NOT FOUND",
        "",
    }

    extracted_dob = extract_dob_from_excel_style_ocr(ocr_text)

    if current_dob in bad_dob_values or not re.search(r"\d", current_dob):
        if extracted_dob:
            fixed_fields["DATE_OF_BIRTH"] = extracted_dob
        else:
            fixed_fields["DATE_OF_BIRTH"] = "Not Found"

    return fixed_fields


# ---------------- HELPERS ----------------
def normalize_mode(mode: str) -> str:
    mode = str(mode or "Balanced").strip().capitalize()

    if mode not in ["Fast", "Balanced", "Accurate"]:
        return "Balanced"

    return mode


def allowed_file(file_name: str) -> bool:
    allowed_extensions = [".png", ".jpg", ".jpeg", ".pdf", ".xlsx", ".xls"]
    return any(file_name.lower().endswith(ext) for ext in allowed_extensions)


def process_excel_file(file_name: str, file_bytes: bytes) -> List[dict]:
    """
    Processes actual Excel files row-by-row.
    Excel ID values stay exact.
    Aadhaar-synth masking is not applied to Excel rows.
    """
    try:
        if file_name.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        else:
            try:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
            except Exception:
                df = pd.read_excel(io.BytesIO(file_bytes))

        df = normalize_excel_columns(df)

        results = []

        for _, row in df.iterrows():
            extracted = extract_synthetic_fields_from_row(row)
            validated = validate_kyc_record(extracted)
            results.append(validated)

        return results

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Excel processing failed: {str(e)}"
        )


def process_document_file(file: StreamlitLikeFile, mode: str) -> dict:
    """
    Processes image/PDF document files through OCR + extractor + validation.
    """
    try:
        text, preview_image = extract_text(file, mode=mode)

        fields = extract_fields(text, preview_image)

        # Fix 1: Aadhaar-synth noisy ID issue.
        fields = force_aadhaar_synth_schema(fields, text)

        # Fix 2: Excel-style image DOB issue.
        fields = fix_excel_style_image_schema(fields, text)

        # Validation after all corrections.
        validated = validate_kyc_record(fields)

        return {
            "file_name": file.name,
            "file_type": "document",
            "ocr_preview": text[:3000] if text else "",
            "extracted_schema": validated,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed for {file.name}: {str(e)}"
        )


def build_summary(results: List[dict]) -> dict:
    """
    Builds API-level dashboard summary.
    """
    if not results:
        return {
            "total_records": 0,
            "valid_records": 0,
            "needs_review": 0,
            "valid_names": 0,
            "valid_dob": 0,
            "valid_locations": 0,
            "valid_ids": 0,
        }

    df = pd.DataFrame(results)

    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = "Not Found"

    return {
        "total_records": int(len(df)),
        "valid_records": int((df["OVERALL_STATUS"] == "Valid").sum()),
        "needs_review": int((df["REVIEW_REQUIRED"] == "Yes").sum()),
        "valid_names": int((df["NAME_STATUS"] == "Valid").sum()),
        "valid_dob": int((df["DOB_STATUS"] == "Valid").sum()),
        "valid_locations": int((df["LOCATION_STATUS"] == "Valid").sum()),
        "valid_ids": int((df["ID_STATUS"] == "Valid").sum()),
    }


# ---------------- API ROUTES ----------------
@app.get("/")
def home():
    return {
        "message": "Smart KYC Document Processor API is running",
        "project": "Smart KYC Document Processor – Mukiyassh",
        "available_routes": [
            "GET /",
            "GET /health",
            "POST /extract",
            "POST /extract-batch",
            "POST /validate-json",
        ],
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Smart KYC API",
    }


@app.post("/extract")
async def extract_single_file(
    file: UploadFile = File(..., description="Upload one KYC file"),
    mode: str = "Balanced",
):
    """
    Upload one KYC file and get extracted + validated output.
    """
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use png, jpg, jpeg, pdf, xlsx, or xls."
        )

    file_bytes = await file.read()
    mode = normalize_mode(mode)

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_name = file.filename.lower()

    if file_name.endswith((".xlsx", ".xls")):
        rows = process_excel_file(file.filename, file_bytes)

        return {
            "status": "success",
            "mode": mode,
            "file_name": file.filename,
            "file_type": "excel",
            "record_count": len(rows),
            "summary": build_summary(rows),
            "results": rows,
        }

    wrapped_file = StreamlitLikeFile(
        file_name=file.filename,
        content_type=file.content_type,
        file_bytes=file_bytes,
    )

    result = process_document_file(wrapped_file, mode)

    return {
        "status": "success",
        "mode": mode,
        "file_name": file.filename,
        "file_type": "document",
        "summary": build_summary([result["extracted_schema"]]),
        "result": result,
    }


@app.post("/extract-batch")
async def extract_batch_files(
    mode: str = "Balanced",
    files: List[UploadFile] = File(..., description="Upload one or more KYC files"),
):
    """
    Upload any number of KYC files and get combined extraction + validation output.

    This version supports n files in a batch.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    mode = normalize_mode(mode)

    all_results = []
    file_level_results = []

    for uploaded_file in files:
        if uploaded_file is None or uploaded_file.filename is None or uploaded_file.filename.strip() == "":
            continue

        if not allowed_file(uploaded_file.filename):
            file_level_results.append(
                {
                    "file_name": uploaded_file.filename,
                    "status": "failed",
                    "error": "Unsupported file type. Use png, jpg, jpeg, pdf, xlsx, or xls.",
                }
            )
            continue

        file_bytes = await uploaded_file.read()

        if not file_bytes:
            file_level_results.append(
                {
                    "file_name": uploaded_file.filename,
                    "status": "failed",
                    "error": "Empty file",
                }
            )
            continue

        file_name = uploaded_file.filename.lower()

        try:
            if file_name.endswith((".xlsx", ".xls")):
                rows = process_excel_file(uploaded_file.filename, file_bytes)

                all_results.extend(rows)

                file_level_results.append(
                    {
                        "file_name": uploaded_file.filename,
                        "file_type": "excel",
                        "status": "success",
                        "record_count": len(rows),
                        "results": rows,
                    }
                )

            else:
                wrapped_file = StreamlitLikeFile(
                    file_name=uploaded_file.filename,
                    content_type=uploaded_file.content_type,
                    file_bytes=file_bytes,
                )

                result = process_document_file(wrapped_file, mode)
                extracted_schema = result["extracted_schema"]

                all_results.append(extracted_schema)

                file_level_results.append(
                    {
                        "file_name": uploaded_file.filename,
                        "file_type": "document",
                        "status": "success",
                        "ocr_preview": result["ocr_preview"],
                        "extracted_schema": extracted_schema,
                    }
                )

        except Exception as e:
            file_level_results.append(
                {
                    "file_name": uploaded_file.filename,
                    "status": "failed",
                    "error": str(e),
                }
            )

    return {
        "status": "completed",
        "mode": mode,
        "uploaded_files": len(files),
        "processed_records": len(all_results),
        "summary": build_summary(all_results),
        "files": file_level_results,
        "combined_results": all_results,
    }


@app.post("/validate-json")
async def validate_json_record(record: dict):
    """
    Send already extracted KYC JSON and get validation result.
    """
    try:
        validated = validate_kyc_record(record)

        return {
            "status": "success",
            "validated_record": validated,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )
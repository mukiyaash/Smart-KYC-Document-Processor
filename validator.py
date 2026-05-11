import re
import pandas as pd


BASE_COLUMNS = ["NAMES", "DATE_OF_BIRTH", "LOCATION", "ID_NUMBER"]

VALIDATION_COLUMNS = [
    "NAME_STATUS",
    "DOB_STATUS",
    "LOCATION_STATUS",
    "ID_STATUS",
    "OVERALL_STATUS",
    "REVIEW_REQUIRED",
]

FINAL_COLUMNS = BASE_COLUMNS + VALIDATION_COLUMNS


def is_missing(value):
    if value is None:
        return True

    value = str(value).strip()

    if value == "":
        return True

    if value.lower() in {"nan", "none", "null", "not found", "not_found"}:
        return True

    return False


def clean_text(value):
    if is_missing(value):
        return "Not Found"

    return re.sub(r"\s+", " ", str(value).strip())


def validate_name(name):
    name = clean_text(name)

    if is_missing(name):
        return "Missing"

    if len(name) < 2:
        return "Needs Review"

    if re.search(r"\d", name):
        return "Needs Review"

    bad_words = [
        "GOVERNMENT",
        "AADHAAR",
        "AADHAR",
        "PASSPORT",
        "SYNTHETIC",
        "DOCUMENT",
        "IDENTITY",
    ]

    upper = name.upper()

    if any(word in upper for word in bad_words):
        return "Needs Review"

    return "Valid"


def normalize_dob_for_check(dob):
    dob = clean_text(dob)

    if is_missing(dob):
        return None

    dob = dob.replace("-", "/").strip()

    # dd/mm/yyyy
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", dob)
    if m:
        dd, mm, yyyy = map(int, m.groups())
        if 1 <= dd <= 31 and 1 <= mm <= 12 and 1930 <= yyyy <= 2026:
            return f"{dd:02d}/{mm:02d}/{yyyy:04d}"

    # yyyy/mm/dd
    m = re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", dob)
    if m:
        yyyy, mm, dd = map(int, m.groups())
        if 1 <= dd <= 31 and 1 <= mm <= 12 and 1930 <= yyyy <= 2026:
            return f"{dd:02d}/{mm:02d}/{yyyy:04d}"

    # 16 Mar 1999 / 16 March 1999
    try:
        dt = pd.to_datetime(dob, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            year = int(dt.year)
            if 1930 <= year <= 2026:
                return dt.strftime("%d/%m/%Y")
    except Exception:
        pass

    # year only fallback
    if re.fullmatch(r"\d{4}", dob):
        year = int(dob)
        if 1930 <= year <= 2026:
            return dob

    return None


def validate_dob(dob):
    if is_missing(dob):
        return "Missing"

    parsed = normalize_dob_for_check(dob)

    if parsed:
        return "Valid"

    return "Needs Review"


def validate_location(location):
    location = clean_text(location)

    if is_missing(location):
        return "Missing"

    if len(location) < 3:
        return "Needs Review"

    if re.search(r"\d", location):
        return "Needs Review"

    bad_values = {
        "PASSPORT",
        "AADHAAR",
        "AADHAR",
        "GOVERNMENT",
        "INDIA",
        "INDIAN",
        "NATIONALITY",
        "DOCUMENT",
        "SYNTHETIC",
    }

    upper = location.upper().strip()

    if upper in bad_values:
        return "Needs Review"

    return "Valid"


def validate_id_number(id_number):
    id_number = clean_text(id_number)

    if is_missing(id_number):
        return "Missing"

    upper = id_number.upper().strip()

    # Aadhaar-synth masked format: XXXX XXXX 1234
    if re.fullmatch(r"X{4}\s+X{4}\s+\d{4}", upper):
        return "Valid"

    # Normal Aadhaar format: 1234 5678 9012
    if re.fullmatch(r"\d{4}\s*\d{4}\s*\d{4}", upper):
        return "Valid"

    # Passport format: Z4676026 / Y34867890
    if re.fullmatch(r"[A-Z][0-9]{7,9}", upper):
        return "Valid"

    # Excel or generic alphanumeric ID
    if re.fullmatch(r"[A-Z0-9\-_/]{5,20}", upper):
        return "Valid"

    return "Needs Review"


def validate_kyc_record(record):
    """
    Adds validation status columns to one extracted KYC record.
    """

    fixed = {}

    for col in BASE_COLUMNS:
        fixed[col] = clean_text(record.get(col, "Not Found"))

    fixed["NAME_STATUS"] = validate_name(fixed["NAMES"])
    fixed["DOB_STATUS"] = validate_dob(fixed["DATE_OF_BIRTH"])
    fixed["LOCATION_STATUS"] = validate_location(fixed["LOCATION"])
    fixed["ID_STATUS"] = validate_id_number(fixed["ID_NUMBER"])

    statuses = [
        fixed["NAME_STATUS"],
        fixed["DOB_STATUS"],
        fixed["LOCATION_STATUS"],
        fixed["ID_STATUS"],
    ]

    if all(status == "Valid" for status in statuses):
        fixed["OVERALL_STATUS"] = "Valid"
        fixed["REVIEW_REQUIRED"] = "No"
    else:
        fixed["OVERALL_STATUS"] = "Needs Review"
        fixed["REVIEW_REQUIRED"] = "Yes"

    return fixed


def validate_dataframe(df):
    """
    Applies validation to an entire dataframe.
    """

    if df is None or df.empty:
        return pd.DataFrame(columns=FINAL_COLUMNS)

    rows = []

    for _, row in df.iterrows():
        record = row.to_dict()
        rows.append(validate_kyc_record(record))

    return pd.DataFrame(rows, columns=FINAL_COLUMNS)
import os
import random
import string
from datetime import datetime
from faker import Faker
import pandas as pd

# ---------------- CONFIG ----------------
fake = Faker("en_IN")
random.seed()
Faker.seed()

OUTPUT_DIR = "synthetic_outputs"
CSV_FILE = "synthetic_kyc_data.csv"
EXCEL_FILE = "synthetic_kyc_data.xlsx"
TEXT_FILE = "synthetic_preview_samples.txt"

NUM_RECORDS = 200

DOC_TYPES = ["AADHAAR", "PASSPORT", "EXCEL_RECORD"]

NAME_LABELS = ["Name", "Names", "Full Name", "Holder Name", "Given Name"]
DOB_LABELS = ["DOB", "Date of Birth", "Birth Date", "Year of Birth"]
LOCATION_LABELS = ["Location", "Place of Birth", "Place of Issue", "Address Location"]
ID_LABELS = ["ID Number", "Passport Number", "Aadhaar Number", "Document ID"]

INDIAN_STATES = [
    "Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh", "Telangana",
    "Maharashtra", "Delhi", "West Bengal", "Gujarat", "Rajasthan",
    "Uttar Pradesh", "Madhya Pradesh", "Bihar", "Odisha", "Punjab",
    "Haryana", "Himachal Pradesh", "Chandigarh"
]

UAE_LOCATIONS = ["Sharjah", "Dubai", "Abu Dhabi", "Ajman", "Al Ain"]

# ---------------- HELPERS ----------------
def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def random_doc_type() -> str:
    return random.choice(DOC_TYPES)

def random_name() -> str:
    name_styles = [
        fake.name,
        lambda: f"{fake.first_name()} {fake.last_name()}",
        lambda: f"{fake.first_name()} {fake.first_name()} {fake.last_name()}",
        lambda: f"{fake.first_name()} {random.choice(string.ascii_uppercase)}",
        lambda: f"{fake.first_name()} {random.choice(string.ascii_uppercase)} {fake.last_name()}",
    ]
    return random.choice(name_styles)()

def random_dob_date():
    return fake.date_of_birth(minimum_age=18, maximum_age=60)

def random_dob_format(dob) -> str:
    formats = [
        dob.strftime("%d/%m/%Y"),
        dob.strftime("%d-%m-%Y"),
        dob.strftime("%Y/%m/%d"),
        dob.strftime("%d %b %Y"),
    ]
    return random.choice(formats)

def random_location(doc_type: str) -> str:
    if doc_type == "PASSPORT":
        if random.choice([True, False]):
            return random.choice(UAE_LOCATIONS).upper()
        return fake.city().upper()
    if random.choice([True, False]):
        return random.choice(INDIAN_STATES).upper()
    return fake.city().upper()

def random_passport_id() -> str:
    return random.choice(string.ascii_uppercase) + "".join(random.choices(string.digits, k=7))

def random_aadhaar_id(masked: bool = False) -> str:
    last_block = "".join(random.choices(string.digits, k=4))
    if masked:
        return f"XXXX XXXX {last_block}"
    first = "".join(random.choices(string.digits, k=4))
    second = "".join(random.choices(string.digits, k=4))
    return f"{first} {second} {last_block}"

def random_id(doc_type: str) -> str:
    if doc_type == "AADHAAR":
        return random_aadhaar_id(masked=random.choice([True, False]))
    if doc_type == "PASSPORT":
        return random_passport_id()
    return random.choice([
        random_passport_id(),
        random_aadhaar_id(masked=False),
        random_aadhaar_id(masked=True)
    ])

def random_case_variant(text: str) -> str:
    variants = [
        text,
        text.upper(),
        text.title()
    ]
    return random.choice(variants)

def random_labels() -> dict:
    return {
        "NAME_LABEL": random.choice(NAME_LABELS),
        "DOB_LABEL": random.choice(DOB_LABELS),
        "LOCATION_LABEL": random.choice(LOCATION_LABELS),
        "ID_LABEL": random.choice(ID_LABELS),
    }

def build_preview_block(record: dict) -> str:
    return (
        f"{record['NAME_LABEL']}: {record['NAMES']}\n"
        f"{record['DOB_LABEL']}: {record['DATE_OF_BIRTH']}\n"
        f"{record['LOCATION_LABEL']}: {record['LOCATION']}\n"
        f"{record['ID_LABEL']}: {record['ID_NUMBER']}\n"
        f"DOC_TYPE: {record['DOC_TYPE']}\n"
        f"{'-' * 50}\n"
    )

# ---------------- CORE GENERATION ----------------
def generate_record() -> dict:
    doc_type = random_doc_type()
    dob = random_dob_date()
    labels = random_labels()

    record = {
        "NAMES": random_case_variant(random_name()),
        "DATE_OF_BIRTH": random_dob_format(dob),
        "LOCATION": random_case_variant(random_location(doc_type)),
        "ID_NUMBER": random_id(doc_type),
        "DOC_TYPE": doc_type,
        "NAME_LABEL": labels["NAME_LABEL"],
        "DOB_LABEL": labels["DOB_LABEL"],
        "LOCATION_LABEL": labels["LOCATION_LABEL"],
        "ID_LABEL": labels["ID_LABEL"],
    }
    return record

def generate_dataset(num_records: int) -> pd.DataFrame:
    records = [generate_record() for _ in range(num_records)]
    return pd.DataFrame(records)

# ---------------- SAVE ----------------
def save_dataset(df: pd.DataFrame) -> tuple[str, str, str]:
    csv_path = os.path.join(OUTPUT_DIR, CSV_FILE)
    excel_path = os.path.join(OUTPUT_DIR, EXCEL_FILE)
    text_path = os.path.join(OUTPUT_DIR, TEXT_FILE)

    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False, engine="openpyxl")

    with open(text_path, "w", encoding="utf-8") as f:
        for _, row in df.head(25).iterrows():
            f.write(build_preview_block(row.to_dict()))

    return csv_path, excel_path, text_path

# ---------------- MAIN ----------------
def main():
    ensure_output_dir()

    print("Generating synthetic KYC data...")
    df = generate_dataset(NUM_RECORDS)

    csv_path, excel_path, text_path = save_dataset(df)

    print("\nSynthetic data generation completed successfully.")
    print(f"Total records generated: {len(df)}")
    print(f"CSV saved at   : {csv_path}")
    print(f"Excel saved at : {excel_path}")
    print(f"Preview saved at: {text_path}")

    print("\nSample output:\n")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
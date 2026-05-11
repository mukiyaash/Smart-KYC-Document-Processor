import os
import textwrap
import random
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIG ----------------
INPUT_XLSX = os.path.join("synthetic_outputs", "synthetic_kyc_data.xlsx")
INPUT_CSV = os.path.join("synthetic_outputs", "synthetic_kyc_data.csv")

OUTPUT_DIR = os.path.join("synthetic_outputs", "generated_images")
AADHAAR_DIR = os.path.join(OUTPUT_DIR, "aadhaar_like")
PASSPORT_DIR = os.path.join(OUTPUT_DIR, "passport_like")
EXCEL_DIR = os.path.join(OUTPUT_DIR, "excel_like")

IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 700
BG_COLOR = "white"
TEXT_COLOR = "black"
SEED = 42

random.seed(SEED)

# ---------------- HELPERS ----------------
def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(AADHAAR_DIR, exist_ok=True)
    os.makedirs(PASSPORT_DIR, exist_ok=True)
    os.makedirs(EXCEL_DIR, exist_ok=True)

def load_dataset():
    if os.path.exists(INPUT_XLSX):
        return pd.read_excel(INPUT_XLSX, engine="openpyxl")
    if os.path.exists(INPUT_CSV):
        return pd.read_csv(INPUT_CSV)
    raise FileNotFoundError(
        "No synthetic dataset found. Make sure synthetic_outputs/synthetic_kyc_data.xlsx "
        "or synthetic_outputs/synthetic_kyc_data.csv exists."
    )

def get_font(size=32, bold=False):
    font_candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def draw_wrapped_text(draw, text, x, y, font, max_width, fill="black", line_spacing=10):
    lines = []
    for paragraph in str(text).split("\n"):
        wrapped = textwrap.wrap(paragraph, width=40)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)

    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, current_y), line, font=font)
        line_height = bbox[3] - bbox[1]
        current_y += line_height + line_spacing
    return current_y

def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

# ---------------- IMAGE GENERATORS ----------------
def create_aadhaar_like_image(row, output_path):
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    title_font = get_font(40, bold=True)
    header_font = get_font(28, bold=True)
    body_font = get_font(30, bold=False)
    small_font = get_font(24, bold=False)

    # Header
    draw.rectangle([(20, 20), (1180, 120)], outline="black", width=3)
    draw.text((40, 35), "Government of India", font=title_font, fill="black")
    draw.text((40, 80), "AADHAAR / IDENTITY SAMPLE", font=header_font, fill="black")

    # Left profile area
    draw.rectangle([(40, 160), (260, 430)], outline="black", width=2)
    draw.text((90, 275), "PHOTO", font=header_font, fill="gray")

    # Text block
    x0 = 320
    y = 180
    draw.text((x0, y), safe_text(row["NAME_LABEL"]) + ":", font=header_font, fill=TEXT_COLOR)
    y += 50
    draw.text((x0, y), safe_text(row["NAMES"]), font=body_font, fill=TEXT_COLOR)

    y += 80
    draw.text((x0, y), safe_text(row["DOB_LABEL"]) + ":", font=header_font, fill=TEXT_COLOR)
    y += 50
    draw.text((x0, y), safe_text(row["DATE_OF_BIRTH"]), font=body_font, fill=TEXT_COLOR)

    y += 80
    draw.text((x0, y), safe_text(row["LOCATION_LABEL"]) + ":", font=header_font, fill=TEXT_COLOR)
    y += 50
    draw.text((x0, y), safe_text(row["LOCATION"]), font=body_font, fill=TEXT_COLOR)

    y += 80
    draw.text((x0, y), safe_text(row["ID_LABEL"]) + ":", font=header_font, fill=TEXT_COLOR)
    y += 50
    draw.text((x0, y), safe_text(row["ID_NUMBER"]), font=body_font, fill=TEXT_COLOR)

    # Footer
    draw.line((40, 600, 1160, 600), fill="black", width=2)
    draw.text((40, 620), "Synthetic Aadhaar-like test document", font=small_font, fill="gray")

    img.save(output_path)

def create_passport_like_image(row, output_path):
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=(245, 245, 250))
    draw = ImageDraw.Draw(img)

    title_font = get_font(42, bold=True)
    header_font = get_font(28, bold=True)
    body_font = get_font(30, bold=False)
    small_font = get_font(22, bold=False)

    # Outer border
    draw.rectangle([(20, 20), (1180, 680)], outline="black", width=3)

    # Header
    draw.text((40, 35), "REPUBLIC OF INDIA", font=title_font, fill="black")
    draw.text((40, 90), "PASSPORT / TEST SAMPLE", font=header_font, fill="black")

    # Photo box
    draw.rectangle([(850, 140), (1090, 430)], outline="black", width=2)
    draw.text((925, 270), "PHOTO", font=header_font, fill="gray")

    # Main fields
    left_x = 50
    y = 160

    fields = [
        ("Surname", safe_text(row["NAMES"]).split()[-1] if safe_text(row["NAMES"]) else ""),
        ("Given Name", " ".join(safe_text(row["NAMES"]).split()[:-1]) if len(safe_text(row["NAMES"]).split()) > 1 else safe_text(row["NAMES"])),
        ("Nationality", "INDIAN"),
        ("Date of Birth", safe_text(row["DATE_OF_BIRTH"])),
        ("Place of Birth", safe_text(row["LOCATION"])),
        ("Passport Number", safe_text(row["ID_NUMBER"])),
    ]

    for label, value in fields:
        draw.text((left_x, y), f"{label}:", font=header_font, fill=TEXT_COLOR)
        draw.text((320, y), value, font=body_font, fill=TEXT_COLOR)
        y += 70

    # Fake MRZ block
    mrz_y = 540
    draw.rectangle([(40, mrz_y), (1160, 650)], outline="black", width=2)
    surname = safe_text(row["NAMES"]).upper().replace(" ", "<")
    passport_no = safe_text(row["ID_NUMBER"]).upper().replace(" ", "")
    mrz_1 = f"P<IND<{surname}".ljust(44, "<")[:44]
    mrz_2 = f"{passport_no}".ljust(44, "<")[:44]

    draw.text((60, mrz_y + 20), mrz_1, font=get_font(30, bold=False), fill="black")
    draw.text((60, mrz_y + 60), mrz_2, font=get_font(30, bold=False), fill="black")

    draw.text((850, 100), "Type P", font=small_font, fill="gray")

    img.save(output_path)

def create_excel_like_image(row, output_path):
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color="white")
    draw = ImageDraw.Draw(img)

    title_font = get_font(36, bold=True)
    header_font = get_font(26, bold=True)
    body_font = get_font(24, bold=False)

    draw.text((40, 30), "EXCEL STYLE KYC RECORD", font=title_font, fill="black")

    table_x = 40
    table_y = 120
    col1 = 320
    col2 = 780
    row_h = 80

    rows = [
        ("NAMES", safe_text(row["NAMES"])),
        ("DATE_OF_BIRTH", safe_text(row["DATE_OF_BIRTH"])),
        ("LOCATION", safe_text(row["LOCATION"])),
        ("ID_NUMBER", safe_text(row["ID_NUMBER"])),
        ("DOC_TYPE", safe_text(row["DOC_TYPE"])),
    ]

    # header row
    draw.rectangle([(table_x, table_y), (table_x + col1, table_y + row_h)], outline="black", width=2)
    draw.rectangle([(table_x + col1, table_y), (table_x + col1 + col2, table_y + row_h)], outline="black", width=2)
    draw.text((table_x + 20, table_y + 20), "FIELD", font=header_font, fill="black")
    draw.text((table_x + col1 + 20, table_y + 20), "VALUE", font=header_font, fill="black")

    current_y = table_y + row_h
    for field, value in rows:
        draw.rectangle([(table_x, current_y), (table_x + col1, current_y + row_h)], outline="black", width=2)
        draw.rectangle([(table_x + col1, current_y), (table_x + col1 + col2, current_y + row_h)], outline="black", width=2)
        draw.text((table_x + 20, current_y + 20), field, font=body_font, fill="black")
        draw.text((table_x + col1 + 20, current_y + 20), value[:45], font=body_font, fill="black")
        current_y += row_h

    img.save(output_path)

# ---------------- MAIN PIPELINE ----------------
def generate_document_from_row(row, index):
    doc_type = safe_text(row.get("DOC_TYPE", "")).upper()

    if doc_type == "AADHAAR":
        output_path = os.path.join(AADHAAR_DIR, f"aadhaar_like_{index+1}.png")
        create_aadhaar_like_image(row, output_path)
        return output_path

    if doc_type == "PASSPORT":
        output_path = os.path.join(PASSPORT_DIR, f"passport_like_{index+1}.png")
        create_passport_like_image(row, output_path)
        return output_path

    output_path = os.path.join(EXCEL_DIR, f"excel_like_{index+1}.png")
    create_excel_like_image(row, output_path)
    return output_path

def main():
    ensure_dirs()
    df = load_dataset()

    generated_files = []

    for index, row in df.iterrows():
        output_file = generate_document_from_row(row, index)
        generated_files.append(output_file)

    print("Synthetic document generation completed.")
    print(f"Total images generated: {len(generated_files)}")
    print(f"Output folder: {OUTPUT_DIR}")
    print("\nSample generated files:")
    for file_path in generated_files[:10]:
        print(file_path)

if __name__ == "__main__":
    main()
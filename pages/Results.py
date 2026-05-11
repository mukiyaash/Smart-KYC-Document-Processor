import io
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_extras.let_it_rain import rain
from UI import (
    init_theme,
    inject_base_css,
    load_lottie_url,
    notification_bar,
    render_lottie,
    render_top_nav,
    build_sidebar,
    render_progress_card,
    render_empty_state,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from auth import require_login
from validator import validate_dataframe, FINAL_COLUMNS

from UI import (
    init_theme,
    inject_base_css,
    load_lottie_url,
    notification_bar,
    render_lottie,
    render_top_nav,
    build_sidebar,
)

st.set_page_config(page_title="Results", layout="wide", initial_sidebar_state="expanded")

init_theme()
inject_base_css(show_sidebar=True)
require_login()

render_top_nav("Results")
build_sidebar("results")
notification_bar("Review the structured KYC output, validation status, enriched profile, and download results.")


# ---------------- FINAL AADHAAR-SYNTH ID CLEANER ----------------
def clean_aadhaar_synth_id_number(value):
    raw = str(value).strip()
    upper = raw.upper()

    if raw.lower() in {"nan", "none", "null", ""}:
        return "Not Found"

    already_masked = re.search(r"\bX{4}\s+X{4}\s+\d{4}\b", upper)
    if already_masked:
        digits = re.findall(r"\d", already_masked.group(0))
        if len(digits) >= 4:
            return f"XXXX XXXX {''.join(digits[-4:])}"

    aadhaar_synth_trigger = (
        "SYNTHETIC AADHAAR" in upper
        or "AADHAAR-LIKE" in upper
        or "AADHAR-LIKE" in upper
        or "AADHAAR LIKE" in upper
        or "AADHAR LIKE" in upper
        or "KQINEXKXX" in upper
        or "QINEXKXX" in upper
    )

    if aadhaar_synth_trigger:
        digits = re.findall(r"\d", raw)

        if len(digits) >= 4:
            return f"XXXX XXXX {''.join(digits[-4:])}"

        return "Not Found"

    return raw


def clean_results_dataframe(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=FINAL_COLUMNS)

    fixed_df = df.copy()

    base_cols = ["NAMES", "DATE_OF_BIRTH", "LOCATION", "ID_NUMBER"]

    for col in base_cols:
        if col not in fixed_df.columns:
            fixed_df[col] = "Not Found"

    fixed_df["ID_NUMBER"] = fixed_df["ID_NUMBER"].apply(clean_aadhaar_synth_id_number)

    fixed_df = validate_dataframe(fixed_df)

    return fixed_df[FINAL_COLUMNS]


def render_metric(label, value):
    st.markdown(
        f"""
        <div class="metric-chip">
            <div class="metric-label">{label}</div>
            <div class="metric-num">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_value(value):
    value = str(value).strip()

    if value.lower() in {"", "nan", "none", "null"}:
        return "Not Found"

    return value


def get_profile_badge(status):
    status = str(status).strip()

    if status == "Valid":
        return "✅ Valid KYC Profile"

    return "⚠️ Needs Manual Review"


def get_review_note(review_required):
    review_required = str(review_required).strip()

    if review_required == "No":
        return "This record is export-ready and can be used for customer onboarding review."

    return "This record contains missing or uncertain fields and should be checked manually before approval."


def generate_enriched_profile_pdf(profile_row, profile_index):
    """
    Generates a PDF report for the selected enriched KYC profile.
    Returns PDF bytes.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "KYCProfileTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=26,
        spaceAfter=12,
        textColor=colors.HexColor("#0f172a"),
    )

    section_style = ParagraphStyle(
        "KYCSectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor("#1e293b"),
    )

    normal_style = ParagraphStyle(
        "KYCNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#334155"),
    )

    small_style = ParagraphStyle(
        "KYCSmall",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748b"),
    )

    name = safe_value(profile_row.get("NAMES", "Not Found"))
    dob = safe_value(profile_row.get("DATE_OF_BIRTH", "Not Found"))
    location = safe_value(profile_row.get("LOCATION", "Not Found"))
    id_number = safe_value(profile_row.get("ID_NUMBER", "Not Found"))

    name_status = safe_value(profile_row.get("NAME_STATUS", "Missing"))
    dob_status = safe_value(profile_row.get("DOB_STATUS", "Missing"))
    location_status = safe_value(profile_row.get("LOCATION_STATUS", "Missing"))
    id_status = safe_value(profile_row.get("ID_STATUS", "Missing"))
    overall_status = safe_value(profile_row.get("OVERALL_STATUS", "Needs Review"))
    review_required = safe_value(profile_row.get("REVIEW_REQUIRED", "Yes"))

    profile_badge = get_profile_badge(overall_status)
    review_note = get_review_note(review_required)

    elements = []

    elements.append(Paragraph("Enriched KYC Profile", title_style))
    elements.append(
        Paragraph(
            "Smart KYC Document Processor - AI-enabled customer onboarding profile",
            small_style,
        )
    )
    elements.append(Spacer(1, 0.2 * inch))

    summary_data = [
        ["Profile ID", f"KYC-{profile_index + 1:04d}"],
        ["Customer Name", name],
        ["KYC Status", overall_status],
        ["Review Required", review_required],
        ["Profile Label", profile_badge],
    ]

    summary_table = Table(summary_data, colWidths=[1.8 * inch, 4.7 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(summary_table)
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph("Extracted KYC Details", section_style))

    details_data = [
        ["Field", "Extracted Value", "Validation Status"],
        ["Customer Name", name, name_status],
        ["Date of Birth", dob, dob_status],
        ["Location / Address", location, location_status],
        ["ID Number", id_number, id_status],
    ]

    details_table = Table(details_data, colWidths=[1.7 * inch, 3.0 * inch, 1.8 * inch])
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(details_table)
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph("Banking AI Use Case", section_style))
    elements.append(
        Paragraph(
            "This enriched profile converts uploaded KYC documents into structured customer onboarding data. "
            "It supports document review by reducing manual data entry and highlighting records that require manual verification before approval.",
            normal_style,
        )
    )

    elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("Review Decision", section_style))
    elements.append(Paragraph(review_note, normal_style))

    elements.append(Spacer(1, 0.3 * inch))

    elements.append(
        Paragraph(
            "Generated by Smart KYC Document Processor. This profile is intended for project demonstration and review workflow purposes.",
            small_style,
        )
    )

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def render_enriched_profile(profile_row, profile_index):
    name = safe_value(profile_row.get("NAMES", "Not Found"))
    dob = safe_value(profile_row.get("DATE_OF_BIRTH", "Not Found"))
    location = safe_value(profile_row.get("LOCATION", "Not Found"))
    id_number = safe_value(profile_row.get("ID_NUMBER", "Not Found"))

    name_status = safe_value(profile_row.get("NAME_STATUS", "Missing"))
    dob_status = safe_value(profile_row.get("DOB_STATUS", "Missing"))
    location_status = safe_value(profile_row.get("LOCATION_STATUS", "Missing"))
    id_status = safe_value(profile_row.get("ID_STATUS", "Missing"))
    overall_status = safe_value(profile_row.get("OVERALL_STATUS", "Needs Review"))
    review_required = safe_value(profile_row.get("REVIEW_REQUIRED", "Yes"))

    profile_badge = get_profile_badge(overall_status)
    review_note = get_review_note(review_required)

    st.markdown("<div class='section-head'>Enriched KYC Profile</div>", unsafe_allow_html=True)

    top_a, top_b = st.columns([1.2, 0.8], gap="large")

    with top_a:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="pill">🏦 AI-Enriched Customer Profile</div>
                <div class="page-title" style="font-size:2rem;">{name}</div>
                <div class="page-sub">
                    This profile is generated from extracted KYC document fields and validation results.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_b:
        status_color = "rgba(34,197,94,0.14)" if overall_status == "Valid" else "rgba(245,158,11,0.16)"
        st.markdown(
            f"""
            <div class="glass-card" style="min-height:185px;background:{status_color};">
                <div style="font-size:1.15rem;font-weight:800;margin-bottom:0.5rem;">{profile_badge}</div>
                <div class="small-note" style="line-height:1.8;">
                    <b>Record ID:</b> KYC-{profile_index + 1:04d}<br>
                    <b>Overall Status:</b> {overall_status}<br>
                    <b>Review Required:</b> {review_required}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="large")

    profile_items = [
        ("👤 Customer Name", name, name_status),
        ("🎂 Date of Birth", dob, dob_status),
        ("📍 Location / Address", location, location_status),
        ("🪪 ID Number", id_number, id_status),
    ]

    for col, (label, value, status) in zip([c1, c2, c3, c4], profile_items):
        with col:
            st.markdown(
                f"""
                <div class="glass-card" style="min-height:155px;">
                    <div style="font-size:0.95rem;font-weight:800;margin-bottom:0.45rem;">{label}</div>
                    <div style="font-size:1.12rem;font-weight:800;margin-bottom:0.4rem;">{value}</div>
                    <div class="small-note">Status: <b>{status}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    s1, s2 = st.columns([1, 1], gap="large")

    with s1:
        st.markdown(
            """
            <div class="glass-card">
                <div style="font-size:1.08rem;font-weight:800;margin-bottom:0.45rem;">📌 Banking AI Use Case</div>
                <div class="small-note" style="line-height:1.8;">
                    This enriched profile converts uploaded KYC documents into structured customer onboarding data.
                    It helps reduce manual data entry and highlights records that need review before approval.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div style="font-size:1.08rem;font-weight:800;margin-bottom:0.45rem;">🧾 Review Decision</div>
                <div class="small-note" style="line-height:1.8;">
                    {review_note}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    pdf_bytes = generate_enriched_profile_pdf(profile_row, profile_index)

    file_safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    if not file_safe_name or file_safe_name == "Not_Found":
        file_safe_name = f"KYC_{profile_index + 1:04d}"

    st.download_button(
        "⬇️ Download Enriched KYC Profile PDF",
        data=pdf_bytes,
        file_name=f"enriched_kyc_profile_{file_safe_name}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key=f"download_enriched_profile_pdf_{profile_index}",
    )


# ---------------- SESSION STATE ----------------
if "kyc_results_df" not in st.session_state:
    st.session_state.kyc_results_df = pd.DataFrame(columns=FINAL_COLUMNS)

if "kyc_processed" not in st.session_state:
    st.session_state.kyc_processed = False

if "kyc_uploaded_count" not in st.session_state:
    st.session_state.kyc_uploaded_count = 0


df = clean_results_dataframe(st.session_state.kyc_results_df.copy())
st.session_state.kyc_results_df = df.copy()


# ---------------- TABLE VIEWS ----------------
OUTPUT_COLUMNS = [
    "NAMES",
    "DATE_OF_BIRTH",
    "LOCATION",
    "ID_NUMBER",
]

VALIDATION_COLUMNS_DISPLAY = [
    "NAME_STATUS",
    "DOB_STATUS",
    "LOCATION_STATUS",
    "ID_STATUS",
    "OVERALL_STATUS",
    "REVIEW_REQUIRED",
]


# ---------------- PAGE HERO ----------------
top_left, top_right = st.columns([1.25, 0.95], gap="large")

with top_left:
    st.markdown(
        """
        <div class="hero-card">
            <div class="page-title" style="font-size:2.2rem;">Results</div>
            <div class="page-sub">
                Review extracted KYC output, validation status, and AI-enriched customer profile.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    res_anim = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_kdx6cani.json")
    render_lottie(res_anim, height=250, key="results_page_anim")

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)


# ---------------- EMPTY STATE ----------------
if df.empty:
    render_empty_state(
        "No processed KYC records yet",
        "Upload documents from the Upload & Process page to generate structured KYC profiles.",
        icon="📊"
    )

    if st.button("⬅️ Go to Upload & Process", use_container_width=True, key="back_to_upload_empty"):
        st.switch_page("pages/U_P.py")


# ---------------- RESULTS ----------------
else:
    names_count = int((df["NAME_STATUS"] == "Valid").sum())
    dob_count = int((df["DOB_STATUS"] == "Valid").sum())
    location_count = int((df["LOCATION_STATUS"] == "Valid").sum())
    id_count = int((df["ID_STATUS"] == "Valid").sum())

    valid_count = int((df["OVERALL_STATUS"] == "Valid").sum())
    review_count = int((df["REVIEW_REQUIRED"] == "Yes").sum())

    # ---------------- KYC OUTPUT METRICS ----------------
    st.markdown("<div class='section-head'>KYC Output Metrics</div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4, gap="large")

    with k1:
        render_metric("👤 Names", names_count)

    with k2:
        render_metric("🎂 DOB", dob_count)

    with k3:
        render_metric("📍 Location", location_count)

    with k4:
        render_metric("🪪 ID Number", id_count)

    st.markdown("<div class='section-head'>Field Coverage</div>", unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns(4, gap="large")

    with p1:
        render_progress_card("Names Coverage", names_count, len(df))

    with p2:
        render_progress_card("DOB Coverage", dob_count, len(df))

    with p3:
        render_progress_card("Location Coverage", location_count, len(df))

    with p4:
        render_progress_card("ID Coverage", id_count, len(df))
    # ---------------- MAIN OUTPUT TABLE ----------------
    st.markdown("<div class='section-head'>Structured KYC Output</div>", unsafe_allow_html=True)

    output_df = df[OUTPUT_COLUMNS].copy()
    st.dataframe(output_df, use_container_width=True, hide_index=True)

    # ---------------- ENRICHED KYC PROFILE ----------------
    profile_options = []

    for idx, row in df.iterrows():
        customer_name = safe_value(row.get("NAMES", "Not Found"))
        id_value = safe_value(row.get("ID_NUMBER", "Not Found"))
        profile_options.append(f"KYC-{idx + 1:04d} | {customer_name} | {id_value}")

    selected_profile_label = st.selectbox(
        "Select record to view enriched KYC profile",
        profile_options,
        key="enriched_profile_selector",
    )

    selected_profile_index = profile_options.index(selected_profile_label)
    selected_profile_row = df.iloc[selected_profile_index].to_dict()

    render_enriched_profile(selected_profile_row, selected_profile_index)

    # ---------------- VALIDATION METRICS ----------------
    st.markdown("<div class='section-head'>Validation Metrics</div>", unsafe_allow_html=True)

    v1, v2 = st.columns(2, gap="large")

    with v1:
        render_metric("✅ Valid", valid_count)

    with v2:
        render_metric("⚠️ Review", review_count)

    # ---------------- SEPARATE VALIDATION TABLE ----------------
    st.markdown("<div class='section-head'>Validation Table</div>", unsafe_allow_html=True)

    validation_df = df[VALIDATION_COLUMNS_DISPLAY].copy()
    st.dataframe(validation_df, use_container_width=True, hide_index=True)

    # ---------------- VALIDATION SUMMARY ----------------
    st.markdown("<div class='section-head'>Validation Summary</div>", unsafe_allow_html=True)

    valid_df = df[df["OVERALL_STATUS"] == "Valid"].copy()
    review_df = df[df["REVIEW_REQUIRED"] == "Yes"].copy()

    valid_output_df = valid_df[OUTPUT_COLUMNS].copy()
    review_validation_df = review_df[VALIDATION_COLUMNS_DISPLAY].copy()

    s1, s2 = st.columns(2, gap="large")

    with s1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div style="font-size:1.1rem;font-weight:800;">✅ Export Ready Records</div>
                <div class="small-note" style="margin-top:0.4rem;">
                    {len(valid_df)} records have all required fields marked as Valid.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div style="font-size:1.1rem;font-weight:800;">⚠️ Records Needing Review</div>
                <div class="small-note" style="margin-top:0.4rem;">
                    {len(review_df)} records need manual checking before final use.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not valid_output_df.empty:
        with st.expander("✅ View export-ready output records"):
            st.dataframe(valid_output_df, use_container_width=True, hide_index=True)

    if not review_validation_df.empty:
        with st.expander("⚠️ View validation issues"):
            st.dataframe(review_validation_df, use_container_width=True, hide_index=True)

    # ---------------- DOWNLOADS ----------------
    st.markdown("<div class='section-head'>Downloads</div>", unsafe_allow_html=True)

    csv_bytes = output_df.to_csv(index=False).encode("utf-8")
    validation_csv_bytes = validation_df.to_csv(index=False).encode("utf-8")

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        output_df.to_excel(writer, index=False, sheet_name="KYC_Output")
        validation_df.to_excel(writer, index=False, sheet_name="Validation_Table")
        valid_output_df.to_excel(writer, index=False, sheet_name="Valid_Output")
        review_validation_df.to_excel(writer, index=False, sheet_name="Needs_Review")

    excel_bytes = excel_buffer.getvalue()

    d1, d2, d3 = st.columns(3, gap="large")

    with d1:
        if st.download_button(
            "⬇️ Download Output CSV",
            data=csv_bytes,
            file_name="kyc_output.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_output_csv_btn",
        ):
            rain(emoji="📄", font_size=16, falling_speed=4, animation_length="1")

    with d2:
        if st.download_button(
            "⬇️ Download Validation CSV",
            data=validation_csv_bytes,
            file_name="kyc_validation_table.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_validation_csv_btn",
        ):
            rain(emoji="✅", font_size=16, falling_speed=4, animation_length="1")

    with d3:
        if st.download_button(
            "⬇️ Download Excel",
            data=excel_bytes,
            file_name="kyc_week7_output_and_validation.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_excel_btn",
        ):
            rain(emoji="📊", font_size=16, falling_speed=4, animation_length="1")

    if st.button("⬅️ Back to Upload & Process", use_container_width=True, key="back_upload_btn"):
        st.switch_page("pages/U_P.py")
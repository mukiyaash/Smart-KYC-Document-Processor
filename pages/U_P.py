import hashlib
import io
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.let_it_rain import rain
from pdf2image import convert_from_bytes

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from auth import require_login
from api_client import check_api_health, extract_batch_via_api
from validator import FINAL_COLUMNS

from UI import (
    init_theme,
    inject_base_css,
    load_lottie_url,
    notification_bar,
    render_lottie,
    render_top_nav,
    build_sidebar,
    render_empty_state,
)

st.set_page_config(page_title="Upload & Process", layout="wide", initial_sidebar_state="expanded")

init_theme()
inject_base_css(show_sidebar=True)
require_login()

# API status must be checked before sidebar so sidebar can show backend status
api_ok, api_status = check_api_health()

render_top_nav("Upload & Process")
build_sidebar("upload", api_connected=api_ok)
notification_bar("Upload your KYC files. They will be processed automatically and can be reviewed document by document.")


# ---------------- CONFIG ----------------
POPPLER_PATH = r"C:\Poppler\poppler-25.07.0\Library\bin"


# ---------------- LOCAL PAGE CSS ----------------
st.markdown(
    """
    <style>
    .api-status-card{
        border-radius: 18px;
        padding: 1rem 1.25rem;
        margin: 0.35rem 0 1rem 0;
        border: 1px solid rgba(255,255,255,0.08);
        background: linear-gradient(135deg, rgba(7,34,44,0.95), rgba(9,44,37,0.92));
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }

    .api-status-head{
        font-size: 0.95rem;
        font-weight: 850;
        letter-spacing: 0.02em;
        opacity: 0.9;
        margin-bottom: 0.35rem;
    }

    .api-status-value{
        font-size: 1.15rem;
        font-weight: 850;
    }

    .api-ok{
        color: #68f0a7;
    }

    .api-fail{
        color: #ff8f8f;
    }

    .mode-card{
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 26px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 10px 35px rgba(2, 8, 23, 0.14);
        backdrop-filter: blur(12px);
        margin-bottom: 0.7rem;
    }

    .mode-title{
        font-size: 1.25rem;
        font-weight: 850;
        margin-bottom: 0.35rem;
    }

    .mode-sub{
        opacity: 0.76;
        font-size: 0.96rem;
        line-height: 1.7;
    }

    .legend-card{
        background: rgba(15, 23, 42, 0.68);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        min-height: 145px;
        box-shadow: 0 8px 26px rgba(2, 8, 23, 0.12);
    }

    .legend-title{
        font-size: 1.08rem;
        font-weight: 850;
        margin-bottom: 0.45rem;
    }

    .legend-text{
        opacity: 0.78;
        font-size: 0.94rem;
        line-height: 1.65;
    }

    .pdf-preview-note{
        border-radius: 18px;
        padding: 0.85rem 1rem;
        margin-top: 0.45rem;
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(14, 165, 233, 0.22);
        font-size: 0.92rem;
        opacity: 0.9;
        line-height: 1.6;
    }

    .file-card {
        background: rgba(15, 23, 42, 0.58);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        padding: 0.75rem 0.85rem;
        min-height: 92px;
        box-shadow: 0 8px 22px rgba(2, 8, 23, 0.10);
    }

    .file-name {
        font-size: 0.86rem;
        font-weight: 850;
        margin-bottom: 0.25rem;
        word-break: break-word;
    }

    .file-meta {
        opacity: 0.78;
        font-size: 0.76rem;
        line-height: 1.45;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- HELPERS ----------------
def make_upload_signature(files, mode):
    md5 = hashlib.md5()
    md5.update(str(mode).encode("utf-8", errors="ignore"))

    for f in files:
        data = f.getvalue()
        md5.update(f.name.encode("utf-8", errors="ignore"))
        md5.update(str(len(data)).encode())
        md5.update(data[:2048])

    return md5.hexdigest()


def clear_upload_state():
    st.session_state.kyc_results_df = pd.DataFrame(columns=FINAL_COLUMNS)
    st.session_state.kyc_processed = False
    st.session_state.kyc_uploaded_count = 0
    st.session_state.uploaded_doc_records = []
    st.session_state.processed_signature = None
    st.session_state.selected_doc_name = None
    st.session_state.uploader_reset_counter += 1


def make_preview_from_file(file):
    file_name = file.name.lower()
    file_bytes = file.getvalue()

    if file_name.endswith((".png", ".jpg", ".jpeg")):
        return {
            "preview_type": "image",
            "preview_data": file_bytes,
            "preview_df": None,
            "preview_error": None,
        }

    if file_name.endswith(".pdf"):
        try:
            pages = convert_from_bytes(
                file_bytes,
                dpi=180,
                first_page=1,
                last_page=1,
                poppler_path=POPPLER_PATH,
            )

            if pages:
                return {
                    "preview_type": "pdf_image",
                    "preview_data": pages[0].convert("RGB"),
                    "preview_df": None,
                    "preview_error": None,
                }

            return {
                "preview_type": "pdf_error",
                "preview_data": None,
                "preview_df": None,
                "preview_error": "PDF preview could not be generated.",
            }

        except Exception as e:
            return {
                "preview_type": "pdf_error",
                "preview_data": None,
                "preview_df": None,
                "preview_error": f"PDF preview failed: {str(e)}",
            }

    if file_name.endswith((".xlsx", ".xls")):
        try:
            if file_name.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            else:
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
                except Exception:
                    df = pd.read_excel(io.BytesIO(file_bytes))

            return {
                "preview_type": "excel",
                "preview_data": None,
                "preview_df": df.head(20),
                "preview_error": None,
            }
        except Exception as e:
            return {
                "preview_type": "none",
                "preview_data": None,
                "preview_df": None,
                "preview_error": f"Excel preview failed: {str(e)}",
            }

    return {
        "preview_type": "none",
        "preview_data": None,
        "preview_df": None,
        "preview_error": None,
    }


def build_doc_records_from_api_response(api_response, uploaded_files):
    file_lookup = {file.name: file for file in uploaded_files}
    doc_records = []
    final_rows = []

    files_response = api_response.get("files", [])

    for item in files_response:
        file_name = item.get("file_name", "Unknown File")
        file = file_lookup.get(file_name)

        preview_info = {
            "preview_type": "none",
            "preview_data": None,
            "preview_df": None,
            "preview_error": None,
        }

        if file is not None:
            preview_info = make_preview_from_file(file)

        if item.get("status") != "success":
            failed_schema = {
                "NAMES": "Not Found",
                "DATE_OF_BIRTH": "Not Found",
                "LOCATION": "Not Found",
                "ID_NUMBER": "Not Found",
                "NAME_STATUS": "Missing",
                "DOB_STATUS": "Missing",
                "LOCATION_STATUS": "Missing",
                "ID_STATUS": "Missing",
                "OVERALL_STATUS": "Needs Review",
                "REVIEW_REQUIRED": "Yes",
            }

            final_rows.append(failed_schema)

            doc_records.append(
                {
                    "file_name": file_name,
                    "file_type": "failed",
                    "preview_type": preview_info["preview_type"],
                    "preview_data": preview_info["preview_data"],
                    "preview_df": preview_info["preview_df"],
                    "preview_error": preview_info["preview_error"],
                    "ocr_text": item.get("error", "Processing failed."),
                    "schema": failed_schema,
                }
            )

            continue

        file_type = item.get("file_type", "document")

        if file_type == "excel":
            rows = item.get("results", [])

            for row in rows:
                final_rows.append(row)

            doc_records.append(
                {
                    "file_name": file_name,
                    "file_type": "excel",
                    "preview_type": preview_info["preview_type"],
                    "preview_data": preview_info["preview_data"],
                    "preview_df": preview_info["preview_df"],
                    "preview_error": preview_info["preview_error"],
                    "ocr_text": json.dumps(rows, indent=2),
                    "schema": rows,
                }
            )

        else:
            schema = item.get("extracted_schema", {})
            final_rows.append(schema)

            doc_records.append(
                {
                    "file_name": file_name,
                    "file_type": "document",
                    "preview_type": preview_info["preview_type"],
                    "preview_data": preview_info["preview_data"],
                    "preview_df": preview_info["preview_df"],
                    "preview_error": preview_info["preview_error"],
                    "ocr_text": item.get("ocr_preview", ""),
                    "schema": schema,
                }
            )

    return doc_records, final_rows


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


def render_api_status_card(is_connected: bool):
    if is_connected:
        st.markdown(
            """
            <div class="api-status-card">
                <div class="api-status-head">Backend Status</div>
                <div class="api-status-value api-ok">🟢 Connected</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="api-status-card">
                <div class="api-status-head">Backend Status</div>
                <div class="api-status-value api-fail">🔴 Connection Failed, Retry!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_legend_card(title, text):
    st.markdown(
        f"""
        <div class="legend-card">
            <div class="legend-title">{title}</div>
            <div class="legend-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_file_cards(records):
    if not records:
        return

    st.markdown("<div class='section-head'>Uploaded File Status</div>", unsafe_allow_html=True)

    cols = st.columns(4, gap="medium")

    for idx, rec in enumerate(records):
        with cols[idx % 4]:
            file_type = rec.get("file_type", "document")
            status = "✅ Processed" if file_type != "failed" else "⚠️ Failed"
            preview_type = rec.get("preview_type", "none")

            st.markdown(
                f"""
                <div class="file-card">
                    <div class="file-name">📄 {rec.get("file_name", "Unknown File")}</div>
                    <div class="file-meta">
                        {file_type} · {preview_type}<br>
                        {status}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------- SESSION STATE ----------------
if "kyc_results_df" not in st.session_state:
    st.session_state.kyc_results_df = pd.DataFrame(columns=FINAL_COLUMNS)

if "kyc_processed" not in st.session_state:
    st.session_state.kyc_processed = False

if "kyc_uploaded_count" not in st.session_state:
    st.session_state.kyc_uploaded_count = 0

if "uploaded_doc_records" not in st.session_state:
    st.session_state.uploaded_doc_records = []

if "processed_signature" not in st.session_state:
    st.session_state.processed_signature = None

if "selected_doc_name" not in st.session_state:
    st.session_state.selected_doc_name = None

if "kyc_speed_mode" not in st.session_state:
    st.session_state["kyc_speed_mode"] = "Balanced"

if "uploader_reset_counter" not in st.session_state:
    st.session_state.uploader_reset_counter = 0


# ---------------- HERO ----------------
top_left, top_right = st.columns([1.25, 0.9], gap="large")

with top_left:
    st.markdown(
        """
        <div class="hero-card">
            <div class="page-title">Upload & Processing</div>
            <div class="page-sub">
                Upload files and review each document’s preview, OCR text, extracted schema, and validation output.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    up_anim = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_49rdyysj.json")
    render_lottie(up_anim, height=205, key="upload_page_anim")

st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)

render_api_status_card(api_ok)

if not api_ok:
    with st.expander("Connection details"):
        st.json(api_status)


# ---------------- EXTRACTION MODE ----------------
st.markdown(
    """
    <div class="mode-card">
        <div class="mode-title">⚡ Extraction Mode</div>
        <div class="mode-sub">
            Choose the processing depth for the current run.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

mode = sac.segmented(
    items=["Fast", "Balanced", "Accurate"],
    index=["Fast", "Balanced", "Accurate"].index(st.session_state["kyc_speed_mode"])
    if st.session_state["kyc_speed_mode"] in ["Fast", "Balanced", "Accurate"]
    else 1,
    align="start",
    size="lg",
    color="cyan",
    return_index=False,
)

if mode:
    st.session_state["kyc_speed_mode"] = mode
else:
    mode = st.session_state["kyc_speed_mode"]

st.markdown("<div style='height:0.65rem'></div>", unsafe_allow_html=True)

l1, l2, l3 = st.columns(3, gap="large")

with l1:
    render_legend_card(
        "🚀 Fast",
        "Quick OCR pass for clean images and faster backend response."
    )

with l2:
    render_legend_card(
        "⚖️ Balanced",
        "Recommended default mode with a balance between speed and extraction accuracy."
    )

with l3:
    render_legend_card(
        "🎯 Accurate",
        "Deeper OCR processing for noisy, unclear, or difficult KYC files."
    )

st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)


# ---------------- UPLOADER ----------------
uploader_key = f"kyc_file_uploader_{st.session_state.uploader_reset_counter}"

uploaded_files = st.file_uploader(
    "Upload files",
    type=["png", "jpg", "jpeg", "pdf", "xlsx", "xls"],
    accept_multiple_files=True,
    key=uploader_key,
)


# ---------------- PROCESS FILES ----------------
if uploaded_files:
    st.session_state.kyc_uploaded_count = len(uploaded_files)
    new_signature = make_upload_signature(uploaded_files, mode)

    if st.session_state.processed_signature != new_signature:
        if not api_ok:
            st.stop()

        progress = st.progress(0)
        status_text = st.empty()

        with st.spinner("Processing Files..."):
            status_text.info("Reading uploaded documents...")
            progress.progress(20)

            success, api_response = extract_batch_via_api(uploaded_files, mode=mode)
            progress.progress(60)

            if not success:
                st.error("Processing failed.")
                st.json(api_response)
                st.stop()

            status_text.info("Building document previews and extracted schema...")
            doc_records, final_rows = build_doc_records_from_api_response(api_response, uploaded_files)
            progress.progress(85)

            st.session_state.uploaded_doc_records = doc_records
            st.session_state.kyc_results_df = pd.DataFrame(final_rows, columns=FINAL_COLUMNS)
            st.session_state.kyc_processed = True
            st.session_state.processed_signature = new_signature
            st.session_state.selected_doc_name = doc_records[0]["file_name"] if doc_records else None

            progress.progress(100)
            status_text.success("Processing completed.")

        rain(emoji="✨", font_size=16, falling_speed=4, animation_length="1")
        st.rerun()


# ---------------- STATUS SUMMARY ----------------
if st.session_state.uploaded_doc_records:
    df_current = st.session_state.kyc_results_df.copy()

    uploaded_count = st.session_state.kyc_uploaded_count
    structured_rows = len(df_current)
    valid_count = int((df_current["OVERALL_STATUS"] == "Valid").sum()) if "OVERALL_STATUS" in df_current.columns else 0
    review_count = int((df_current["REVIEW_REQUIRED"] == "Yes").sum()) if "REVIEW_REQUIRED" in df_current.columns else 0

    c1, c2, c3, c4 = st.columns(4, gap="large")

    with c1:
        render_metric("📦 Uploaded Files", uploaded_count)

    with c2:
        render_metric("📄 Structured Rows", structured_rows)

    with c3:
        render_metric("✅ Valid Records", valid_count)

    with c4:
        render_metric("⚠️ Needs Review", review_count)

    render_file_cards(st.session_state.uploaded_doc_records)


# ---------------- DOCUMENT VIEWER ----------------
if st.session_state.uploaded_doc_records:
    st.markdown("<div class='section-head'>Document Viewer</div>", unsafe_allow_html=True)

    file_names = [rec["file_name"] for rec in st.session_state.uploaded_doc_records]

    if st.session_state.selected_doc_name not in file_names:
        st.session_state.selected_doc_name = file_names[0]

    selected_file = st.selectbox(
        "Select uploaded document",
        file_names,
        index=file_names.index(st.session_state.selected_doc_name),
    )

    st.session_state.selected_doc_name = selected_file

    selected_record = next(
        rec for rec in st.session_state.uploaded_doc_records if rec["file_name"] == selected_file
    )

    left, right = st.columns([1.0, 1.0], gap="large")

    with left:
        st.markdown(
            """
            <div class="glass-card">
                <div style="font-size:1.12rem;font-weight:850;">🖼️ Document Preview</div>
                <div class="small-note" style="margin-top:0.25rem;">
                    Preview of the currently selected uploaded file.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        if selected_record["preview_type"] == "image":
            st.image(selected_record["preview_data"], use_container_width=True)

        elif selected_record["preview_type"] == "pdf_image":
            st.image(selected_record["preview_data"], use_container_width=True)
            st.markdown(
                """
                <div class="pdf-preview-note">
                    PDF preview shows the first page only. OCR extraction may process more pages depending on the selected mode.
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif selected_record["preview_type"] == "excel":
            if selected_record["preview_df"] is not None:
                st.dataframe(selected_record["preview_df"], use_container_width=True, hide_index=True)
            else:
                st.info("Excel preview unavailable.")

        elif selected_record["preview_type"] == "pdf_error":
            st.warning("PDF preview unavailable, but OCR extraction may still work.")
            if selected_record.get("preview_error"):
                st.caption(selected_record["preview_error"])

        else:
            st.info("Preview unavailable for this file type. OCR/API output is available on the right.")

    with right:
        tab1, tab2 = st.tabs(["OCR Preview", "Extracted Schema"])

        with tab1:
            st.code(
                selected_record["ocr_text"][:12000]
                if selected_record["ocr_text"]
                else "No OCR text available.",
                language="text",
            )

        with tab2:
            st.code(json.dumps(selected_record["schema"], indent=2), language="json")

    st.markdown("<div style='height:0.65rem'></div>", unsafe_allow_html=True)

    st.info("✅ Files are processed here. Final structured output and validation metrics are shown in the Results page.")

    a1, a2 = st.columns(2, gap="large")

    with a1:
        if st.button("📊 Open Results", use_container_width=True, key="open_results_btn"):
            st.switch_page("pages/Results.py")

    with a2:
        if st.button("🗑️ Clear Current Batch", use_container_width=True, key="clear_batch_btn"):
            clear_upload_state()
            st.rerun()

else:
    render_empty_state(
        "Awaiting Upload",
        "Upload one or more KYC files to start processing and validation.",
        icon="📂"
    )
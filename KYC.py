import streamlit as st
from streamlit_extras.let_it_rain import rain

from auth import init_auth_state, render_auth_page, render_user_box

from UI import (
    init_theme,
    inject_base_css,
    load_lottie_url,
    notification_bar,
    render_lottie,
    render_top_nav,
    render_workflow_timeline,
    render_tech_badges,
)

st.set_page_config(page_title="Smart KYC AI", layout="wide")

init_theme()
inject_base_css(show_sidebar=False)

init_auth_state()

if not st.session_state.authenticated:
    render_auth_page()
    st.stop()

render_top_nav("Home")
render_user_box()

notification_bar("Smart KYC workspace ready. Upload documents, process fields, and review structured results.")

hero_left, hero_right = st.columns([1.25, 0.95], gap="large")

with hero_left:
    st.markdown(
        """
        <div class="hero-card">
            <div class="pill">✨ AI-enabled KYC workflow</div>
            <div class="page-title">Smart KYC Document Processor</div>
            <div class="page-sub">
                Process Aadhaar-like samples, passport-style documents, images, PDFs, and spreadsheets
                through a clean multi-page interface with standardized outputs.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        go_upload = st.button("🚀 Go to Upload & Process", use_container_width=True, key="home_go_upload")

    with c2:
        go_results = st.button("📊 Open Results", use_container_width=True, key="home_go_results")

    if go_upload:
        rain(emoji="✨", font_size=18, falling_speed=4, animation_length="1")
        st.switch_page("pages/U_P.py")

    if go_results:
        rain(emoji="📊", font_size=16, falling_speed=4, animation_length="1")
        st.switch_page("pages/Results.py")

with hero_right:
    home_anim = load_lottie_url("https://assets3.lottiefiles.com/packages/lf20_iorpbol0.json")
    render_lottie(home_anim, height=340, key="home_main_lottie")

st.markdown("<div class='section-head'>Workflow</div>", unsafe_allow_html=True)
render_workflow_timeline()

st.markdown("<div class='section-head'>Technology Stack</div>", unsafe_allow_html=True)
render_tech_badges([
    "Streamlit",
    "FastAPI",
    "PyTesseract",
    "spaCy",
    "Pandas",
    "SQLite",
    "OpenCV",
    "ReportLab",
])

st.markdown("<div class='section-head'>Platform Highlights</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="large")

cards = [
    ("📂 Multi-format intake", "Upload JPG, PNG, PDF, XLS, and XLSX files in one workflow."),
    ("⚡ Guided extraction", "Move from upload to processing to results in a cleaner sequence."),
    ("📄 Standardized output", "All extracted outputs are normalized into NAMES, DATE_OF_BIRTH, LOCATION, and ID_NUMBER."),
]

for col, (head, body) in zip([c1, c2, c3], cards):
    with col:
        st.markdown(
            f"""
            <div class="glass-card" style="min-height:190px;">
                <div style="font-size:1.28rem;font-weight:850;margin-bottom:0.55rem;">{head}</div>
                <div class="small-note" style="line-height:1.8;">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div class='section-head'>Quick Flow</div>", unsafe_allow_html=True)

f1, f2, f3 = st.columns(3, gap="large")

flow = [
    ("1. Login", "Sign in or create an account to access the workspace."),
    ("2. Upload", "Choose one or multiple KYC files."),
    ("3. Review", "Validate and download the structured results."),
]

for col, (head, body) in zip([f1, f2, f3], flow):
    with col:
        st.markdown(
            f"""
            <div class="glass-card">
                <div style="font-size:1.2rem;font-weight:850;">{head}</div>
                <div class="small-note" style="margin-top:0.45rem;line-height:1.8;">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
import json
from pathlib import Path

import requests
import streamlit as st
import streamlit_antd_components as sac
from streamlit_lottie import st_lottie

from auth import logout_user

ASSETS_DIR = Path(__file__).parent / "assets"


# ---------------- THEME ----------------
def init_theme():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"


def is_dark():
    init_theme()
    return st.session_state.theme_mode == "dark"


def toggle_theme():
    init_theme()
    st.session_state.theme_mode = "light" if is_dark() else "dark"


def page_colors():
    if is_dark():
        return {
            "bg1": "#020617",
            "bg2": "#03142f",
            "bg3": "#02101f",
            "card": "rgba(15, 23, 42, 0.72)",
            "card2": "rgba(10, 18, 35, 0.90)",
            "card3": "rgba(30, 41, 59, 0.55)",
            "border": "rgba(148, 163, 184, 0.20)",
            "text": "#f8fafc",
            "muted": "#cbd5e1",
            "soft": "#94a3b8",
            "sidebar": "rgba(4, 18, 42, 0.96)",
            "notice1": "#0ea5e9",
            "notice2": "#22c55e",
            "notice3": "#8b5cf6",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
        }

    return {
        "bg1": "#edf5ff",
        "bg2": "#f9fbff",
        "bg3": "#eef6ff",
        "card": "rgba(255, 255, 255, 0.84)",
        "card2": "rgba(255, 255, 255, 0.94)",
        "card3": "rgba(248, 250, 252, 0.92)",
        "border": "rgba(30, 41, 59, 0.12)",
        "text": "#0f172a",
        "muted": "#475569",
        "soft": "#64748b",
        "sidebar": "rgba(255, 255, 255, 0.96)",
        "notice1": "#2563eb",
        "notice2": "#10b981",
        "notice3": "#7c3aed",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#dc2626",
    }


# ---------------- NAV HELPERS ----------------
def get_main_app_file():
    root = Path(__file__).resolve().parent

    if (root / "KYC.py").exists():
        return "KYC.py"

    return "dummy.py"


def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None

    return None


def render_lottie(animation, height=280, key="lottie"):
    if animation:
        st_lottie(animation, height=height, key=key)
    else:
        st.markdown(
            """
            <div class="glass-card" style="height:280px;display:flex;align-items:center;justify-content:center;">
                <div style="font-size:1.05rem;font-weight:700;opacity:.75;">Animation unavailable</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------- GLOBAL CSS ----------------
def inject_base_css(show_sidebar=True):
    c = page_colors()

    if show_sidebar:
        sidebar_css = f"""
        [data-testid="stSidebar"] {{
            display: block !important;
            visibility: visible !important;
            background: {c["sidebar"]} !important;
            border-right: 1px solid {c["border"]};
        }}

        [data-testid="stSidebar"] > div:first-child {{
            display: block !important;
            visibility: visible !important;
        }}
        """
    else:
        sidebar_css = """
        [data-testid="stSidebar"] {
            display:none !important;
            visibility:hidden !important;
        }
        """

    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility:hidden;}}
        footer {{visibility:hidden;}}
        header {{visibility:hidden;}}
        [data-testid="stSidebarNav"] {{display:none !important;}}

        {sidebar_css}

        .stApp {{
            background:
                radial-gradient(circle at 10% 15%, rgba(14,165,233,0.16), transparent 24%),
                radial-gradient(circle at 88% 12%, rgba(139,92,246,0.12), transparent 24%),
                radial-gradient(circle at 50% 90%, rgba(34,197,94,0.08), transparent 28%),
                linear-gradient(135deg, {c["bg1"]} 0%, {c["bg2"]} 45%, {c["bg3"]} 100%);
            color: {c["text"]};
        }}

        [data-testid="stAppViewContainer"] {{
            background: transparent !important;
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1240px;
        }}

        [data-testid="stSidebar"] * {{
            color: {c["text"]};
        }}

        .glass-card {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 28px;
            padding: 1.2rem 1.3rem;
            box-shadow: 0 14px 42px rgba(2, 8, 23, 0.18);
            backdrop-filter: blur(14px);
        }}

        .glass-card-compact {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 22px;
            padding: 1rem;
            box-shadow: 0 10px 30px rgba(2, 8, 23, 0.14);
            backdrop-filter: blur(12px);
        }}

        .hero-card {{
            background:
                radial-gradient(circle at 15% 15%, rgba(14,165,233,0.14), transparent 28%),
                linear-gradient(135deg, rgba(37,99,235,0.12), rgba(34,211,238,0.08)),
                {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 32px;
            padding: 1.55rem 1.6rem;
            box-shadow: 0 16px 46px rgba(2, 8, 23, 0.22);
            backdrop-filter: blur(16px);
        }}

        .page-title {{
            font-size: 2.5rem;
            font-weight: 850;
            line-height: 1.05;
            color: {c["text"]};
            margin-bottom: 0.7rem;
            letter-spacing: -0.03em;
        }}

        .page-sub {{
            font-size: 1.02rem;
            line-height: 1.8;
            color: {c["muted"]};
        }}

        .pill {{
            display: inline-block;
            padding: 0.38rem 0.8rem;
            border-radius: 999px;
            background: rgba(37,99,235,0.14);
            color: {c["muted"]};
            border: 1px solid {c["border"]};
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }}

        .pretty-bar {{
            width: 100%;
            border-radius: 18px;
            padding: 0.9rem 1rem;
            color: white;
            font-weight: 800;
            margin: 0.35rem 0 1rem 0;
            background: linear-gradient(90deg, {c["notice1"]}, {c["notice2"]}, {c["notice3"]});
            background-size: 200% 200%;
            animation: shiftbar 8s ease infinite;
            box-shadow: 0 10px 30px rgba(2, 8, 23, 0.16);
        }}

        @keyframes shiftbar {{
            0% {{background-position: 0% 50%;}}
            50% {{background-position: 100% 50%;}}
            100% {{background-position: 0% 50%;}}
        }}

        .sidebar-card {{
            background: {c["card2"]};
            border: 1px solid {c["border"]};
            border-radius: 22px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 24px rgba(2, 8, 23, 0.10);
        }}

        .sidebar-title {{
            font-size: 1.02rem;
            font-weight: 850;
            margin-bottom: 0.45rem;
            color: {c["text"]};
        }}

        .sidebar-muted {{
            color: {c["muted"]};
            line-height: 1.7;
            font-size: 0.95rem;
        }}

        div.stButton > button {{
            width: 100%;
            border-radius: 18px !important;
            border: 1px solid {c["border"]} !important;
            min-height: 3rem;
            font-weight: 750 !important;
            transition: all .22s ease !important;
            box-shadow: 0 8px 22px rgba(2, 8, 23, 0.12);
        }}

        div.stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 16px 32px rgba(2, 8, 23, 0.20);
        }}

        .metric-chip {{
            background: {c["card2"]};
            border: 1px solid {c["border"]};
            border-radius: 24px;
            padding: 1rem 1.1rem;
            text-align: left;
            box-shadow: 0 10px 28px rgba(2, 8, 23, 0.12);
        }}

        .metric-num {{
            font-size: 2rem;
            font-weight: 850;
            color: {c["text"]};
            letter-spacing: -0.03em;
        }}

        .metric-label {{
            color: {c["muted"]};
            font-weight: 650;
            font-size: 0.96rem;
        }}

        .section-head {{
            font-size: 1.65rem;
            font-weight: 850;
            color: {c["text"]};
            margin: 1rem 0 0.8rem 0;
            letter-spacing: -0.02em;
        }}

        .small-note {{
            color: {c["muted"]};
            font-size: 0.95rem;
        }}

        .nav-action-small button {{
            min-height: 3rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            font-size: 0.9rem !important;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 850;
            border: 1px solid {c["border"]};
        }}

        .badge-valid {{
            background: rgba(34,197,94,0.15);
            color: {c["success"]};
        }}

        .badge-review {{
            background: rgba(245,158,11,0.16);
            color: {c["warning"]};
        }}

        .badge-api {{
            background: rgba(14,165,233,0.15);
            color: #38bdf8;
        }}

        .workflow-strip {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 0.75rem;
        }}

        .workflow-step {{
            background: {c["card2"]};
            border: 1px solid {c["border"]};
            border-radius: 22px;
            padding: 0.9rem;
            min-height: 115px;
            box-shadow: 0 10px 26px rgba(2, 8, 23, 0.10);
        }}

        .workflow-num {{
            width: 32px;
            height: 32px;
            border-radius: 12px;
            background: linear-gradient(135deg, {c["notice1"]}, {c["notice3"]});
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 850;
            margin-bottom: 0.55rem;
        }}

        .workflow-title {{
            font-weight: 850;
            color: {c["text"]};
            margin-bottom: 0.25rem;
        }}

        .workflow-sub {{
            color: {c["muted"]};
            font-size: 0.83rem;
            line-height: 1.55;
        }}

        .tech-badge {{
            display: inline-block;
            margin: 0.25rem 0.25rem 0.25rem 0;
            padding: 0.42rem 0.7rem;
            border-radius: 999px;
            background: {c["card3"]};
            border: 1px solid {c["border"]};
            color: {c["muted"]};
            font-weight: 700;
            font-size: 0.86rem;
        }}

        .progress-shell {{
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: rgba(148,163,184,0.18);
            overflow: hidden;
            border: 1px solid {c["border"]};
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, {c["notice1"]}, {c["notice2"]});
        }}

        @media (max-width: 980px) {{
            .workflow-strip {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .page-title {{
                font-size: 2.05rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------- BASIC COMPONENTS ----------------
def notification_bar(message: str):
    st.markdown(f'<div class="pretty-bar">✨ {message}</div>', unsafe_allow_html=True)


def status_badge(label: str, status_type="api"):
    cls = "badge-api"
    if status_type == "valid":
        cls = "badge-valid"
    elif status_type == "review":
        cls = "badge-review"

    st.markdown(
        f'<span class="status-badge {cls}">{label}</span>',
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value, note: str = ""):
    note_html = f'<div class="small-note" style="margin-top:0.25rem;">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="metric-chip">
            <div class="metric-label">{label}</div>
            <div class="metric-num">{value}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_card(title: str, value: int, total: int):
    percent = 0 if total == 0 else int((value / total) * 100)
    st.markdown(
        f"""
        <div class="glass-card-compact">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.55rem;">
                <div style="font-weight:850;">{title}</div>
                <div class="small-note">{percent}%</div>
            </div>
            <div class="progress-shell">
                <div class="progress-fill" style="width:{percent}%;"></div>
            </div>
            <div class="small-note" style="margin-top:0.45rem;">{value} of {total} records valid</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, message: str, icon="📂"):
    st.markdown(
        f"""
        <div class="glass-card" style="text-align:center;padding:2rem;">
            <div style="font-size:3rem;margin-bottom:0.7rem;">{icon}</div>
            <div style="font-size:1.25rem;font-weight:850;margin-bottom:0.4rem;">{title}</div>
            <div class="small-note" style="line-height:1.75;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_timeline():
    steps = [
        ("1", "Login", "Secure workspace access"),
        ("2", "Upload", "Add KYC files"),
        ("3", "OCR", "Read document text"),
        ("4", "Extract", "Find KYC fields"),
        ("5", "Validate", "Check field quality"),
        ("6", "Export", "Download outputs"),
    ]

    cols = st.columns(6, gap="small")

    for col, (num, title, sub) in zip(cols, steps):
        with col:
            st.markdown(
                f'<div class="workflow-step">'
                f'<div class="workflow-num">{num}</div>'
                f'<div class="workflow-title">{title}</div>'
                f'<div class="workflow-sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_tech_badges(items):
    html = ""
    for item in items:
        html += f'<span class="tech-badge">{item}</span>'
    st.markdown(html, unsafe_allow_html=True)


# ---------------- TOP NAV ----------------
def render_top_nav(active_label: str):
    init_theme()
    c = page_colors()

    left, mid, theme_col, logout_col = st.columns(
        [1.25, 1.75, 0.55, 0.55],
        vertical_alignment="center",
    )

    with left:
        st.markdown(
            f"""
            <div class="glass-card" style="padding:0.95rem 1.1rem;">
                <div style="font-size:2rem;font-weight:850;color:{c["text"]};">📄 Smart KYC AI</div>
                <div style="color:{c["muted"]};margin-top:0.15rem;">Document extraction workspace</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with mid:
        items = ["Home", "Upload & Process", "Results"]

        if active_label not in items:
            active_label = "Home"

        current_index = items.index(active_label)

        selected = sac.segmented(
            items=items,
            index=current_index,
            align="center",
            size="lg",
            color="blue",
            return_index=False,
        )

        if selected and selected != active_label:
            if selected == "Home":
                st.switch_page(get_main_app_file())
            elif selected == "Upload & Process":
                st.switch_page("pages/U_P.py")
            elif selected == "Results":
                st.switch_page("pages/Results.py")

    with theme_col:
        st.markdown('<div class="nav-action-small">', unsafe_allow_html=True)

        if st.button("☀️ Light" if is_dark() else "🌙 Dark", key=f"theme_{active_label}"):
            toggle_theme()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with logout_col:
        st.markdown('<div class="nav-action-small">', unsafe_allow_html=True)

        if st.session_state.get("authenticated", False):
            if st.button("🚪 Logout", key=f"logout_{active_label}"):
                logout_user()

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------
def build_sidebar(page_name: str, api_connected=None):
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-card">
                <div class="sidebar-title">📌 Smart KYC AI v1.0</div>
                <div class="sidebar-muted">
                    AI-based banking onboarding workspace for OCR, extraction, validation, and profile generation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if api_connected is not None:
            status_text = "🟢 Backend Connected" if api_connected else "🔴 Backend Offline"
            st.markdown(
                f"""
                <div class="sidebar-card">
                    <div class="sidebar-title">🔌 System Status</div>
                    <div class="sidebar-muted">
                        {status_text}<br>
                        Mode: Active Workspace
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if page_name == "upload":
            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="sidebar-title">⚙️ Upload Checklist</div>
                    <div class="sidebar-muted">
                        ✅ Upload files<br>
                        ✅ Auto-process batch<br>
                        ✅ Inspect document preview<br>
                        ✅ Review OCR/schema<br>
                        ✅ Open final results
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="sidebar-title">📂 Supported Files</div>
                    <div class="sidebar-muted">
                        PNG · JPG · JPEG<br>
                        PDF · XLSX · XLS
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="sidebar-title">🧾 Standard Fields</div>
                    <div class="sidebar-muted">
                        NAMES<br>
                        DATE_OF_BIRTH<br>
                        LOCATION<br>
                        ID_NUMBER
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            anim = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_qp1q7mct.json")
            render_lottie(anim, height=165, key="sidebar_upload_anim")

        elif page_name == "results":
            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="sidebar-title">📊 Results Workflow</div>
                    <div class="sidebar-muted">
                        ✅ View field coverage<br>
                        ✅ Check structured output<br>
                        ✅ Review enriched profile<br>
                        ✅ Export CSV/Excel/PDF
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="sidebar-title">✅ Validation Focus</div>
                    <div class="sidebar-muted">
                        Records marked Valid are export-ready. Records marked Review need manual checking.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            anim = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json")
            render_lottie(anim, height=165, key="sidebar_results_anim")
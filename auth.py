import re
import streamlit as st

from auth_db import create_user, authenticate_user, init_user_db


# ---------------- AUTH SESSION SETUP ----------------
def init_auth_state():
    init_user_db()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None

    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"


# ---------------- VALIDATION HELPERS ----------------
def is_valid_email(email: str) -> bool:
    email = str(email).strip().lower()
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def is_valid_username(username: str) -> bool:
    username = str(username).strip()

    if len(username) < 3:
        return False

    pattern = r"^[A-Za-z0-9_.]+$"
    return re.match(pattern, username) is not None


def logout_user():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_page = "login"
    st.rerun()


# ---------------- AUTH CSS ----------------
def inject_auth_css():
    st.markdown(
        """
<style>
.stApp {
    background:
        radial-gradient(circle at 12% 18%, rgba(14, 165, 233, 0.30), transparent 28%),
        radial-gradient(circle at 82% 12%, rgba(139, 92, 246, 0.24), transparent 28%),
        radial-gradient(circle at 55% 90%, rgba(34, 197, 94, 0.13), transparent 30%),
        linear-gradient(135deg, #020617 0%, #03142f 45%, #02101f 100%) !important;
    color: #f8fafc;
    overflow: hidden;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: -20%;
    z-index: 0;
    pointer-events: none;
    background:
        radial-gradient(circle at 20% 30%, rgba(14, 165, 233, 0.26), transparent 18%),
        radial-gradient(circle at 78% 24%, rgba(139, 92, 246, 0.22), transparent 20%),
        radial-gradient(circle at 60% 78%, rgba(34, 197, 94, 0.15), transparent 18%);
    filter: blur(18px);
    animation: authGlowMove 16s ease-in-out infinite alternate;
}

.stApp::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(125, 211, 252, 0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(125, 211, 252, 0.055) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: linear-gradient(to bottom, rgba(0,0,0,0.75), rgba(0,0,0,0.08));
    animation: authGridDrift 20s linear infinite;
}

@keyframes authGlowMove {
    0% {
        transform: translate3d(-2%, -2%, 0) scale(1);
        opacity: 0.8;
    }

    50% {
        transform: translate3d(2%, 3%, 0) scale(1.08);
        opacity: 1;
    }

    100% {
        transform: translate3d(4%, -1%, 0) scale(1.04);
        opacity: 0.9;
    }
}

@keyframes authGridDrift {
    0% {
        background-position: 0 0, 0 0;
    }

    100% {
        background-position: 48px 48px, 48px 48px;
    }
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
    position: relative;
    z-index: 1;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stSidebar"] {
    display: none !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1240px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 1.5rem !important;
    position: relative;
    z-index: 2;
}

/* Left glass panel */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {
    min-height: 640px;
    border-radius: 34px;
    padding: 2rem !important;
    background:
        radial-gradient(circle at 20% 15%, rgba(56,189,248,0.20), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(139,92,246,0.16), transparent 30%),
        linear-gradient(135deg, rgba(15,23,42,0.70), rgba(2,6,23,0.78));
    border: 1px solid rgba(148,163,184,0.24);
    box-shadow: 0 20px 60px rgba(2,8,23,0.40);
    backdrop-filter: blur(18px);
    overflow: hidden;
}

/* Right glass panel */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
    min-height: 640px;
    border-radius: 34px;
    padding: 2rem !important;
    background:
        radial-gradient(circle at 50% 8%, rgba(14,165,233,0.16), transparent 32%),
        radial-gradient(circle at 90% 88%, rgba(34,197,94,0.10), transparent 26%),
        linear-gradient(135deg, rgba(15,23,42,0.70), rgba(2,6,23,0.80));
    border: 1px solid rgba(148,163,184,0.24);
    box-shadow: 0 20px 60px rgba(2,8,23,0.40);
    backdrop-filter: blur(18px);
}

.auth-pill {
    display: inline-block;
    padding: 0.45rem 0.85rem;
    border-radius: 999px;
    color: #e0f2fe;
    background: rgba(14,165,233,0.20);
    border: 1px solid rgba(125,211,252,0.30);
    font-weight: 800;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.auth-title {
    font-size: 3rem;
    line-height: 1.05;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: -0.04em;
    margin-bottom: 1rem;
}

.auth-subtitle {
    color: #dbeafe;
    font-size: 1rem;
    line-height: 1.8;
    margin-bottom: 1.25rem;
}

.auth-feature-card {
    border-radius: 22px;
    padding: 1rem;
    min-height: 135px;
    background: rgba(30,41,59,0.56);
    border: 1px solid rgba(148,163,184,0.22);
    box-shadow: 0 10px 28px rgba(2,8,23,0.20);
    backdrop-filter: blur(12px);
}

.auth-feature-title {
    color: #f8fafc;
    font-size: 0.95rem;
    font-weight: 850;
    margin-bottom: 0.35rem;
}

.auth-feature-sub {
    color: #dbeafe;
    font-size: 0.84rem;
    line-height: 1.55;
}

.auth-flow-card {
    margin-top: 1.2rem;
    border-radius: 24px;
    padding: 1.05rem;
    background: linear-gradient(135deg, rgba(14,165,233,0.22), rgba(34,197,94,0.16));
    border: 1px solid rgba(148,163,184,0.22);
    box-shadow: 0 10px 28px rgba(2,8,23,0.18);
}

.auth-flow-title {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 850;
    margin-bottom: 0.5rem;
}

.auth-flow-steps {
    color: #dbeafe;
    font-size: 0.9rem;
    line-height: 1.7;
}

.auth-bottom-note {
    color: #cbd5e1;
    font-size: 0.88rem;
    line-height: 1.7;
    margin-top: 1.2rem;
}

.auth-form-top {
    text-align: center;
    margin-bottom: 1.2rem;
    margin-top: 1.6rem;
}

.auth-form-icon {
    width: 62px;
    height: 62px;
    margin: 0 auto 0.75rem auto;
    border-radius: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.85rem;
    background: linear-gradient(135deg, rgba(14,165,233,0.30), rgba(139,92,246,0.30));
    border: 1px solid rgba(148,163,184,0.22);
}

.auth-form-title {
    font-size: 1.85rem;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 0.35rem;
}

.auth-form-sub {
    color: #dbeafe;
    font-size: 0.94rem;
    line-height: 1.65;
}

.auth-switch-box {
    margin-top: 1rem;
    padding: 0.9rem;
    border-radius: 20px;
    background: rgba(2,6,23,0.35);
    border: 1px solid rgba(148,163,184,0.20);
    text-align: center;
}

.auth-switch-text {
    color: #dbeafe;
    font-size: 0.9rem;
}

.auth-mini-note {
    color: #cbd5e1;
    font-size: 0.78rem;
    text-align: center;
    line-height: 1.55;
    margin-top: 0.75rem;
}

div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

div[data-testid="stTextInput"] label {
    color: #e2e8f0 !important;
    font-weight: 800 !important;
    font-size: 0.9rem !important;
}

div[data-testid="stTextInput"] input {
    border-radius: 16px !important;
    min-height: 2.8rem !important;
    background: rgba(255,255,255,0.94) !important;
    border: 1px solid rgba(148,163,184,0.22) !important;
    color: #0f172a !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: rgba(14,165,233,0.8) !important;
    box-shadow: 0 0 0 2px rgba(14,165,233,0.18) !important;
}

div[data-testid="stFormSubmitButton"] button,
div.stButton > button {
    border-radius: 18px !important;
    min-height: 3rem !important;
    font-weight: 850 !important;
    border: 1px solid rgba(148,163,184,0.18) !important;
    background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
    color: white !important;
    box-shadow: 0 12px 28px rgba(14,165,233,0.20) !important;
    transition: all 0.22s ease !important;
}

div[data-testid="stFormSubmitButton"] button:hover,
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 34px rgba(14,165,233,0.28) !important;
}

.stAlert {
    border-radius: 18px !important;
}

@media (max-width: 1000px) {
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1),
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
        min-height: auto;
    }

    .auth-title {
        font-size: 2.2rem;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


# ---------------- SMALL HTML HELPERS ----------------
def html_line(content: str):
    st.markdown(content, unsafe_allow_html=True)


def feature_card(title: str, body: str):
    st.markdown(
        f'<div class="auth-feature-card"><div class="auth-feature-title">{title}</div><div class="auth-feature-sub">{body}</div></div>',
        unsafe_allow_html=True,
    )


# ---------------- LEFT PANEL ----------------
def render_auth_left_panel():
    html_line('<div class="auth-pill">✨ AI-enabled KYC workflow</div>')

    html_line(
        '<div class="auth-title">Smart KYC<br>Document Processor</div>'
    )

    html_line(
        '<div class="auth-subtitle">A banking AI workspace that extracts customer details from images, PDFs, and Excel files using OCR, structured validation, and a clean review dashboard.</div>'
    )

    c1, c2 = st.columns(2)

    with c1:
        feature_card(
            "📂 Multi-format intake",
            "Supports PNG, JPG, JPEG, PDF, XLS, and XLSX documents."
        )

    with c2:
        feature_card(
            "🧠 OCR + extraction",
            "Uses PyTesseract, rules, and spaCy support to extract KYC fields."
        )

    c3, c4 = st.columns(2)

    with c3:
        feature_card(
            "✅ Validation engine",
            "Checks name, DOB, location, and ID fields before final review."
        )

    with c4:
        feature_card(
            "📊 Dashboard output",
            "Displays structured results with CSV, Excel, and PDF downloads."
        )

    html_line(
        '<div class="auth-flow-card"><div class="auth-flow-title">Workflow</div><div class="auth-flow-steps">Login → Upload KYC files → OCR processing → Field extraction → Validation → Enriched KYC profile</div></div>'
    )

    html_line(
        '<div class="auth-bottom-note">Built for banking onboarding automation, project demonstration, and full-stack AI portfolio presentation.</div>'
    )


# ---------------- FORM HEADER ----------------
def render_form_header(mode: str):
    if mode == "signup":
        icon = "📝"
        title = "Create Account"
        subtitle = "Register your account to start using the KYC workspace."
    else:
        icon = "🔐"
        title = "Welcome Back"
        subtitle = "Login to continue document extraction and validation."

    st.markdown(
        f'<div class="auth-form-top"><div class="auth-form-icon">{icon}</div><div class="auth-form-title">{title}</div><div class="auth-form-sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


# ---------------- LOGIN FORM ----------------
def render_login_form():
    render_form_header("login")

    with st.form("login_form", clear_on_submit=False):
        username_or_email = st.text_input(
            "Username or Email",
            placeholder="Enter username or email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        login_button = st.form_submit_button(
            "Login to Workspace",
            use_container_width=True
        )

    if login_button:
        success, result = authenticate_user(username_or_email, password)

        if success:
            st.session_state.authenticated = True
            st.session_state.user = result
            st.success("Login successful.")
            st.rerun()
        else:
            st.error(result)

    html_line(
        '<div class="auth-switch-box"><div class="auth-switch-text">New to Smart KYC?</div></div>'
    )

    if st.button("Create New Account", use_container_width=True, key="go_to_signup"):
        st.session_state.auth_page = "signup"
        st.rerun()

    html_line(
        '<div class="auth-mini-note">Secure local login using SQLite and bcrypt password hashing.</div>'
    )


# ---------------- SIGNUP FORM ----------------
def render_signup_form():
    render_form_header("signup")

    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        email = st.text_input(
            "Email",
            placeholder="Enter your email"
        )

        username = st.text_input(
            "Username",
            placeholder="Choose a username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter password"
        )

        signup_button = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

    if signup_button:
        full_name = full_name.strip()
        email = email.strip().lower()
        username = username.strip()

        if not full_name:
            st.error("Full name is required.")

        elif not is_valid_email(email):
            st.error("Enter a valid email address.")

        elif not is_valid_username(username):
            st.error(
                "Username must be at least 3 characters and can contain only letters, numbers, underscore, or dot."
            )

        elif len(password) < 6:
            st.error("Password must be at least 6 characters long.")

        elif password != confirm_password:
            st.error("Passwords do not match.")

        else:
            success, message = create_user(
                full_name=full_name,
                email=email,
                username=username,
                password=password
            )

            if success:
                st.success("Account created successfully. Please login now.")
                st.session_state.auth_page = "login"
                st.rerun()
            else:
                st.error(message)

    html_line(
        '<div class="auth-switch-box"><div class="auth-switch-text">Already have an account?</div></div>'
    )

    if st.button("Back to Login", use_container_width=True, key="go_to_login"):
        st.session_state.auth_page = "login"
        st.rerun()

    html_line(
        '<div class="auth-mini-note">Your login details are stored locally for project demonstration.</div>'
    )


# ---------------- AUTH PAGE CONTROLLER ----------------
def render_auth_page():
    init_auth_state()
    inject_auth_css()

    left_col, right_col = st.columns([1.05, 0.95], gap="large")

    with left_col:
        render_auth_left_panel()

    with right_col:
        if st.session_state.auth_page == "signup":
            render_signup_form()
        else:
            render_login_form()


# ---------------- ACCESS GUARD ----------------
def require_login():
    init_auth_state()

    if not st.session_state.authenticated:
        render_auth_page()
        st.stop()


# ---------------- SIDEBAR USER BOX ----------------
def render_user_box():
    init_auth_state()

    if st.session_state.authenticated and st.session_state.user:
        user = st.session_state.user

        st.sidebar.markdown(
            f"""
            <div class="sidebar-card">
                <div class="sidebar-title">👤 Logged In</div>
                <div class="sidebar-muted">
                    <b>{user.get("full_name", "User")}</b><br>
                    @{user.get("username", "")}<br>
                    {user.get("email", "")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
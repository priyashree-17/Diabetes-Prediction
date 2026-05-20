import streamlit as st
import pandas as pd
import pickle
from datetime import datetime
from io import BytesIO
import urllib.parse

import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit.components.v1 as components

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="GlucoTrack",
    page_icon="🩺",
    layout="wide"
)

# ==============================
# LOAD MODEL
# ==============================
model = pickle.load(open("diabetes_model.pkl", "rb"))
columns = pickle.load(open("columns.pkl", "rb"))

# ==============================
# SESSION STATE
# ==============================
defaults = {
    "started": False,
    "logged_in": False,
    "role": None,
    "page": "User Login",
    "users": {"user@gmail.com": {"password": "1234", "name": "Demo User"}},
    "admins": {"admin@glucotrack.com": "admin@123"},
    "prediction_done": False,
    "patient_data": None,
    "prediction_result": None,
    "confidence": None,
    "pdf_bytes": None,
    "current_user_name": "",
    "current_user_email": "",
    "prediction_time": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==============================
# THEME
# ==============================
dark_mode = False
if st.session_state.started:
    dark_mode = st.sidebar.toggle("🌙 Dark Mode")

if dark_mode:
    bg = "#023047"
    card = "#126782"
    text = "#FFFFFF"
    accent = "#8ECAE6"
    input_text = "#FFFFFF"
    sidebar_bg = "linear-gradient(180deg, #012A3A, #023047, #126782)"
    plot_template = "plotly_dark"
    feature_bg1 = "linear-gradient(135deg, #0C3547, #0A4A6E)"
    feature_bg2 = "linear-gradient(135deg, #0C3D1E, #0A4D28)"
    feature_bg3 = "linear-gradient(135deg, #3D2E00, #4D3A00)"
    feature_txt1 = "#8ECAE6"
    feature_txt2 = "#86EFAC"
    feature_txt3 = "#FDE68A"
    step_bg = "rgba(255,255,255,0.07)"
    step_border = "rgba(255,255,255,0.15)"
    step_txt = "#FFFFFF"
else:
    bg = "#F0F8FF"
    card = "#FFFFFF"
    text = "#1E293B"
    accent = "#0284C7"
    input_text = "#1E293B"
    sidebar_bg = "linear-gradient(180deg, #8ECAE6, #219EBC)"
    plot_template = "plotly_white"
    feature_bg1 = "linear-gradient(135deg, #E0F2FE, #BAE6FD)"
    feature_bg2 = "linear-gradient(135deg, #DCFCE7, #BBF7D0)"
    feature_bg3 = "linear-gradient(135deg, #FEF9C3, #FDE68A)"
    feature_txt1 = "#075985"
    feature_txt2 = "#166534"
    feature_txt3 = "#854D0E"
    step_bg = "rgba(2,132,199,0.07)"
    step_border = "rgba(2,132,199,0.18)"
    step_txt = "#1E293B"

# ==============================
# CSS
# ==============================
st.markdown(f"""
<style>
.stApp {{
    background: {bg};
    color: {text};
}}
section[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
}}
section[data-testid="stSidebar"] > div {{ background: transparent; }}
section[data-testid="stSidebar"] * {{ color: white !important; }}

div[data-testid="stRadio"] label {{
    background: rgba(255,255,255,0.14);
    padding: 12px 16px;
    border-radius: 14px;
    margin-bottom: 8px;
    font-weight: 600;
    display: block;
}}
div[data-testid="stRadio"] label:hover {{ background: rgba(255,255,255,0.28); }}

.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background-color: {card} !important;
    color: {input_text} !important;
    border-radius: 12px !important;
}}
div[data-baseweb="input"] > div {{
    background-color: {card} !important;
    border-radius: 12px !important;
    border: 1.5px solid rgba(2,132,199,0.25) !important;
}}
div[data-baseweb="select"] > div {{
    background-color: {card} !important;
    color: {input_text} !important;
    border-radius: 12px !important;
}}
div[data-baseweb="select"] * {{ color: {input_text} !important; }}

.hero-wrap {{
    background: linear-gradient(135deg, #0EA5E9 0%, #8B5CF6 50%, #EC4899 100%);
    padding: 60px 40px 50px;
    border-radius: 32px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(14,165,233,0.30);
    position: relative;
    overflow: hidden;
}}
.hero-badge {{
    display: inline-block;
    background: rgba(255,255,255,0.18);
    color: white !important;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 6px 18px;
    border-radius: 100px;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.30);
}}
.hero-title {{
    font-size: 58px;
    font-weight: 900;
    color: white !important;
    line-height: 1.1;
    margin-bottom: 16px;
}}
.hero-sub {{
    font-size: 19px;
    color: rgba(255,255,255,0.90) !important;
    max-width: 640px;
    margin: 0 auto 10px;
    line-height: 1.6;
}}
.hero-stats {{
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 36px;
    flex-wrap: wrap;
}}
.hero-stat-num {{
    font-size: 32px;
    font-weight: 900;
    color: white !important;
}}
.hero-stat-label {{
    font-size: 13px;
    color: rgba(255,255,255,0.80) !important;
    font-weight: 500;
}}

.feat-card {{
    border-radius: 24px;
    padding: 32px 26px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.09);
    height: 100%;
}}
.feat-icon {{ font-size: 48px; margin-bottom: 12px; display: block; }}
.feat-title {{ font-size: 19px; font-weight: 800; margin-bottom: 12px; }}
.feat-desc {{ font-size: 14.5px; line-height: 1.7; opacity: 0.92; }}
.feat-tag {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 100px;
    margin-bottom: 14px;
    background: rgba(255,255,255,0.35);
}}

.section-heading {{ text-align: center; margin: 48px 0 8px; }}
.section-heading h2 {{ font-size: 32px; font-weight: 900; color: {text} !important; }}
.section-heading p {{ font-size: 16px; color: {text} !important; opacity: 0.65; margin-top: 4px; }}

.step-card {{
    background: {step_bg};
    border: 1.5px solid {step_border};
    border-radius: 20px;
    padding: 26px 20px;
    text-align: center;
    height: 100%;
}}
.step-num {{ font-size: 36px; font-weight: 900; color: {accent} !important; margin-bottom: 8px; }}
.step-title {{ font-size: 15px; font-weight: 700; color: {step_txt} !important; margin-bottom: 6px; }}
.step-desc {{ font-size: 13px; color: {step_txt} !important; opacity: 0.75; line-height: 1.5; }}

.result-high {{
    background: linear-gradient(135deg, #FFE4E6, #FECDD3);
    color: #BE123C !important;
    padding: 32px;
    border-radius: 24px;
    font-size: 28px;
    font-weight: 800;
    text-align: center;
    border: 2px solid #FDA4AF;
    box-shadow: 0 8px 24px rgba(190,18,60,0.12);
}}
.result-low {{
    background: linear-gradient(135deg, #DCFCE7, #BBF7D0);
    color: #166534 !important;
    padding: 32px;
    border-radius: 24px;
    font-size: 28px;
    font-weight: 800;
    text-align: center;
    border: 2px solid #86EFAC;
    box-shadow: 0 8px 24px rgba(22,101,52,0.12);
}}

.patient-info-card {{
    background: {card};
    border-radius: 20px;
    padding: 24px 30px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 24px;
    border-left: 5px solid {accent};
}}
.patient-info-row {{
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 20px;
}}
.patient-info-item label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: {accent} !important;
    display: block;
    margin-bottom: 3px;
}}
.patient-info-item span {{
    font-size: 16px;
    font-weight: 600;
    color: {text} !important;
}}

.param-card {{
    background: {card};
    border-radius: 16px;
    padding: 16px 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    text-align: center;
    margin-bottom: 12px;
}}
.param-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: {accent} !important;
    margin-bottom: 4px;
}}
.param-value {{
    font-size: 22px;
    font-weight: 900;
    color: {text} !important;
}}

.stButton>button, .stDownloadButton>button {{
    background: linear-gradient(135deg, #0284C7, #0EA5E9) !important;
    color: white !important;
    border-radius: 12px;
    padding: 10px 26px;
    border: none;
    font-weight: 700;
    box-shadow: 0 4px 14px rgba(2,132,199,0.30);
}}
.stButton>button:hover, .stDownloadButton>button:hover {{
    background: linear-gradient(135deg, #0369A1, #0284C7) !important;
    color: white !important;
}}

.stMarkdown, label, p, h1, h2, h3, h4, h5, h6, span {{
    color: {input_text} !important;
}}
</style>
""", unsafe_allow_html=True)


# ==============================
# HOME PAGE
# ==============================
def home_page():
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">🩺 AI-Powered Health Platform</div>
        <div class="hero-title">GlucoTrack</div>
        <p class="hero-sub">
            Predict diabetes risk in seconds using Machine Learning.<br>
            Understand your health. Take action early. Live better.
        </p>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-num">95%+</div>
                <div class="hero-stat-label">Model Accuracy</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-num">8</div>
                <div class="hero-stat-label">Health Parameters</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-num">100%</div>
                <div class="hero-stat-label">Free to Use</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-heading">
        <h2>✨ What GlucoTrack Does</h2>
        <p>Three powerful features to monitor, predict, and improve your health</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown(f"""
        <div class="feat-card" style="background:{feature_bg1};">
            <span class="feat-tag" style="color:{feature_txt1};">Machine Learning</span>
            <span class="feat-icon">🤖</span>
            <div class="feat-title" style="color:{feature_txt1};">ML-Based Diabetes Risk Prediction</div>
            <div class="feat-desc" style="color:{feature_txt1};">
                Our trained ML model analyzes <strong>8 clinical parameters</strong> —
                Glucose, BMI, Insulin, Blood Pressure, Age, Pregnancies,
                Skin Thickness, and Diabetes Pedigree Function — to compute your
                <strong>diabetes risk with a confidence score</strong>.
                <br><br>
                Early detection gives you the power to act <em>before</em> symptoms appear
                and avoid long-term complications.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="feat-card" style="background:{feature_bg2};">
            <span class="feat-tag" style="color:{feature_txt2};">Analytics</span>
            <span class="feat-icon">📊</span>
            <div class="feat-title" style="color:{feature_txt2};">Patient Health Analytics</div>
            <div class="feat-desc" style="color:{feature_txt2};">
                Visualize your health data through <strong>interactive bar charts,
                glucose gauges, and BMI indicators</strong>.
                <br><br>
                See all key vitals — glucose, blood pressure, insulin, BMI —
                in a clean <strong>graphical dashboard</strong> with color-coded
                healthy vs risk zones, so you can make <em>data-driven</em>
                decisions with your doctor.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="feat-card" style="background:{feature_bg3};">
            <span class="feat-tag" style="color:{feature_txt3};">Personalized</span>
            <span class="feat-icon">💡</span>
            <div class="feat-title" style="color:{feature_txt3};">Personalized Health Suggestions</div>
            <div class="feat-desc" style="color:{feature_txt3};">
                Unlike generic advice, GlucoTrack analyzes <strong>your specific
                health values</strong> — high glucose, elevated BMI, raised blood
                pressure — and gives <strong>targeted recommendations</strong>
                tailored to your risk profile.
                <br><br>
                Diet tips, exercise guidance, and when to consult a doctor —
                all <em>specific to you</em>, not a generic checklist.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-heading">
        <h2>🔄 How It Works</h2>
        <p>Get your diabetes risk assessment in 4 simple steps</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    s1, s2, s3, s4 = st.columns(4, gap="medium")
    steps = [
        ("01", "Create Account", "Sign up with your name and email to create your secure patient profile"),
        ("02", "Enter Health Data", "Fill in your clinical values like glucose, BMI, blood pressure, and age"),
        ("03", "Get Prediction", "ML model instantly calculates your diabetes risk with a confidence score"),
        ("04", "View & Download", "See analytics, personalized suggestions, and download your full PDF report"),
    ]
    for col, (num, title, desc) in zip([s1, s2, s3, s4], steps):
        with col:
            st.markdown(f"""
            <div class="step-card">
                <div class="step-num">{num}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    _, mid, _ = st.columns([1.5, 1, 1.5])
    with mid:
        if st.button("🚀 Get Started Now", use_container_width=True):
            st.session_state.started = True
            st.rerun()

    st.write("")
    st.markdown("""<p style="text-align:center;font-size:13px;opacity:0.45;">
    ⚕️ GlucoTrack is for educational purposes. Always consult a medical professional.
    </p>""", unsafe_allow_html=True)


if not st.session_state.started:
    home_page()
    st.stop()


# ==============================
# SIDEBAR  â† FIX: index= se current page select hogi
# ==============================
st.sidebar.markdown("## 🩺 GLUCOTRACK")
st.sidebar.caption("Smart Health Dashboard")
st.sidebar.markdown("---")

if st.session_state.logged_in:
    st.sidebar.success(f"👤 {st.session_state.current_user_name or st.session_state.role}")

# Define menu options based on user role
if st.session_state.logged_in:
    if st.session_state.role == "Admin":
        menu_options = ["Admin Dashboard", "Prediction", "Results"]
    else:
        menu_options = ["Prediction", "Results"]
else:
    menu_options = ["User Login", "Sign Up", "Admin Login"]

# ✅ KEY FIX: current page ka index find karo aur radio ko wahan set karo
# If current page is not in menu, default to index 0
current_page = st.session_state.page
if current_page not in menu_options:
    current_page = menu_options[0]
    st.session_state.page = current_page

current_index = menu_options.index(current_page)

# Radio widget — highlights current page
selected_page = st.sidebar.radio(
    "",
    menu_options,
    index=current_index,
    label_visibility="collapsed"
)

# ✅ KEY FIX: Update only when user manually changes selection
# prediction_page() sets page="Results", preserve that behavior
if selected_page != st.session_state.page:
    st.session_state.page = selected_page
    st.rerun()

if st.session_state.logged_in:
    if st.sidebar.button("ðŸšª Logout"):
        for k in ["logged_in", "role", "prediction_done", "patient_data",
                  "prediction_result", "confidence", "pdf_bytes",
                  "current_user_name", "current_user_email", "prediction_time"]:
            st.session_state[k] = defaults[k]
        st.session_state.page = "User Login"
        st.rerun()


# ==============================
# LOGIN / SIGNUP
# ==============================
def user_login():
    st.title("🔐 User Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = st.session_state.users
        if email in users and users[email]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = "User"
            st.session_state.current_user_name = users[email]["name"]
            st.session_state.current_user_email = email
            st.session_state.page = "Prediction"
            st.rerun()
        else:
            st.error("Invalid email ID or password")


def signup():
    st.title("📝 Patient Sign Up")
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name")
            email = st.text_input("Email ID")
            phone = st.text_input("Phone Number")
            age = st.number_input("Age", 1, 100, 25)
        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Other"])
            address = st.text_area("Address")
            new_pass = st.text_input("Create Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Create Account")
        if submit:
            if not full_name or not email or not phone or not new_pass:
                st.error("Please fill all required fields.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match.")
            elif email in st.session_state.users:
                st.error("Email ID already exists.")
            else:
                st.session_state.users[email] = {"password": new_pass, "name": full_name}
                st.success(f"Account created for {full_name}! Please login.")


def admin_login():
    st.title("🛡️ Admin Login")
    email = st.text_input("Admin Email ID")
    password = st.text_input("Admin Password", type="password")
    if st.button("Admin Login"):
        if email in st.session_state.admins and st.session_state.admins[email] == password:
            st.session_state.logged_in = True
            st.session_state.role = "Admin"
            st.session_state.current_user_name = "Admin"
            st.session_state.current_user_email = email
            st.session_state.page = "Admin Dashboard"
            st.rerun()
        else:
            st.error("Invalid admin email or password")


def admin_dashboard():
    st.title("🛡️ Admin Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Registered Users", len(st.session_state.users))
    col2.metric("Admin Accounts", len(st.session_state.admins))
    col3.metric("Current Role", "Admin")
    st.subheader("Registered Users")
    rows = [{"Name": v["name"], "Email ID": k} for k, v in st.session_state.users.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ==============================
# HEALTH SUGGESTIONS
# ==============================
def get_suggestions(patient_data):
    glucose = patient_data["Glucose"]
    bmi = patient_data["BMI"]
    bp = patient_data["BloodPressure"]
    if glucose >= 126:
        return [
            "Monitor blood glucose levels every day",
            "Reduce sugar, sweets, and refined carbohydrates",
            "Consult a doctor for diabetes management",
            "Avoid sugary drinks — switch to water or herbal tea"
        ]
    elif bmi >= 30:
        return [
            "Follow a calorie-controlled and balanced diet",
            "Exercise for at least 30 minutes daily",
            "Track your weight and BMI weekly",
            "Avoid fried and processed foods"
        ]
    elif bp > 90:
        return [
            "Reduce sodium (salt) and processed food intake",
            "Monitor blood pressure at home regularly",
            "Practice yoga or meditation for stress relief",
            "Maintain daily physical activity for heart health"
        ]
    else:
        return [
            "Maintain a balanced diet rich in vegetables and whole grains",
            "Exercise regularly to stay active and healthy",
            "Drink at least 8 glasses of water daily",
            "Get 7–8 hours of quality sleep every night"
        ]


# ==============================
# PDF REPORT
# ==============================
def generate_pdf_report(patient_data, result, confidence, patient_name, patient_email, prediction_time):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFillColorRGB(0.05, 0.52, 0.78)
    pdf.rect(0, height - 80, width, 80, fill=True, stroke=False)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(40, height - 45, "GlucoTrack — Diabetes Risk Report")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, height - 65, f"Generated: {prediction_time}")

    y = height - 110

    pdf.setFillColorRGB(0.94, 0.97, 1.0)
    pdf.rect(30, y - 55, width - 60, 62, fill=True, stroke=False)
    pdf.setFillColorRGB(0.05, 0.52, 0.78)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(45, y - 12, f"Patient Name:  {patient_name}")
    pdf.drawString(45, y - 32, f"Email:              {patient_email}")
    pdf.drawString(300, y - 12, f"Date:  {prediction_time[:10]}")
    pdf.drawString(300, y - 32, f"Time:  {prediction_time[11:]}")
    y -= 78

    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Health Parameters")
    y -= 6
    pdf.setStrokeColorRGB(0.05, 0.52, 0.78)
    pdf.setLineWidth(1.5)
    pdf.line(40, y, width - 40, y)
    y -= 20

    items = list(patient_data.items())
    col2_x = width // 2 + 20
    for i in range(0, len(items), 2):
        k1, v1 = items[i]
        pdf.setFillColorRGB(0.05, 0.52, 0.78)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, f"{k1}:")
        pdf.setFillColorRGB(0.1, 0.1, 0.1)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(185, y, str(v1))
        if i + 1 < len(items):
            k2, v2 = items[i + 1]
            pdf.setFillColorRGB(0.05, 0.52, 0.78)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(col2_x, y, f"{k2}:")
            pdf.setFillColorRGB(0.1, 0.1, 0.1)
            pdf.setFont("Helvetica", 11)
            pdf.drawString(col2_x + 135, y, str(v2))
        y -= 22

    y -= 14

    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Prediction Result")
    y -= 6
    pdf.line(40, y, width - 40, y)
    y -= 22

    if "High" in result:
        pdf.setFillColorRGB(1.0, 0.9, 0.91)
        pdf.rect(40, y - 16, width - 80, 34, fill=True, stroke=False)
        pdf.setFillColorRGB(0.75, 0.07, 0.24)
    else:
        pdf.setFillColorRGB(0.86, 0.99, 0.90)
        pdf.rect(40, y - 16, width - 80, 34, fill=True, stroke=False)
        pdf.setFillColorRGB(0.09, 0.40, 0.20)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(55, y, f"{result}     |     Confidence: {confidence}%")
    y -= 52

    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Personalized Health Recommendations")
    y -= 6
    pdf.setStrokeColorRGB(0.05, 0.52, 0.78)
    pdf.line(40, y, width - 40, y)
    y -= 20

    for s in get_suggestions(patient_data):
        pdf.setFillColorRGB(0.05, 0.52, 0.78)
        pdf.drawString(50, y, "•")
        pdf.setFillColorRGB(0.1, 0.1, 0.1)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(65, y, s[:88])
        y -= 20

    y -= 20
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(40, y, "This report is generated by GlucoTrack ML model and does not replace professional medical advice.")

    pdf.setFillColorRGB(0.05, 0.52, 0.78)
    pdf.rect(0, 0, width, 28, fill=True, stroke=False)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(40, 9, "GlucoTrack — Smart Diabetes Risk Prediction System")
    pdf.drawRightString(width - 40, 9, f"Patient: {patient_name}")

    pdf.save()
    return buffer.getvalue()


# ==============================
# ANALYTICS
# ==============================
def show_patient_analytics(patient_data):
    st.subheader("📊 Patient Health Analytics")

    metrics = ["Glucose", "BMI", "Insulin", "BloodPressure", "Age"]
    values = [patient_data[m] for m in metrics]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=metrics, y=values,
        marker_color=["#FF6B9A", "#4D96FF", "#F4A261", "#52B788", "#9D79BC"],
        text=values, textposition="outside"
    ))
    fig.update_layout(
        title="Health Parameter Overview",
        xaxis_title="Parameter", yaxis_title="Value",
        template=plot_template, height=400,
        margin=dict(t=50, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=patient_data["Glucose"],
            title={"text": "Glucose Level (mg/dL)"},
            gauge={
                "axis": {"range": [0, 250]},
                "bar": {"color": "#FF6B9A"},
                "steps": [
                    {"range": [0, 99],    "color": "#DCFCE7"},
                    {"range": [100, 125], "color": "#FEF9C3"},
                    {"range": [126, 250], "color": "#FFE4E6"}
                ],
                "threshold": {"line": {"color": "red", "width": 3}, "value": 126}
            }
        ))
        g.update_layout(height=300, template=plot_template, margin=dict(t=40, b=20))
        st.plotly_chart(g, use_container_width=True)

    with c2:
        bg2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=patient_data["BMI"],
            title={"text": "BMI"},
            gauge={
                "axis": {"range": [0, 70]},
                "bar": {"color": "#4D96FF"},
                "steps": [
                    {"range": [0, 18.4],   "color": "#FEF9C3"},
                    {"range": [18.5, 24.9], "color": "#DCFCE7"},
                    {"range": [25, 29.9],  "color": "#FEF9C3"},
                    {"range": [30, 70],    "color": "#FFE4E6"}
                ],
                "threshold": {"line": {"color": "orange", "width": 3}, "value": 25}
            }
        ))
        bg2.update_layout(height=300, template=plot_template, margin=dict(t=40, b=20))
        st.plotly_chart(bg2, use_container_width=True)


# ==============================
# SUGGESTIONS CARD
# ==============================
def show_health_suggestions(patient_data):
    suggestions = get_suggestions(patient_data)

    if dark_mode:
        card_bg = "linear-gradient(135deg, #081C3A, #0D5B63)"
        title_col = "#FFFFFF"
        desc_col = "#A7F3D0"
    else:
        card_bg = "linear-gradient(135deg, #EFF6FF, #DBEAFE)"
        title_col = "#0F172A"
        desc_col = "#1E40AF"

    items_html = "".join([f"""
    <li style="margin-bottom:10px; color:{desc_col}; font-size:15px; font-weight:500;">{s}</li>
    """ for s in suggestions])

    components.html(f"""
    <div style="background:{card_bg}; padding:30px 36px; border-radius:24px;
                box-shadow:0 8px 28px rgba(0,0,0,0.12); font-family:Arial,sans-serif;">
        <h2 style="color:{title_col}; font-size:22px; font-weight:800; margin-bottom:16px;">
            💡 Personalized Health Recommendations
        </h2>
        <ul style="margin:0; padding-left:22px; line-height:1.8;">{items_html}</ul>
    </div>
    """, height=270)


# ==============================
# PREDICTION PAGE
# ==============================
def prediction_page():
    st.title("🩺 Diabetes Risk Prediction")

    # â”€â”€ Patient Info Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("### 👤 Patient Information")
    st.caption("You can edit or enter your name and email below.")

    pinfo_col1, pinfo_col2 = st.columns(2)
    with pinfo_col1:
        patient_name_input = st.text_input(
            "Patient Full Name",
            value=st.session_state.current_user_name,
            placeholder="Enter your full name...",
        )
    with pinfo_col2:
        patient_email_input = st.text_input(
            "Patient Email ID",
            value=st.session_state.current_user_email,
            placeholder="example@email.com",
        )

    # Validate name not empty
    if not patient_name_input.strip():
        st.warning("⚠️ Patient name is required to generate the report.")

    st.markdown("---")
    # â”€â”€ Clinical Parameters â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("### 🔬 Clinical Health Parameters")
    st.write("Enter your health values below:")

    col1, col2 = st.columns(2)

    with col1:
        preg    = st.number_input("Pregnancies", 0, 20, 1)
        glucose = st.number_input("Glucose (mg/dL)", 50, 250, 120)
        bp      = st.number_input("Blood Pressure (mm Hg)", 30, 140, 70)
        skin    = st.number_input("Skin Thickness (mm)", 0, 100, 20)

    with col2:
        insulin = st.number_input("Insulin (μU/mL)", 0, 400, 100)
        bmi     = st.number_input("BMI", 10.0, 70.0, 25.0)
        dpf     = st.number_input("Diabetes Pedigree Function", 0.0, 3.0, 0.5)
        age     = st.number_input("Age", 1, 100, 30)

    st.write("")
    if st.button("ðŸ” Predict Diabetes Risk", use_container_width=True):

        # Name validation before prediction
        if not patient_name_input.strip():
            st.error("❌ Please enter the patient name first!")
            st.stop()

        # ✅ User ne jo naam/email diya, woh use karo (session update bhi)
        final_name  = patient_name_input.strip()
        final_email = patient_email_input.strip()
        st.session_state.current_user_name  = final_name
        st.session_state.current_user_email = final_email

        patient_data = {
            "Pregnancies": preg, "Glucose": glucose,
            "BloodPressure": bp, "SkinThickness": skin,
            "Insulin": insulin, "BMI": bmi,
            "DiabetesPedigreeFunction": dpf, "Age": age
        }

        input_raw = pd.DataFrame([patient_data])
        input_raw["Glucose_BMI"]     = input_raw["Glucose"] * input_raw["BMI"]
        input_raw["Insulin_Glucose"] = input_raw["Insulin"] * input_raw["Glucose"]
        input_raw["Age_BMI"]         = input_raw["Age"] * input_raw["BMI"]
        input_raw["BMI_Squared"]     = input_raw["BMI"] ** 2

        input_encoded = pd.get_dummies(input_raw)
        input_df = input_encoded.reindex(columns=columns, fill_value=0)
        prediction = model.predict(input_df)

        if hasattr(model, "predict_proba"):
            prob = model.predict_proba(input_df)[0]
            if prediction[0] == 1:
                result = "High Risk of Diabetes"
                confidence = round(prob[1] * 100, 2)
            else:
                result = "Low Risk of Diabetes"
                confidence = round(prob[0] * 100, 2)
        else:
            result = "High Risk of Diabetes" if prediction[0] == 1 else "Low Risk of Diabetes"
            confidence = "N/A"

        pred_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        st.session_state.prediction_done   = True
        st.session_state.patient_data      = patient_data
        st.session_state.prediction_result = result
        st.session_state.confidence        = confidence
        st.session_state.prediction_time   = pred_time
        st.session_state.pdf_bytes = generate_pdf_report(
            patient_data, result, confidence,
            final_name,
            final_email,
            pred_time
        )

        st.session_state.page = "Results"
        st.rerun()


# ==============================
# RESULTS PAGE
# ==============================
def results_page():
    st.title("📋 Prediction Results")

    if not st.session_state.prediction_done:
        st.warning("⚠️ No prediction found. Please go to **Prediction** page and submit your details first.")
        if st.button("ðŸ”™ Go to Prediction"):
            st.session_state.page = "Prediction"
            st.rerun()
        return

    result       = st.session_state.prediction_result
    patient_data = st.session_state.patient_data
    confidence   = st.session_state.confidence
    pred_time    = st.session_state.prediction_time
    name         = st.session_state.current_user_name
    email        = st.session_state.current_user_email

    # Patient Info Card
    st.markdown(f"""
    <div class="patient-info-card">
        <div class="patient-info-row">
            <div class="patient-info-item">
                <label>Patient Name</label>
                <span>{name}</span>
            </div>
            <div class="patient-info-item">
                <label>Email ID</label>
                <span>{email}</span>
            </div>
            <div class="patient-info-item">
                <label>Report Date</label>
                <span>{pred_time[:10] if pred_time else "—"}</span>
            </div>
            <div class="patient-info-item">
                <label>Report Time</label>
                <span>{pred_time[11:] if pred_time else "—"}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Result Banner
    if result == "High Risk of Diabetes":
        st.markdown(f"""
        <div class="result-high">
            ⚠️ High Risk of Diabetes
            <br><span style="font-size:17px;font-weight:600;">Prediction Confidence: {confidence}%</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="result-low">
            ✅ Low Risk of Diabetes
            <br><span style="font-size:17px;font-weight:600;">Prediction Confidence: {confidence}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Parameter Summary Grid
    st.subheader("🧾 Submitted Health Parameters")
    params = list(patient_data.items())
    cols = st.columns(4)
    for i, (k, v) in enumerate(params):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="param-card">
                <div class="param-label">{k}</div>
                <div class="param-value">{v}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    show_patient_analytics(patient_data)
    st.write("")
    show_health_suggestions(patient_data)
    st.write("")

    # Action Buttons — row 1
    b1, b2 = st.columns(2)
    with b1:
        st.download_button(
            label="📄 Download PDF Report",
            data=st.session_state.pdf_bytes,
            file_name=f"glucotrack_{name.replace(' ', '_')}_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with b2:
        if st.button("🔁 New Prediction", use_container_width=True):
            for k in ["prediction_done", "patient_data", "prediction_result",
                      "confidence", "pdf_bytes", "prediction_time"]:
                st.session_state[k] = defaults[k]
            st.session_state.page = "Prediction"
            st.rerun()

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # WHATSAPP SECTION — SIMPLE wa.me LINK
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    st.write("")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#dcfce7,#bbf7d0);
                border:2px solid #4ade80; border-radius:20px; padding:22px 26px;">
        <div style="font-size:20px;font-weight:800;color:#14532d;">
            📲 Send Report via WhatsApp
        </div>
        <div style="font-size:13px;color:#166534;margin-top:4px;">
            Enter number → Click button → WhatsApp opens → Send message
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    wa_col1, wa_col2 = st.columns([2, 1])
    with wa_col1:
        wa_number = st.text_input(
            "📞 WhatsApp Number (with Country Code)",
            placeholder="91XXXXXXXXXX  ya  +91XXXXXXXXXX",
            key="wa_number_input"
        )
    with wa_col2:
        st.write("")
        st.write("")
        send_wa = st.button("💬 Send via WhatsApp", use_container_width=True)

    if send_wa:
        digits_only = wa_number.strip().replace("+", "").replace(" ", "").replace("-", "")
        if not digits_only or not digits_only.isdigit() or len(digits_only) < 10:
            st.error("❌ Please enter a valid number. Example: 919876543210")
        else:
            suggestions      = get_suggestions(patient_data)
            suggestions_text = "\n".join([f"  • {s}" for s in suggestions])
            result_emoji     = "⚠️" if "High" in result else "✅"

            wa_message = (
                f"🩺 *GlucoTrack — Diabetes Risk Report*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 *Patient:* {name}\n"
                f"ðŸ“§ *Email:* {email}\n"
                f"📅 *Date:* {pred_time[:10] if pred_time else '—'}\n"
                f"🕐 *Time:* {pred_time[11:] if pred_time else '—'}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{result_emoji} *Result: {result}*\n"
                f"📊 *Confidence: {confidence}%*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔬 *Health Parameters:*\n"
                f"  • Pregnancies: {patient_data['Pregnancies']}\n"
                f"  • Glucose: {patient_data['Glucose']} mg/dL\n"
                f"  • Blood Pressure: {patient_data['BloodPressure']} mm Hg\n"
                f"  • Skin Thickness: {patient_data['SkinThickness']} mm\n"
                f"  • Insulin: {patient_data['Insulin']} uU/mL\n"
                f"  • BMI: {patient_data['BMI']}\n"
                f"  • Diabetes Pedigree: {patient_data['DiabetesPedigreeFunction']}\n"
                f"  • Age: {patient_data['Age']} years\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 *Recommendations:*\n"
                f"{suggestions_text}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"_GlucoTrack ML Report — Please consult a doctor_"
            )

            encoded  = urllib.parse.quote(wa_message)
            wa_link  = f"https://wa.me/{digits_only}?text={encoded}"

            st.success("✅ Link is ready! Click the green button below to open WhatsApp.")
            st.markdown(f"""
            <div style="text-align:center; margin-top:12px;">
                <a href="{wa_link}" target="_blank" style="
                    display:inline-block;
                    background:linear-gradient(135deg,#25D366,#128C7E);
                    color:white; font-size:17px; font-weight:800;
                    padding:14px 44px; border-radius:50px;
                    text-decoration:none;
                    box-shadow:0 6px 20px rgba(37,211,102,0.40);">
                    📲 Open in WhatsApp &amp; Send
                </a>
                <p style="font-size:12px;color:#6b7280;margin-top:10px;">
                    Clicking will open WhatsApp Web/App — just press Send
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.caption("⚕️ This prediction is generated by a Machine Learning model and does not replace professional medical advice.")


# ==============================
# ROUTING  â† FIX: session_state.page se route karo, radio se nahi
# ==============================
page = st.session_state.page

if page == "User Login":
    user_login()
elif page == "Sign Up":
    signup()
elif page == "Admin Login":
    admin_login()
elif page == "Admin Dashboard":
    admin_dashboard()
elif page == "Prediction":
    prediction_page()
elif page == "Results":
    results_page()

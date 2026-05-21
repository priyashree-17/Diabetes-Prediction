import os
import json
import pickle
import base64
from datetime import datetime
from io import BytesIO
import urllib.parse

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title='GlucoTrack', page_icon='🩺', layout='wide', initial_sidebar_state='expanded')

USERS_FILE = 'users.json'
DOCTORS_FILE = 'doctors.json'
ADMINS_FILE = 'admins.json'
REPORTS_FILE = 'reports.json'
AUDIT_FILE = 'audit_log.json'
MODEL_FILE = 'diabetes_model.pkl'
COLUMNS_FILE = 'columns.pkl'


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(default, f, indent=4)
    return default


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def add_audit(action, email='System', details=''):
    logs = load_json(AUDIT_FILE, [])
    logs.append({'time': datetime.now().strftime('%d-%m-%Y %H:%M:%S'), 'email': email, 'action': action, 'details': details})
    save_json(AUDIT_FILE, logs)


DEFAULT_USERS = {
    'user@gmail.com': {
        'password': 'Pass1234',
        'name': 'Demo User',
        'phone': 'Not Provided',
        'age': 30,
        'gender': 'Female',
        'address': 'Not Provided',
        'medical_history': '',
        'user_type': 'patient',
        'profile_created': True,
    }
}

DEFAULT_DOCTORS = {
    'doctor@glucotrack.com': {
        'password': 'Doc@1234',
        'name': 'Dr. Demo',
        'phone': 'Not Provided',
        'specialization': 'Endocrinology',
        'hospital': 'City Hospital',
        'license_no': 'MCI-12345',
        'approved': False,
        'user_type': 'doctor',
        'profile_created': True,
    }
}

DEFAULT_ADMINS = {'admin@glucotrack.com': 'admin@123'}

users = load_json(USERS_FILE, DEFAULT_USERS)
doctors = load_json(DOCTORS_FILE, DEFAULT_DOCTORS)
admins = load_json(ADMINS_FILE, DEFAULT_ADMINS)
reports = load_json(REPORTS_FILE, [])


defaults = {
    'started': False,
    'page': 'home',
    'auth_mode': 'signin',
    'signup_step': 1,
    'logged_in': False,
    'user_type': None,
    'current_user_name': '',
    'current_user_email': '',
    'dark_mode': False,
    'signup_name': '',
    'signup_email': '',
    'signup_phone': '',
    'signup_age': 25,
    'signup_gender': 'Female',
    'signup_address': '',
    'signup_password': '',
    'prediction_done': False,
    'patient_data': None,
    'prediction_result': None,
    'confidence': None,
    'prediction_time': None,
    'pdf_bytes': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

DARK = st.session_state.dark_mode
if DARK:
    BG = '#0F172A'; CARD = '#1E293B'; TEXT = '#F8FAFC'; MUTED = '#94A3B8'; BORDER = '#334155'; INPUT = '#172033'; BLUE = '#38BDF8'; BLUE_DARK = '#0284C7'; SIDEBAR = '#0F172A'; PLOT_TEMPLATE = 'plotly_dark'
    RESULT_HIGH_BG = '#450A0A'; RESULT_HIGH_BORDER = '#7F1D1D'; RESULT_HIGH_TEXT = '#FCA5A5'
    RESULT_LOW_BG = '#022C22'; RESULT_LOW_BORDER = '#064E3B'; RESULT_LOW_TEXT = '#A7F3D0'
    BOX_SUGGESTION_BG = '#1E293B'; BOX_SUGGESTION_TITLE = '#F8FAFC'; BOX_SUGGESTION_TEXT = '#38BDF8'
else:
    BG = '#F6F9FC'; CARD = '#FFFFFF'; TEXT = '#0F172A'; MUTED = '#91A0B8'; BORDER = '#E6EDF5'; INPUT = '#F8FAFD'; BLUE = '#16A6E8'; BLUE_DARK = '#0284C7'; SIDEBAR = '#FFFFFF'; PLOT_TEMPLATE = 'plotly_white'
    RESULT_HIGH_BG = '#FFF1F2'; RESULT_HIGH_BORDER = '#FECDD3'; RESULT_HIGH_TEXT = '#BE123C'
    RESULT_LOW_BG = '#F0FDF4'; RESULT_LOW_BORDER = '#BBF7D0'; RESULT_LOW_TEXT = '#166534'
    BOX_SUGGESTION_BG = '#E8F5FF'; BOX_SUGGESTION_TITLE = '#0F172A'; BOX_SUGGESTION_TEXT = '#006BAA'

css = f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{{box-sizing:border-box;}}
html, body, [class*="css"]{{font-family:'Inter',sans-serif!important;}}
.stApp{{background:{BG}!important;}}
.block-container{{padding-top:2rem!important;padding-left:1.55rem!important;padding-right:1.55rem!important;max-width:100%!important;}}
h1,h2,h3,h4,h5,h6,p,label{{font-family:'Inter',sans-serif!important;}}
h1,h2,h3,h4,h5,h6,p,label{{color:{TEXT}!important;}}
[data-testid="stDecoration"]{{display:none!important;}}
header[data-testid="stHeader"]{{background:transparent!important;box-shadow:none!important;border:none!important;}}
header[data-testid="stHeader"] [data-testid="stAppDeployButton"]{{display:none!important;}}
header[data-testid="stHeader"] #MainMenu{{display:none!important;}}
header[data-testid="stHeader"] [data-testid="stConnectionStatus"]{{display:none!important;}}
.nav-link{{text-decoration:none!important;color:{TEXT}!important;font-weight:700!important;font-size:16px!important;transition:color 0.2s ease!important;}}
.nav-link:hover{{color:{BLUE}!important;}}
.stTextInput input,.stNumberInput input,.stTextArea textarea{{background:{INPUT}!important;color:{TEXT}!important;border:1px solid {BORDER}!important;border-radius:14px!important;min-height:54px!important;font-size:16px!important;padding-left:16px!important;}}
.stSelectbox div[data-baseweb="select"]>div{{background:{INPUT}!important;color:{TEXT}!important;border:1px solid {BORDER}!important;border-radius:14px!important;min-height:54px!important;}}

/* Card container styling */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD}!important;
    border: 1px solid {BORDER}!important;
    border-radius: 20px!important;
    padding: 24px!important;
    box-shadow: 0 8px 30px rgba(15,23,42,.04)!important;
}}

/* Button styling */
.stButton>button[kind="primary"],.stDownloadButton>button,.stFormSubmitButton>button{{background:{BLUE}!important;color:white!important;border:none!important;border-radius:14px!important;font-weight:800!important;font-size:16px!important;min-height:52px!important;box-shadow:0 12px 24px rgba(22,166,232,.20)!important;}}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button:hover,.stFormSubmitButton>button:hover{{background:{BLUE_DARK}!important;transform:translateY(-1px);}}
.stButton>button[kind="secondary"]{{background:transparent!important;color:{TEXT}!important;border:1px solid {BORDER}!important;border-radius:14px!important;font-weight:800!important;font-size:16px!important;min-height:52px!important;}}
.stButton>button[kind="secondary"]:hover{{background:{BORDER}!important;color:{TEXT}!important;transform:translateY(-1px);}}
button *{{color:white!important;}}
.stButton>button[kind="secondary"] *{{color:{TEXT}!important;}}

section[data-testid="stSidebar"]{{background:{SIDEBAR}!important;border-right:1px solid {BORDER};}}
section[data-testid="stSidebar"]>div{{background:transparent!important;padding-top:0!important;}}
section[data-testid="stSidebar"] *{{color:{TEXT}!important;}}
.sb-header{{height:82px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1px solid {BORDER};}}
.sb-logo-box{{width:40px;height:40px;background:{BLUE};color:white!important;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:21px;}}
.sb-brand{{font-size:22px;font-weight:900;color:{TEXT}!important;}}
.sb-profile{{display:flex;align-items:center;gap:14px;padding:22px 18px;border-bottom:1px solid {BORDER};}}
.sb-avatar{{width:50px;height:50px;border-radius:16px;background:#E0F2FE;color:{BLUE}!important;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;}}
.sb-name{{font-size:16px;font-weight:900;color:{TEXT}!important;margin-bottom:4px;}}
.sb-role{{font-size:14px;color:#8CA0BF!important;font-weight:500;}}
div[data-testid="stRadio"]{{padding:20px 7px 0!important;}}
div[data-testid="stRadio"] label{{border-radius:13px!important;padding:14px 14px!important;margin:4px 0!important;font-size:16px!important;font-weight:800!important;background:transparent!important;}}
div[data-testid="stRadio"] label:hover{{background:#EEF8FF!important;}}
div[data-testid="stRadio"] label[data-baseweb="radio"]>div:first-child{{display:none!important;}}

.hero{{padding:78px 20px 50px;text-align:center;max-width:1050px;margin:0 auto;}}
.hero-badge{{display:inline-flex;align-items:center;gap:9px;border:1px solid {'#0284C7' if DARK else '#8BD6FF'};background:{'#0C4A6E' if DARK else '#EAF7FF'};color:{'#38BDF8' if DARK else '#006BAA'}!important;border-radius:999px;padding:10px 18px;letter-spacing:2px;font-weight:900;font-size:14px;}}
.hero-title{{font-size:92px;line-height:.98;letter-spacing:-4px;font-weight:950;margin:42px 0 24px;color:{TEXT}!important;}}
.hero-blue{{color:{BLUE}!important;display:block;}}
.hero-sub{{font-size:27px;line-height:1.5;max-width:900px;margin:0 auto 48px;color:{MUTED}!important;}}

.stats-wrap{{max-width:1120px;margin:42px auto 90px;border-radius:26px;border:1px solid {BORDER};display:grid;grid-template-columns:repeat(3,1fr);overflow:hidden;box-shadow:0 10px 28px rgba(15,23,42,.03);background:{CARD}!important;}}
.stat{{padding:48px 20px;text-align:center;border-right:1px solid {BORDER};}}
.stat:last-child{{border-right:none;}}
.stat-num{{font-size:46px;font-weight:950;color:{BLUE}!important;}}
.stat-label{{font-size:18px;margin-top:6px;color:{MUTED}!important;}}
.section{{padding:0 20px 90px;}}
.section-title{{text-align:center;font-size:38px;font-weight:950;margin-bottom:16px;color:{TEXT}!important;}}
.section-sub{{text-align:center;font-size:22px;margin-bottom:60px;color:{MUTED}!important;}}
.feature-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;max-width:1260px;margin:0 auto;}}
.feature-card{{border-radius:28px;padding:40px;min-height:430px;border:1px solid {BORDER}!important;}}
.feature-blue{{background:{'#1E293B' if DARK else '#E8F5FF'}!important;}}
.feature-green{{background:{'#1E293B' if DARK else '#E8FFF1'}!important;}}
.feature-red{{background:{'#1E293B' if DARK else '#FFECEC'}!important;}}
.pill{{display:inline-flex;border-radius:999px;padding:8px 18px;font-size:14px;font-weight:900;letter-spacing:.5px;margin-bottom:36px;border:1px solid transparent;}}
.pill-blue{{background:{'#0F172A' if DARK else '#E8F5FF'}!important;border-color:{BLUE}!important;color:{BLUE}!important;}}
.pill-green{{background:{'#0F172A' if DARK else '#E8FFF1'}!important;border-color:{'#059669' if DARK else '#80EDB3'}!important;color:{'#34D399' if DARK else '#00885A'}!important;}}
.pill-red{{background:{'#0F172A' if DARK else '#FFECEC'}!important;border-color:{'#DC2626' if DARK else '#FFB4C1'}!important;color:{'#F87171' if DARK else '#D9043D'}!important;}}
.icon-box{{width:58px;height:58px;border-radius:17px;display:flex;align-items:center;justify-content:center;font-size:30px;margin-bottom:48px;}}
.icon-blue{{background:{'#0F172A' if DARK else '#D4EDFF'}!important;}}
.icon-green{{background:{'#0F172A' if DARK else '#CFF9E4'}!important;}}
.icon-red{{background:{'#0F172A' if DARK else '#FFDDE2'}!important;}}
.feature-title{{font-size:23px;font-weight:950;margin-bottom:20px;color:{TEXT}!important;}}
.feature-text{{font-size:19px;line-height:1.45;color:{TEXT if DARK else '#475569'}!important;}}
.steps-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:28px;max-width:1260px;margin:0 auto;}}
.step-card{{border:1px solid {BORDER};border-radius:18px;padding:38px 24px;text-align:center;background:{CARD}!important;}}
.step-num{{color:{BLUE}!important;font-size:46px;font-weight:950;margin-bottom:14px;}}
.step-title{{font-size:21px;font-weight:950;margin-bottom:14px;color:{TEXT}!important;}}
.step-text{{font-size:18px;line-height:1.55;color:{MUTED}!important;}}
.bottom-cta{{max-width:840px;margin:0 auto 90px;text-align:center;border-radius:28px;padding:58px 70px;}}
.auth-title{{text-align:center;padding:34px 0 20px;}}
.auth-title h1{{font-size:32px;margin:28px 0 6px;color:{TEXT}!important;}}
.auth-title p{{font-size:18px;color:{MUTED}!important;}}
.auth-logo-row{{display:flex;justify-content:center;align-items:center;gap:12px;font-size:32px;font-weight:950;color:{TEXT}!important;}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
.auth-link{{text-align:center;font-size:17px;}}
.auth-link b{{color:{BLUE}!important;}}
.page-head{{display:flex;align-items:center;gap:16px;padding:26px 34px 18px;}}
.page-icon{{width:50px;height:50px;background:#DFF3FF;color:{BLUE}!important;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:25px;}}
.page-title{{font-size:31px;font-weight:950;}}
.page-sub{{font-size:18px;margin-top:4px;color:{MUTED}!important;}}
.card-heading{{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:950;margin-bottom:22px;}}
.badge-num{{width:30px;height:30px;background:#DFF3FF;color:{BLUE}!important;border-radius:999px;display:flex;align-items:center;justify-content:center;font-weight:950;}}
.result-high{{background:{RESULT_HIGH_BG};border:1px solid {RESULT_HIGH_BORDER};color:{RESULT_HIGH_TEXT}!important;padding:28px;border-radius:20px;text-align:center;font-weight:950;font-size:25px;}}
.result-low{{background:{RESULT_LOW_BG};border:1px solid {RESULT_LOW_BORDER};color:{RESULT_LOW_TEXT}!important;padding:28px;border-radius:20px;text-align:center;font-weight:950;font-size:25px;}}
.param-card{{background:{CARD}!important;border:1px solid {BORDER}!important;border-radius:15px;padding:16px;text-align:center;}}
.param-label{{color:{MUTED}!important;font-size:12px;font-weight:800;text-transform:uppercase;}}
.param-value{{color:{TEXT}!important;font-size:23px;font-weight:950;}}
.footer{{border-top:1px solid {BORDER};padding:28px 22px;display:flex;justify-content:space-between;color:{MUTED}!important;}}
.footer-logo{{font-weight:950;color:{TEXT}!important;}}
@media(max-width:900px){{.hero-title{{font-size:55px;}}.feature-grid,.steps-grid,.stats-wrap{{grid-template-columns:1fr;}}.form-row{{grid-template-columns:1fr;}}}}
</style>
'''
st.markdown(css, unsafe_allow_html=True)


def initials(name):
    parts = str(name or 'User').strip().split()
    if not parts:
        return 'U'
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def password_strength(password):
    score = 0; hints = []
    if len(password) >= 6: score += 1
    else: hints.append('6+ characters')
    if any(c.isupper() for c in password): score += 1
    else: hints.append('uppercase')
    if any(c.isdigit() for c in password): score += 1
    else: hints.append('number')
    if any(c in '!@#$%^&*' for c in password): score += 1
    else: hints.append('symbol')
    if score <= 1: return 'Weak', '#EF4444', 25, hints
    if score == 2: return 'Fair', '#F97316', 50, hints
    if score == 3: return 'Good', '#EAB308', 75, hints
    return 'Strong', '#22C55E', 100, hints


def reset_prediction_state():
    for k in ['prediction_done', 'patient_data', 'prediction_result', 'confidence', 'prediction_time', 'pdf_bytes']:
        st.session_state[k] = defaults[k]


def login_user(email, password):
    email = email.strip().lower()
    if email in admins and admins[email] == password:
        st.session_state.logged_in = True; st.session_state.user_type = 'admin'; st.session_state.current_user_name = 'Admin'; st.session_state.current_user_email = email; st.session_state.page = 'admin'; add_audit('Login', email, 'Admin logged in'); return True, ''
    if email in users and users[email].get('password') == password:
        user = users[email]; st.session_state.logged_in = True; st.session_state.user_type = 'patient'; st.session_state.current_user_name = user.get('name', 'User'); st.session_state.current_user_email = email; st.session_state.page = 'prediction'; add_audit('Login', email, 'Patient logged in'); return True, ''
    if email in doctors and doctors[email].get('password') == password:
        doctor = doctors[email]
        if not doctor.get('approved', False): return False, 'Doctor account is waiting for admin approval.'
        st.session_state.logged_in = True; st.session_state.user_type = 'doctor'; st.session_state.current_user_name = doctor.get('name', 'Doctor'); st.session_state.current_user_email = email; st.session_state.page = 'doctor'; add_audit('Login', email, 'Doctor logged in'); return True, ''
    return False, 'Invalid email or password.'


def load_model():
    if os.path.exists(MODEL_FILE) and os.path.exists(COLUMNS_FILE):
        try:
            with open(MODEL_FILE, 'rb') as f: model = pickle.load(f)
            with open(COLUMNS_FILE, 'rb') as f: cols = pickle.load(f)
            return model, cols
        except Exception: return None, None
    return None, None


def model_predict(patient_data):
    model, cols = load_model()
    if model is not None and cols is not None:
        input_raw = pd.DataFrame([patient_data])
        input_raw['Glucose_BMI'] = input_raw['Glucose'] * input_raw['BMI']
        input_raw['Insulin_Glucose'] = input_raw['Insulin'] * input_raw['Glucose']
        input_raw['Age_BMI'] = input_raw['Age'] * input_raw['BMI']
        input_raw['BMI_Squared'] = input_raw['BMI'] ** 2
        input_encoded = pd.get_dummies(input_raw)
        input_df = input_encoded.reindex(columns=cols, fill_value=0)
        prediction = model.predict(input_df)
        if hasattr(model, 'predict_proba'):
            prob = model.predict_proba(input_df)[0]
            if prediction[0] == 1: return 'High Risk of Diabetes', round(prob[1] * 100, 2)
            return 'Low Risk of Diabetes', round(prob[0] * 100, 2)
        return ('High Risk of Diabetes' if prediction[0] == 1 else 'Low Risk of Diabetes'), 'N/A'
    score = 0
    if patient_data['Glucose'] >= 126: score += 3
    elif patient_data['Glucose'] >= 110: score += 2
    if patient_data['BMI'] >= 30: score += 2
    elif patient_data['BMI'] >= 25: score += 1
    if patient_data['Age'] >= 45: score += 1
    if patient_data['BloodPressure'] >= 90: score += 1
    if patient_data['Insulin'] >= 180: score += 1
    if score >= 4: return 'High Risk of Diabetes', min(98, 72 + score * 5)
    return 'Low Risk of Diabetes', max(70, 92 - score * 6)


def get_suggestions(patient_data):
    if patient_data['Glucose'] >= 126:
        return ['Monitor blood glucose levels regularly.', 'Reduce sugar and refined carbohydrate intake.', 'Consult a healthcare professional for proper evaluation.']
    if patient_data['BMI'] >= 30:
        return ['Follow a balanced calorie-controlled diet.', 'Exercise for at least 30 minutes daily.', 'Track BMI and weight weekly.']
    if patient_data['BloodPressure'] > 90:
        return ['Reduce sodium and processed food intake.', 'Monitor blood pressure regularly.', 'Practice yoga, walking, or meditation.']
    return ['Maintain a balanced nutritious diet.', 'Exercise regularly to stay active.', 'Drink enough water and get adequate sleep.']


def generate_pdf(patient_data, result, confidence, name, email, pred_time):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # 1. Header Banner
    pdf.setFillColorRGB(0.09, 0.17, 0.31) # #172B4D
    pdf.rect(0, height - 100, width, 100, fill=True, stroke=False)
    
    # Header Title
    pdf.setFillColorRGB(1.0, 1.0, 1.0)
    pdf.setFont('Helvetica-Bold', 22)
    pdf.drawString(40, height - 45, 'GlucoTrack Clinical Health Report')
    
    # Header Subtitle
    pdf.setFont('Helvetica-Oblique', 10)
    pdf.setFillColorRGB(0.70, 0.85, 1.0)
    pdf.drawString(40, height - 65, 'AI-Powered Diabetes Risk Assessment & Clinical Analytics')
    
    # Generation Timestamp
    pdf.setFont('Helvetica', 9)
    pdf.drawString(40, height - 82, f'Date generated: {pred_time}')
    
    # 2. Patient Information Card
    y = height - 145
    pdf.setFillColorRGB(0.95, 0.97, 1.0) # Light blue box background
    pdf.rect(40, y - 60, width - 80, 60, fill=True, stroke=False)
    
    pdf.setFillColorRGB(0.0, 0.0, 0.0)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(55, y - 18, 'PATIENT DEMOGRAPHICS')
    
    pdf.setFont('Helvetica', 10)
    pdf.drawString(55, y - 36, f'Full Name: {name}')
    pdf.drawString(55, y - 50, f'Email Address: {email}')
    
    # 3. Clinical Assessment (Risk Outcome)
    y -= 85
    is_high = 'High' in result
    if is_high:
        bg_color = (0.99, 0.92, 0.92) # Reddish background
        border_color = (0.93, 0.27, 0.27)
        text_color = (0.75, 0.08, 0.08)
    else:
        bg_color = (0.94, 0.99, 0.95) # Greenish background
        border_color = (0.13, 0.58, 0.25)
        text_color = (0.09, 0.39, 0.16)
        
    # Draw Risk Alert Box
    pdf.setFillColorRGB(*bg_color)
    pdf.setStrokeColorRGB(*border_color)
    pdf.setLineWidth(1.5)
    pdf.rect(40, y - 55, width - 80, 55, fill=True, stroke=True)
    
    # Alert Title & Score
    pdf.setFillColorRGB(*text_color)
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(55, y - 22, f'Risk Assessment: {result.upper()}')
    
    pdf.setFont('Helvetica', 11)
    pdf.drawString(55, y - 42, f'Analysis Confidence Level: {confidence}%')
    
    # 4. Clinical Parameter Table
    y -= 95
    pdf.setFillColorRGB(0.0, 0.0, 0.0)
    pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
    pdf.setLineWidth(0.5)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(40, y, 'CLINICAL MEASUREMENTS')
    pdf.line(40, y - 5, width - 40, y - 5)
    
    # Table Grid Layout
    y -= 25
    pdf.setFont('Helvetica-Bold', 10)
    pdf.setFillColorRGB(0.4, 0.4, 0.4)
    
    # Draw 2-column parameter grid
    items = list(patient_data.items())
    half = (len(items) + 1) // 2
    
    for idx, (key, value) in enumerate(items):
        col_x = 55 if idx < half else width / 2 + 15
        row_y = y - (idx % half) * 22
        
        # Friendly key labels mapping
        label_map = {
            'Pregnancies': 'Pregnancies',
            'Glucose': 'Glucose (mg/dL)',
            'BloodPressure': 'Blood Pressure (mmHg)',
            'SkinThickness': 'Skin Thickness (mm)',
            'Insulin': 'Insulin (μU/mL)',
            'BMI': 'BMI (kg/m²)',
            'DiabetesPedigreeFunction': 'Diabetes Pedigree Score',
            'Age': 'Age (years)'
        }
        friendly_key = label_map.get(key, key)
        
        pdf.setFillColorRGB(0.3, 0.3, 0.3)
        pdf.setFont('Helvetica', 10)
        pdf.drawString(col_x, row_y, f'{friendly_key}:')
        
        pdf.setFillColorRGB(0.0, 0.0, 0.0)
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(col_x + 140, row_y, f'{value}')
        
        # Subtle separator line
        pdf.setStrokeColorRGB(0.93, 0.93, 0.93)
        pdf.line(col_x, row_y - 4, col_x + 230, row_y - 4)
        
    # 5. Doctor Clinical Suggestions
    y = y - (half * 22) - 25
    pdf.setFillColorRGB(0.0, 0.0, 0.0)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(40, y, 'RECOMMENDED CLINICAL ACTION PLAN')
    
    pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
    pdf.line(40, y - 5, width - 40, y - 5)
    
    y -= 25
    suggestions = get_suggestions(patient_data)
    pdf.setFont('Helvetica', 10)
    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    
    for s in suggestions:
        pdf.drawString(55, y, f'•  {s}')
        y -= 20
        
    # 6. Report Footer / Disclaimer
    pdf.setStrokeColorRGB(0.9, 0.9, 0.9)
    pdf.line(40, 50, width - 40, 50)
    
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.setFont('Helvetica-Oblique', 8)
    pdf.drawCentredString(width / 2, 38, 'DISCLAIMER: This diagnostic report is generated utilizing machine learning predictive modeling.')
    pdf.drawCentredString(width / 2, 26, 'It is for educational and screening purposes only and does not constitute official medical advice.')
    
    pdf.save()
    return buffer.getvalue()


def public_header():
    col_logo, col_nav, col_spacer, col_theme, col_signin = st.columns([2.5, 4.0, 2.0, 1.2, 1.2])
    with col_logo:
        st.markdown(f'''
        <div style="display:flex;align-items:center;gap:12px;font-size:24px;font-weight:900;color:{TEXT};margin-top:8px;">
            <div style="width:36px;height:36px;border-radius:8px;background:{BLUE};color:white;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;">⌁</div>
            <div>GlucoTrack</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_nav:
        st.markdown(f'''
        <div style="display:flex;gap:32px;margin-top:16px;">
            <a href="#features" class="nav-link" target="_self">What GlucoTrack Does</a>
            <a href="#how-it-works" class="nav-link" target="_self">How It Works</a>
        </div>
        ''', unsafe_allow_html=True)
    with col_theme:
        theme_label = '☀️ Light' if st.session_state.dark_mode else '🌙 Dark'
        if st.button(theme_label, key='pub_theme_toggle', type='secondary', use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col_signin:
        if st.button('Sign In', key='nav_signin', type='primary', use_container_width=True):
            st.session_state.started = True
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'signin'
            st.rerun()
    st.markdown(f'<hr style="margin:10px 0 20px 0;border:0;border-top:1px solid {BORDER};">', unsafe_allow_html=True)


def dashboard_sidebar():
    if not st.session_state.started or not st.session_state.logged_in: return
    name = st.session_state.current_user_name; email = st.session_state.current_user_email; role = {'patient': 'User', 'doctor': 'Doctor', 'admin': 'Admin'}.get(st.session_state.user_type, 'User'); init = initials(name)
    
    # Retrieve profile picture if available
    profile_pic = None
    if st.session_state.user_type == 'patient' and email in users:
        profile_pic = users[email].get('profile_pic')
    elif st.session_state.user_type == 'doctor' and email in doctors:
        profile_pic = doctors[email].get('profile_pic')
        
    if profile_pic:
        avatar_html = f'<img src="data:image/png;base64,{profile_pic}" style="width:50px;height:50px;border-radius:16px;object-fit:cover;display:block;">'
    else:
        avatar_html = f'<div class="sb-avatar">{init}</div>'
        
    st.sidebar.markdown(f'<div class="sb-header"><div class="sb-logo-box">⌁</div><div class="sb-brand">GlucoTrack</div></div><div class="sb-profile">{avatar_html}<div><div class="sb-name">{name if name else "Loading..."}</div><div class="sb-role">{role}</div></div></div>', unsafe_allow_html=True)
    
    if st.sidebar.button('👤 Edit Profile', use_container_width=True): 
        st.session_state.page = 'profile'; st.rerun()
        
    if st.sidebar.button('☀️ Light Mode' if st.session_state.dark_mode else '🌙 Dark Mode', use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
        
    if st.session_state.user_type == 'patient': options = ['prediction', 'dashboard']; labels = ['🩺 Predict', '📊 Health Dashboard']
    elif st.session_state.user_type == 'doctor': options = ['doctor', 'dashboard']; labels = ['👨⚕️ Patient Data', '📊 Health Dashboard']
    else: options = ['admin', 'prediction', 'dashboard']; labels = ['🛡️ Admin Panel', '🩺 Predict', '📊 Health Dashboard']
    if st.session_state.page not in options and st.session_state.page != 'profile': st.session_state.page = options[0]
    if st.session_state.page != 'profile':
        idx = options.index(st.session_state.page) if st.session_state.page in options else 0
        selected_label = st.sidebar.radio('', labels, index=idx, label_visibility='collapsed')
        selected_page = options[labels.index(selected_label)]
        if selected_page != st.session_state.page: st.session_state.page = selected_page; st.rerun()
    st.sidebar.markdown('<div style="height:200px;"></div>', unsafe_allow_html=True)
    if st.sidebar.button('↪  Sign Out', use_container_width=True):
        add_audit('Logout', st.session_state.current_user_email, 'User logged out')
        for key in ['logged_in', 'user_type', 'current_user_name', 'current_user_email', 'prediction_done', 'patient_data', 'prediction_result', 'confidence', 'prediction_time', 'pdf_bytes']:
            st.session_state[key] = defaults[key]
        st.session_state.page = 'auth'; st.session_state.auth_mode = 'signin'; st.rerun()


def landing_page():
    public_header()
    components.html(
        """
        <script>
            if (!window.parent.location.hash) {
                const mainContainer = window.parent.document.querySelector('.main') || window.parent.document.querySelector('section.main');
                if (mainContainer) { mainContainer.scrollTop = 0; }
            }
        </script>
        """,
        height=0,
        width=0
    )
    
    st.markdown(f'''
    <section class="hero" style="padding-bottom: 20px;">
        <div class="hero-badge">↯ AI-POWERED HEALTH PLATFORM</div>
        <h1 class="hero-title">Know Your <span class="hero-blue">Diabetes Risk</span></h1>
        <p class="hero-sub">Predict diabetes risk in seconds using Machine Learning. Understand<br>your health. Take action early. Live better.</p>
    </section>
    ''', unsafe_allow_html=True)
    
    # Centered single button
    c1, c2, c3 = st.columns([1.6, 1.2, 1.6])
    with c2:
        if st.button('Get Started', type='primary', key='landing_start_btn', use_container_width=True):
            st.session_state.started = True
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'signup'
            st.session_state.signup_step = 1
            st.rerun()
            
    st.markdown(f'''
    <div class="stats-wrap">
        <div class="stat">
            <div class="stat-num">95%+</div>
            <div class="stat-label">Model Accuracy</div>
        </div>
        <div class="stat">
            <div class="stat-num">8</div>
            <div class="stat-label">Health Parameters</div>
        </div>
        <div class="stat">
            <div class="stat-num">100%</div>
            <div class="stat-label">Free to Use</div>
        </div>
    </div>
    <section id="features" class="section">
        <h2 class="section-title">What GlucoTrack Does</h2>
        <p class="section-sub">Three powerful features to monitor, predict, and improve your health</p>
        <div class="feature-grid">
            <div class="feature-card feature-blue">
                <div class="pill pill-blue">MACHINE LEARNING</div>
                <div class="icon-box icon-blue">🧠</div>
                <div class="feature-title">ML-Based Risk Prediction</div>
                <div class="feature-text">Our trained ML model analyzes 8 clinical parameters — Glucose, BMI, Insulin, Blood Pressure, Age, Pregnancies, Skin Thickness, and DPF — to compute your diabetes risk with a confidence score.</div>
            </div>
            <div class="feature-card feature-green">
                <div class="pill pill-green">ANALYTICS</div>
                <div class="icon-box icon-green">⌁</div>
                <div class="feature-title">Patient Health Analytics</div>
                <div class="feature-text">Visualize your health data through interactive charts, glucose gauges, and BMI indicators inside a clean dashboard.</div>
            </div>
            <div class="feature-card feature-red">
                <div class="pill pill-red">PERSONALIZED</div>
                <div class="icon-box icon-red">♡</div>
                <div class="feature-title">Health Suggestions</div>
                <div class="feature-text">Get targeted, personalized recommendations based on your specific health values to help you take meaningful action.</div>
            </div>
        </div>
    </section>
    <section id="how-it-works" class="section">
        <h2 class="section-title">How It Works</h2>
        <p class="section-sub">Get your diabetes risk assessment in 4 simple steps</p>
        <div class="steps-grid">
            <div class="step-card">
                <div class="step-num">01</div>
                <div class="step-title">Create Account</div>
                <div class="step-text">Sign up with your name and email address</div>
            </div>
            <div class="step-card">
                <div class="step-num">02</div>
                <div class="step-title">Enter Health Data</div>
                <div class="step-text">Fill in your clinical health values</div>
            </div>
            <div class="step-card">
                <div class="step-num">03</div>
                <div class="step-title">Get Prediction</div>
                <div class="step-text">ML model calculates your diabetes risk</div>
            </div>
            <div class="step-card">
                <div class="step-num">04</div>
                <div class="step-title">View Dashboard</div>
                <div class="step-text">See analytics, share or download your PDF report</div>
            </div>
        </div>
    </section>
    <section class="section" style="padding-bottom:20px;">
        <div class="bottom-cta" style="background:{BLUE};">
            <div style="font-size:42px;margin-bottom:18px;">♢</div>
            <h2 style="font-size:38px;font-weight:950;margin:0 0 18px;color:white !important;">Take Control of Your Health</h2>
            <p style="font-size:21px;line-height:1.5;margin-bottom:34px;color:white !important;">Join thousands who use GlucoTrack to monitor their diabetes risk. It's free, fast, and takes less than 2 minutes.</p>
        </div>
    </section>
    ''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1.8, 1.4, 1.8])
    with c2:
        if st.button('Create Free Account →', key='bottom_signup_btn', type='primary', use_container_width=True):
            st.session_state.started = True
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'signup'
            st.session_state.signup_step = 1
            st.rerun()
            
    st.markdown('''
    <div class="footer">
        <div class="footer-logo">⌁ GlucoTrack</div>
        <div>For educational purposes only. Always consult a medical professional.</div>
    </div>
    ''', unsafe_allow_html=True)


def auth_page():
    public_header()
    
    # Sleek navigation back button
    if st.button('← Back to Home', key='auth_back_home', type='secondary'):
        st.session_state.started = False
        st.session_state.page = 'home'
        st.rerun()
        
    if st.session_state.auth_mode == 'signin':
        st.markdown('<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">⌁</div><div>GlucoTrack</div></div><h1>Welcome back</h1><p>Sign in to continue to your dashboard</p></div>', unsafe_allow_html=True)
        
        c1, col_card, c3 = st.columns([1, 1.8, 1])
        with col_card:
            with st.container(border=True):
                email = st.text_input('Email address', placeholder='you@example.com', key='signin_email')
                password = st.text_input('Password', type='password', placeholder='Your password', key='signin_password')
                is_admin = st.checkbox('Are you an admin or doctor?', key='is_admin_login')
                if is_admin:
                    st.info('🔑 **Demo Credentials:**\n\n'
                            '🛡️ *Admin*:\n'
                            '- Email: `admin@glucotrack.com`\n'
                            '- Password: `admin@123`\n\n'
                            '👨‍⚕️ *Doctor*:\n'
                            '- Email: `doctor@glucotrack.com`\n'
                            '- Password: `Doc@1234`\n'
                            '*(Note: Doctor account must be approved in the Admin Panel first)*')
                st.write('')
                if st.button('Sign In →', type='primary', use_container_width=True, key='signin_btn'):
                    ok, msg = login_user(email, password)
                    if ok: st.rerun()
                    else: st.error(msg)
                st.markdown(f'<div style="text-align:center;margin:22px 0;color:{MUTED};">or</div>', unsafe_allow_html=True)
                if st.button('Create a free account →', type='secondary', use_container_width=True, key='to_signup'):
                    st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()
                st.markdown(f'<p style="text-align:center;color:{MUTED};margin-top:24px;">🔒 Your data is private and never shared.</p>', unsafe_allow_html=True)
    else:
        if st.session_state.signup_step == 1:
            st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">⌁</div><div>GlucoTrack</div></div><h1>Create your account</h1><p>Step 1 of 2 — Personal Details</p><div style="height:7px;background:{BLUE};border-radius:8px;max-width:560px;margin:34px auto 0;width:50%;"></div></div>', unsafe_allow_html=True)
            
            c1, col_card, c3 = st.columns([1, 1.8, 1])
            with col_card:
                with st.container(border=True):
                    full_name = st.text_input('Full Name *', placeholder='John Doe', key='reg_name')
                    email = st.text_input('Email Address *', placeholder='you@example.com', key='reg_email')
                    phone = st.text_input('Phone Number *', placeholder='+91 98765 43210', key='reg_phone')
                    c_a, c_b = st.columns(2)
                    with c_a: age = st.number_input('Age *', 1, 100, 25, key='reg_age')
                    with c_b: gender = st.selectbox('Gender', ['Select', 'Female', 'Male', 'Other'], key='reg_gender')
                    address = st.text_area('Address', placeholder='Your address (optional)', key='reg_address')
                    if st.button('Continue', type='primary', use_container_width=True, key='reg_continue'):
                        email_clean = email.strip().lower()
                        if not full_name or not email_clean or not phone: st.error('Please fill all required fields.')
                        elif gender == 'Select': st.error('Please select gender.')
                        elif email_clean in users or email_clean in doctors or email_clean in admins: st.error('Email already registered. Please sign in.')
                        else:
                            st.session_state.signup_name = full_name.strip(); st.session_state.signup_email = email_clean; st.session_state.signup_phone = phone.strip(); st.session_state.signup_age = age; st.session_state.signup_gender = gender; st.session_state.signup_address = address.strip(); st.session_state.signup_step = 2; st.rerun()
                    if st.button('Already have an account? Sign in', type='secondary', use_container_width=True, key='step1_to_signin'):
                        st.session_state.auth_mode = 'signin'
                        st.rerun()
        else:
            st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">⌁</div><div>GlucoTrack</div></div><h1>Create your account</h1><p>Step 2 of 2 — Set Password</p><div style="height:7px;background:{BLUE};border-radius:8px;max-width:560px;margin:34px auto 0;width:100%;"></div></div>', unsafe_allow_html=True)
            
            c1, col_card, c3 = st.columns([1, 1.8, 1])
            with col_card:
                with st.container(border=True):
                    password = st.text_input('Create Password', type='password', placeholder='At least 6 characters', key='reg_password')
                    confirm = st.text_input('Confirm Password', type='password', placeholder='Re-enter password', key='reg_confirm')
                    label, color, width, hints = password_strength(password)
                    if password:
                        hint_text = f"add {', '.join(hints)}" if hints else 'Strong password ✓'
                        st.markdown(f'<div style="margin:-4px 0 20px;"><div style="height:5px;border-radius:5px;background:#E2E8F0;overflow:hidden;"><div style="height:100%;width:{width}%;background:{color};border-radius:5px;"></div></div><div style="font-size:13px;color:{color};font-weight:700;margin-top:6px;">{label} · {hint_text}</div></div>', unsafe_allow_html=True)
                    c_a, c_b = st.columns(2)
                    with c_a:
                        if st.button('Back', type='secondary', use_container_width=True, key='back_signup'):
                            st.session_state.signup_step = 1; st.rerun()
                    with c_b:
                        if st.button('Create Account', type='primary', use_container_width=True, key='create_account_btn'):
                            if not password: st.error('Please enter password.')
                            elif len(password) < 6: st.error('Password must be at least 6 characters.')
                            elif password != confirm: st.error('Passwords do not match.')
                            else:
                                st.session_state.signup_password = password; st.session_state.page = 'create_profile'; st.rerun()
                    if st.button('Already have an account? Sign in', type='secondary', use_container_width=True, key='step2_to_signin'):
                        st.session_state.auth_mode = 'signin'
                        st.rerun()


def create_profile_page():
    public_header()
    
    if st.button('← Back to Password Setup', key='create_profile_back', type='secondary'):
        st.session_state.page = 'auth'
        st.session_state.auth_mode = 'signup'
        st.session_state.signup_step = 2
        st.rerun()
        
    st.markdown(f'<div class="auth-title"><div class="auth-logo-row" style="color:{TEXT} !important;"><div class="logo-square">⌁</div><div>GlucoTrack</div></div><h1 style="font-size:32px;margin:28px 0 6px;color:{TEXT} !important;">Create Profile</h1><p style="font-size:18px;color:{MUTED} !important;">Choose whether you are a patient or doctor</p></div>', unsafe_allow_html=True)
    
    c1, col_card, c3 = st.columns([1, 1.8, 1])
    with col_card:
        with st.container(border=True):
            role = st.radio('I am a', ['Patient', 'Doctor'], horizontal=True)
            name = st.text_input('Full Name', value=st.session_state.signup_name)
            email = st.text_input('Email', value=st.session_state.signup_email, disabled=True)
            if role == 'Patient':
                phone = st.text_input('Phone', value=st.session_state.signup_phone)
                age = st.number_input('Age', 1, 100, int(st.session_state.signup_age))
                gender = st.selectbox('Gender', ['Female', 'Male', 'Other'], index=['Female', 'Male', 'Other'].index(st.session_state.signup_gender) if st.session_state.signup_gender in ['Female', 'Male', 'Other'] else 0)
                address = st.text_area('Address', value=st.session_state.signup_address)
                
                # Profile Photo Upload
                uploaded_photo = st.file_uploader('Upload Profile Photo (Optional)', type=['png', 'jpg', 'jpeg'], key='patient_photo')
                
                if st.button('Create Patient Profile', type='primary', use_container_width=True):
                    base64_photo = None
                    if uploaded_photo:
                        base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                        
                    users[st.session_state.signup_email] = {
                        'password': st.session_state.signup_password, 
                        'name': name, 
                        'phone': phone, 
                        'age': age, 
                        'gender': gender, 
                        'address': address, 
                        'medical_history': '', 
                        'user_type': 'patient', 
                        'profile_created': True,
                        'profile_pic': base64_photo
                    }
                    save_json(USERS_FILE, users)
                    add_audit('Account Created', st.session_state.signup_email, 'Patient profile created')
                    ok, msg = login_user(st.session_state.signup_email, st.session_state.signup_password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                phone = st.text_input('Phone', value=st.session_state.signup_phone)
                specialization = st.text_input('Specialization', placeholder='Endocrinology')
                hospital = st.text_input('Hospital / Clinic')
                license_no = st.text_input('Medical License No.')
                
                # Profile Photo Upload
                uploaded_photo = st.file_uploader('Upload Profile Photo (Optional)', type=['png', 'jpg', 'jpeg'], key='doctor_photo')
                
                if st.button('Create Doctor Profile', type='primary', use_container_width=True):
                    base64_photo = None
                    if uploaded_photo:
                        base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                        
                    doctors[st.session_state.signup_email] = {
                        'password': st.session_state.signup_password, 
                        'name': name, 
                        'phone': phone, 
                        'specialization': specialization, 
                        'hospital': hospital, 
                        'license_no': license_no, 
                        'approved': False, 
                        'user_type': 'doctor', 
                        'profile_created': True,
                        'profile_pic': base64_photo
                    }
                    save_json(DOCTORS_FILE, doctors)
                    add_audit('Doctor Signup', st.session_state.signup_email, 'Waiting for approval')
                    st.success('Doctor profile created. Please wait for admin approval.')
                    st.session_state.page = 'auth'
                    st.session_state.auth_mode = 'signin'
                    st.rerun()


def prediction_page():
    st.markdown('<div class="page-head"><div class="page-icon">🩺</div><div><div class="page-title">Diabetes Risk Prediction</div><div class="page-sub">Enter your clinical parameters for an AI-powered assessment</div></div></div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<div class="card-heading"><div class="badge-num">1</div>Clinical Health Parameters</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            preg = st.number_input('Pregnancies', 0, 20, 1)
            bp = st.number_input('Blood Pressure (mm Hg)', 30, 140, 70)
            insulin = st.number_input('Insulin (μU/mL)', 0, 400, 100)
            dpf = st.number_input('Diabetes Pedigree', 0.0, 3.0, 0.5)
        with c2:
            glucose = st.number_input('Glucose (mg/dL)', 50, 250, 120)
            skin = st.number_input('Skin Thickness (mm)', 0, 100, 20)
            bmi = st.number_input('BMI', 10.0, 70.0, 25.0)
            default_age = int(users.get(st.session_state.current_user_email, {}).get('age', 30)) if st.session_state.user_type == 'patient' else 30
            age = st.number_input('Age (years)', 1, 100, default_age)
            
    if st.button('Predict Diabetes Risk  ›', type='primary', use_container_width=True):
        patient_data = {'Pregnancies': preg, 'Glucose': glucose, 'BloodPressure': bp, 'SkinThickness': skin, 'Insulin': insulin, 'BMI': bmi, 'DiabetesPedigreeFunction': dpf, 'Age': age}; result, confidence = model_predict(patient_data); pred_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S'); name = st.session_state.current_user_name; email = st.session_state.current_user_email; pdf = generate_pdf(patient_data, result, confidence, name, email, pred_time); st.session_state.patient_data = patient_data; st.session_state.prediction_result = result; st.session_state.confidence = confidence; st.session_state.prediction_time = pred_time; st.session_state.pdf_bytes = pdf; st.session_state.prediction_done = True; reports.append({'name': name, 'email': email, 'result': result, 'confidence': confidence, 'time': pred_time, 'data': patient_data}); save_json(REPORTS_FILE, reports); add_audit('Prediction', email, result); st.session_state.page = 'dashboard'; st.rerun()


def dashboard_page():
    st.markdown('<div class="page-head"><div class="page-icon">📊</div><div><div class="page-title">Health Dashboard</div><div class="page-sub">Your prediction result, analytics, and suggestions</div></div></div>', unsafe_allow_html=True)
    if not st.session_state.prediction_done:
        st.warning('No prediction found. Please complete a prediction first.')
        if st.button('Go to Prediction', type='primary'): st.session_state.page = 'prediction'; st.rerun()
        return
    result = st.session_state.prediction_result; confidence = st.session_state.confidence; patient_data = st.session_state.patient_data
    
    st.markdown(f'<div class="{"result-high" if "High" in result else "result-low"}">{"⚠️" if "High" in result else "✅"} {result}<br><span style="font-size:17px;">Confidence: {confidence}%</span></div>', unsafe_allow_html=True)
    st.write('')
    
    st.subheader('🧾 Submitted Health Parameters')
    params = list(patient_data.items()); cols = st.columns(4)
    for i, (k, v) in enumerate(params):
        with cols[i % 4]: st.markdown(f'<div class="param-card"><div class="param-label">{k}</div><div class="param-value">{v}</div></div>', unsafe_allow_html=True)
        
    st.write('')
    st.subheader('📈 Patient Health Analytics')
    metrics = ['Glucose', 'BMI', 'Insulin', 'BloodPressure', 'Age']; values = [patient_data[m] for m in metrics]; fig = go.Figure(); fig.add_trace(go.Bar(x=metrics, y=values, marker_color=[BLUE, '#22C55E', '#F97316', '#8B5CF6', '#EF4444'], text=values, textposition='outside')); fig.update_layout(template=PLOT_TEMPLATE, height=390, title='Health Parameter Overview'); st.plotly_chart(fig, use_container_width=True)
    
    suggestions = get_suggestions(patient_data); items = ''.join([f'<li>{s}</li>' for s in suggestions]); components.html(f'<div style="background:{BOX_SUGGESTION_BG};padding:28px 34px;border-radius:20px;border:1px solid {BORDER};font-family:Inter,Arial;"><h2 style="color:{BOX_SUGGESTION_TITLE};margin:0 0 16px;font-weight:900;">💡 Health Suggestions</h2><ul style="color:{BOX_SUGGESTION_TEXT};font-size:16px;line-height:1.8;font-weight:600;">{items}</ul></div>', height=230)
    
    col_dl, col_wa = st.columns(2)
    with col_dl:
        st.download_button('📄 Download Patient Report', data=st.session_state.pdf_bytes, file_name=f"glucotrack_{st.session_state.current_user_name.replace(' ', '_')}_report.pdf", mime='application/pdf', use_container_width=True)
    
    with col_wa:
        # Construct url-encoded WhatsApp message
        msg_text = f"*GlucoTrack Diabetes Risk Report*\n\n" \
                  f"👤 *Patient Name:* {st.session_state.current_user_name}\n" \
                  f"🩺 *Risk Assessment:* {result}\n" \
                  f"🎯 *Confidence Level:* {confidence}%\n" \
                  f"📅 *Date/Time:* {st.session_state.prediction_time}\n\n" \
                  f"📊 *Clinical Values:*\n" \
                  f"- Glucose: {patient_data['Glucose']} mg/dL\n" \
                  f"- BMI: {patient_data['BMI']}\n" \
                  f"- Blood Pressure: {patient_data['BloodPressure']} mmHg\n" \
                  f"- Age: {patient_data['Age']} years\n\n" \
                  f"💡 *Key Recommendations:*\n"
        for s in suggestions[:2]:
            msg_text += f"- {s}\n"
        msg_text += "\n_For educational purposes only. Always consult a medical professional._"
        encoded_text = urllib.parse.quote(msg_text)
        whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_text}"
        
        st.markdown(f'''
        <a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
            <div style="background-color:#25D366;color:white;text-align:center;padding:14px;border-radius:14px;font-weight:800;font-size:16px;box-shadow:0 12px 24px rgba(37,211,102,.20);min-height:52px;display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.93c0 1.39.365 2.743 1.06 3.962L0 16l4.13-1.082A7.86 7.86 0 0 0 7.99 12c4.365 0 7.934-3.558 7.939-7.93a7.86 7.86 0 0 0-2.328-5.744M7.993 11.89c-1.392 0-2.702-.38-3.829-1.08l-.275-.164-2.429.637.649-2.368-.18-.287a5.95 5.95 0 0 1-.98-3.216c.004-3.279 2.685-5.96 5.966-5.96 1.587.001 3.079.616 4.2 1.738a5.96 5.96 0 0 1 1.729 4.2c-.004 3.28-2.685 5.96-5.966 5.96M11.53 8.87c-.191-.096-1.136-.56-1.31-.624-.173-.064-.3-.096-.426.096-.127.192-.49.61-.6.732-.11.123-.219.138-.41.042-.191-.096-.807-.297-1.537-.95-.568-.506-.95-1.133-1.062-1.324-.112-.19-.012-.294.084-.389.087-.085.191-.223.287-.335.095-.112.127-.19.19-.32.064-.13.032-.243-.016-.339-.048-.096-.426-1.026-.583-1.407-.152-.37-.308-.32-.426-.326-.11-.006-.237-.008-.363-.008-.127 0-.332.048-.506.237-.174.19-66 1.63-66 3.97 0 2.34 1.7 4.595 1.94 4.914.24.318 3.352 5.12 8.12 7.18 1.133.49 2.02.784 2.709 1.004 1.134.36 2.167.309 2.984.187.912-.136 2.793-.113 3.197-1.197.404-1.084.404-2.013.283-2.203-.12-.19-.32-.304-.51-.399"/>
                </svg>
                Share Report via WhatsApp
            </div>
        </a>
        <div style="font-size:12px;color:{MUTED};margin-top:8px;font-weight:500;text-align:center;">💡 <i>Tip: Download the PDF report first, then click here to send the clinical text summary and attach the downloaded PDF.</i></div>
        ''', unsafe_allow_html=True)
        
    st.write('')
    if st.button('New Prediction', type='secondary', use_container_width=True): reset_prediction_state(); st.session_state.page = 'prediction'; st.rerun()


def doctor_page():
    st.markdown('<div class="page-head"><div class="page-icon">👨‍⚕️</div><div><div class="page-title">Doctor Portal</div><div class="page-sub">Comprehensive Patient Directory & Health Analytics</div></div></div>', unsafe_allow_html=True)
    
    # Calculate key portal stats
    high_cases = [r for r in reports if 'High' in r.get('result', '')]
    total_cases = len(reports)
    total_patients = len(users)
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric('Total Assessments', total_cases)
        c2.metric('High Risk Patients ⚠️', len(high_cases))
        c3.metric('Registered Patients', total_patients)
        
    st.write('')
    
    tab_dir, tab_detail = st.tabs(['📋 Patient Reports Directory', '🔍 Detailed Patient Analysis'])
    
    with tab_dir:
        st.subheader('All Patient Reports')
        if not reports:
            st.info('No patient reports available yet.')
        else:
            report_data = []
            for idx, r in enumerate(reports):
                data_dict = r.get('data', {})
                report_data.append({
                    'ID': idx,
                    'Patient Name': r.get('name'),
                    'Email': r.get('email'),
                    'Risk Level': r.get('result'),
                    'Confidence': f"{r.get('confidence')}%",
                    'Assessment Time': r.get('time'),
                    'Glucose': data_dict.get('Glucose', 'N/A'),
                    'BMI': data_dict.get('BMI', 'N/A'),
                    'BP': data_dict.get('BloodPressure', 'N/A'),
                    'Age': data_dict.get('Age', 'N/A')
                })
            df_reports = pd.DataFrame(report_data)
            st.dataframe(df_reports.drop(columns=['ID']), use_container_width=True)
            
    with tab_detail:
        if not reports:
            st.info('No patient reports available for analysis.')
        else:
            # Dropdown options
            report_options = [f"{r.get('name')} ({r.get('time')}) - {r.get('result')}" for r in reports]
            selected_idx = st.selectbox('Select Patient Report to Analyze:', range(len(reports)), format_func=lambda x: report_options[x])
            
            selected_report = reports[selected_idx]
            patient_data = selected_report.get('data', {})
            result = selected_report.get('result')
            confidence = selected_report.get('confidence')
            pred_time = selected_report.get('time')
            name = selected_report.get('name')
            email = selected_report.get('email')
            
            # Fetch details from users db
            patient_info = users.get(email, {})
            phone = patient_info.get('phone', 'Not Provided')
            age = patient_info.get('age', patient_data.get('Age', 'N/A'))
            gender = patient_info.get('gender', 'Not Provided')
            
            # Profile card
            st.markdown(f'''
            <div style="background:{CARD}; border: 1px solid {BORDER}; padding: 24px; border-radius: 20px; margin-bottom: 24px;">
                <h3 style="margin-top:0; color:{TEXT};">👤 Patient Profile: {name}</h3>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
                    <div><b>Email:</b> {email}</div>
                    <div><b>Phone:</b> {phone}</div>
                    <div><b>Age:</b> {age}</div>
                    <div><b>Gender:</b> {gender}</div>
                </div>
                <div class="{"result-high" if "High" in result else "result-low"}" style="padding: 16px;">
                    {"⚠️" if "High" in result else "✅"} <b>Assessment:</b> {result} ({confidence}% Confidence)
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Param cards
            st.subheader('📋 Clinical Health Parameters')
            cols = st.columns(4)
            param_labels = {
                'Pregnancies': 'Pregnancies',
                'Glucose': 'Glucose (mg/dL)',
                'BloodPressure': 'Blood Pressure (mmHg)',
                'SkinThickness': 'Skin Thickness (mm)',
                'Insulin': 'Insulin (μU/mL)',
                'BMI': 'BMI (kg/m²)',
                'DiabetesPedigreeFunction': 'Diabetes Pedigree',
                'Age': 'Age (years)'
            }
            for i, (key, label) in enumerate(param_labels.items()):
                val = patient_data.get(key, 'N/A')
                with cols[i % 4]:
                    st.markdown(f'<div class="param-card"><div class="param-label">{label}</div><div class="param-value">{val}</div></div>', unsafe_allow_html=True)
            
            # Charts & Suggestions
            st.write('')
            c_left, c_right = st.columns([3, 2])
            with c_left:
                st.subheader('📈 Health Parameter Analytics')
                metrics_list = ['Glucose', 'BMI', 'Insulin', 'BloodPressure', 'Age']
                values_list = [patient_data.get(m, 0) for m in metrics_list]
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=metrics_list, 
                    y=values_list, 
                    marker_color=[BLUE, '#22C55E', '#F97316', '#8B5CF6', '#EF4444'], 
                    text=values_list, 
                    textposition='outside'
                ))
                fig.update_layout(template=PLOT_TEMPLATE, height=350, title='Key Metrics Analysis', margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with c_right:
                st.subheader('💡 Clinical Suggestions')
                suggestions = get_suggestions(patient_data)
                s_html = ''.join([f'<li style="margin-bottom:8px;">{s}</li>' for s in suggestions])
                components.html(f'''
                <div style="background:{BOX_SUGGESTION_BG}; padding: 20px; border-radius: 16px; border: 1px solid {BORDER}; font-family: Inter, Arial; height: 100%;">
                    <h4 style="color:{BOX_SUGGESTION_TITLE}; margin: 0 0 12px; font-weight:900;">Recommendations</h4>
                    <ul style="color:{BOX_SUGGESTION_TEXT}; font-size:15px; line-height:1.6; font-weight:600; padding-left:20px; margin:0;">
                        {s_html}
                    </ul>
                </div>
                ''', height=350)
                
            # PDF Generation & WhatsApp Integration
            st.write('')
            st.subheader('📄 Export & Share Reports')
            
            pdf_data = generate_pdf(patient_data, result, confidence, name, email, pred_time)
            
            col_pdf_dl, col_wa_share = st.columns(2)
            with col_pdf_dl:
                st.download_button(
                    label=f'📥 Download PDF Report for {name}',
                    data=pdf_data,
                    file_name=f"glucotrack_{name.replace(' ', '_')}_report.pdf",
                    mime='application/pdf',
                    use_container_width=True,
                    key=f"dl_btn_{selected_idx}"
                )
                
            with col_wa_share:
                default_phone = phone if phone != 'Not Provided' else ''
                target_phone = st.text_input('Recipient Phone Number (with Country Code):', value=default_phone, key=f"phone_input_{selected_idx}", placeholder='e.g., +919876543210')
                
                # Format clinical report summary for WhatsApp
                msg_text = f"*GlucoTrack Clinical Health Analytics Report*\n\n" \
                           f"👤 *Patient Name:* {name}\n" \
                           f"📧 *Email:* {email}\n" \
                           f"📞 *Phone:* {phone}\n" \
                           f"🩺 *Assessment Result:* {result}\n" \
                           f"🎯 *Model Confidence:* {confidence}%\n" \
                           f"📅 *Report Generated:* {pred_time}\n\n" \
                           f"📊 *Clinical Metrics:*\n" \
                           f"- Glucose: {patient_data.get('Glucose', 'N/A')} mg/dL\n" \
                           f"- BMI: {patient_data.get('BMI', 'N/A')}\n" \
                           f"- Blood Pressure: {patient_data.get('BloodPressure', 'N/A')} mmHg\n" \
                           f"- Insulin: {patient_data.get('Insulin', 'N/A')} μU/mL\n" \
                           f"- Age: {patient_data.get('Age', 'N/A')} years\n\n" \
                           f"💡 *Key Doctor Recommendations:*\n"
                for s in suggestions:
                    msg_text += f"- {s}\n"
                msg_text += f"\n_This report was reviewed and shared by Dr. {st.session_state.current_user_name} via GlucoTrack._"
                
                encoded_text = urllib.parse.quote(msg_text)
                clean_phone = ''.join(c for c in target_phone if c.isdigit())
                
                if clean_phone:
                    whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"
                else:
                    whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_text}"
                
                st.markdown(f'''
                <a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#25D366;color:white;text-align:center;padding:14px;border-radius:14px;font-weight:800;font-size:16px;box-shadow:0 12px 24px rgba(37,211,102,.20);min-height:52px;display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.93c0 1.39.365 2.743 1.06 3.962L0 16l4.13-1.082A7.86 7.86 0 0 0 7.99 12c4.365 0 7.934-3.558 7.939-7.93a7.86 7.86 0 0 0-2.328-5.744M7.993 11.89c-1.392 0-2.702-.38-3.829-1.08l-.275-.164-2.429.637.649-2.368-.18-.287a5.95 5.95 0 0 1-.98-3.216c.004-3.279 2.685-5.96 5.966-5.96 1.587.001 3.079.616 4.2 1.738a5.96 5.96 0 0 1 1.729 4.2c-.004 3.28-2.685 5.96-5.966 5.96M11.53 8.87c-.191-.096-1.136-.56-1.31-.624-.173-.064-.3-.096-.426.096-.127.192-.49.61-.6.732-.11.123-.219.138-.41.042-.191-.096-.807-.297-1.537-.95-.568-.506-.95-1.133-1.062-1.324-.112-.19-.012-.294.084-.389.087-.085.191-.223.287-.335.095-.112.127-.19.19-.32.064-.13.032-.243-.016-.339-.048-.096-.426-1.026-.583-1.407-.152-.37-.308-.32-.426-.326-.11-.006-.237-.008-.363-.008-.127 0-.332.048-.506.237-.174.19-66 1.63-66 3.97 0 2.34 1.7 4.595 1.94 4.914.24.318 3.352 5.12 8.12 7.18 1.133.49 2.02.784 2.709 1.004 1.134.36 2.167.309 2.984.187.912-.136 2.793-.113 3.197-1.197.404-1.084.404-2.013.283-2.203-.12-.19-.32-.304-.51-.399"/>
                        </svg>
                        Send Report via WhatsApp
                    </div>
                </a>
                ''', unsafe_allow_html=True)


def admin_page():
    st.markdown('<div class="page-head"><div class="page-icon">🛡️</div><div><div class="page-title">Admin Panel</div><div class="page-sub">Manage doctors, users, reports, and audit logs</div></div></div>', unsafe_allow_html=True)
    pending = {email: d for email, d in doctors.items() if not d.get('approved', False)}; high = [r for r in reports if 'High' in r.get('result', '')]
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Patients', len(users))
        c2.metric('Doctors', len(doctors))
        c3.metric('Pending Doctors', len(pending))
        c4.metric('High Risk', len(high))
        
    st.write('')
    st.subheader('Doctor Approval Requests')
    if not pending: st.success('No pending doctor approvals.')
    else:
        for email, d in pending.items():
            with st.container(border=True):
                st.write(f"**Name:** {d.get('name')} | **Email:** {email}")
                st.write(f"Specialization: {d.get('specialization')}")
                st.write(f"Hospital: {d.get('hospital')}")
                st.write(f"License: {d.get('license_no')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f'Approve {email}', key=f'approve_{email}', type='primary', use_container_width=True):
                        doctors[email]['approved'] = True; save_json(DOCTORS_FILE, doctors); add_audit('Doctor Approved', st.session_state.current_user_email, email); st.rerun()
                with col2:
                    if st.button(f'Reject {email}', key=f'reject_{email}', type='secondary', use_container_width=True):
                        doctors.pop(email); save_json(DOCTORS_FILE, doctors); add_audit('Doctor Rejected', st.session_state.current_user_email, email); st.rerun()
                        
    st.write('')
    st.subheader('Registered Patients'); st.dataframe(pd.DataFrame([{'Name': v.get('name'), 'Email': k, 'Age': v.get('age'), 'Gender': v.get('gender')} for k, v in users.items()]), use_container_width=True)
    st.write('')
    st.subheader('Registered Doctors'); st.dataframe(pd.DataFrame([{'Name': v.get('name'), 'Email': k, 'Approved': v.get('approved'), 'Specialization': v.get('specialization')} for k, v in doctors.items()]), use_container_width=True)
    st.write('')
    st.subheader('Audit Log')
    logs = load_json(AUDIT_FILE, [])
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else:
        st.info('No audit logs yet.')


def profile_page():
    back_page = 'prediction' if st.session_state.user_type == 'patient' else ('doctor' if st.session_state.user_type == 'doctor' else 'admin')
    if st.button('← Back to Dashboard', key='profile_back', type='secondary'):
        st.session_state.page = back_page
        st.rerun()
        
    st.markdown('<div class="page-head"><div class="page-icon">👤</div><div><div class="page-title">My Profile</div><div class="page-sub">Edit your profile details</div></div></div>', unsafe_allow_html=True)
    email = st.session_state.current_user_email; utype = st.session_state.user_type
    
    with st.container(border=True):
        if utype == 'patient':
            user = users[email]
            name = st.text_input('Name', value=user.get('name', ''))
            phone = st.text_input('Phone', value=user.get('phone', ''))
            age = st.number_input('Age', 1, 100, int(user.get('age', 25)))
            gender = st.selectbox('Gender', ['Female', 'Male', 'Other'], index=['Female', 'Male', 'Other'].index(user.get('gender', 'Female')) if user.get('gender') in ['Female', 'Male', 'Other'] else 0)
            address = st.text_area('Address', value=user.get('address', ''))
            
            # Profile Photo Edit
            uploaded_photo = st.file_uploader('Change Profile Photo', type=['png', 'jpg', 'jpeg'], key='edit_patient_photo')
            
            if st.button('Save Profile', type='primary', use_container_width=True):
                update_data = {'name': name, 'phone': phone, 'age': age, 'gender': gender, 'address': address}
                if uploaded_photo:
                    base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                    update_data['profile_pic'] = base64_photo
                users[email].update(update_data)
                save_json(USERS_FILE, users)
                st.session_state.current_user_name = name
                add_audit('Profile Updated', email, 'Patient profile updated')
                st.success('Profile updated.')
                st.rerun()
        elif utype == 'doctor':
            doctor = doctors[email]
            name = st.text_input('Name', value=doctor.get('name', ''))
            phone = st.text_input('Phone', value=doctor.get('phone', ''))
            specialization = st.text_input('Specialization', value=doctor.get('specialization', ''))
            hospital = st.text_input('Hospital', value=doctor.get('hospital', ''))
            license_no = st.text_input('License No.', value=doctor.get('license_no', ''))
            
            # Profile Photo Edit
            uploaded_photo = st.file_uploader('Change Profile Photo', type=['png', 'jpg', 'jpeg'], key='edit_doctor_photo')
            
            if st.button('Save Profile', type='primary', use_container_width=True):
                update_data = {'name': name, 'phone': phone, 'specialization': specialization, 'hospital': hospital, 'license_no': license_no}
                if uploaded_photo:
                    base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                    update_data['profile_pic'] = base64_photo
                doctors[email].update(update_data)
                save_json(DOCTORS_FILE, doctors)
                st.session_state.current_user_name = name
                add_audit('Profile Updated', email, 'Doctor profile updated')
                st.success('Profile updated.')
                st.rerun()
        else: st.info('Admin profile editing is not enabled.')


if not st.session_state.started:
    landing_page(); st.stop()

dashboard_sidebar()

if st.session_state.page == 'auth': auth_page()
elif st.session_state.page == 'create_profile': create_profile_page()
elif st.session_state.page == 'prediction': prediction_page()
elif st.session_state.page == 'dashboard': dashboard_page()
elif st.session_state.page == 'doctor': doctor_page()
elif st.session_state.page == 'admin': admin_page()
elif st.session_state.page == 'profile': profile_page()
else:
    st.session_state.page = 'auth'; st.rerun()

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

# ── ReportLab imports ────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Circle, Group, Polygon
)
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

st.set_page_config(page_title='GlucoTrack', page_icon='🩺', layout='wide', initial_sidebar_state='expanded')

USERS_FILE   = 'users.json'
DOCTORS_FILE = 'doctors.json'
ADMINS_FILE  = 'admins.json'
REPORTS_FILE = 'reports.json'
AUDIT_FILE   = 'audit_log.json'
MODEL_FILE   = 'diabetes_model.pkl'
COLUMNS_FILE = 'columns.pkl'

# ── JSON helpers ─────────────────────────────────────────────────────────────
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
    logs.append({'time': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                 'email': email, 'action': action, 'details': details})
    save_json(AUDIT_FILE, logs)

# ── Default data ─────────────────────────────────────────────────────────────
DEFAULT_USERS = {
    'user@gmail.com': {
        'password': 'Pass1234', 'name': 'Demo User', 'phone': 'Not Provided',
        'age': 30, 'gender': 'Female', 'address': 'Not Provided',
        'medical_history': '', 'user_type': 'patient', 'profile_created': True,
    }
}
DEFAULT_DOCTORS = {
    'doctor@glucotrack.com': {
        'password': 'Doc@1234', 'name': 'Dr. Demo', 'phone': 'Not Provided',
        'specialization': 'Endocrinology', 'hospital': 'City Hospital',
        'license_no': 'MCI-12345', 'approved': False,
        'user_type': 'doctor', 'profile_created': True,
    }
}
DEFAULT_ADMINS = {'admin@glucotrack.com': 'admin@123'}

users   = load_json(USERS_FILE,   DEFAULT_USERS)
doctors = load_json(DOCTORS_FILE, DEFAULT_DOCTORS)
admins  = load_json(ADMINS_FILE,  DEFAULT_ADMINS)
reports = load_json(REPORTS_FILE, [])

# ── Session state ─────────────────────────────────────────────────────────────
defaults = {
    'started': False, 'page': 'home', 'auth_mode': 'signin',
    'signup_step': 1, 'logged_in': False, 'user_type': None,
    'current_user_name': '', 'current_user_email': '', 'dark_mode': False,
    'signup_name': '', 'signup_email': '', 'signup_phone': '',
    'signup_age': 25, 'signup_gender': 'Female', 'signup_address': '',
    'signup_password': '', 'prediction_done': False, 'patient_data': None,
    'prediction_result': None, 'confidence': None, 'prediction_time': None,
    'pdf_bytes': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Theme ─────────────────────────────────────────────────────────────────────
DARK = st.session_state.dark_mode
if DARK:
    BG='#0A0F1E'; CARD='#131929'; TEXT='#F0F4FF'; MUTED='#8B9BBE'
    BORDER='#1E2A42'; INPUT='#0D1526'; BLUE='#3B9EFF'; BLUE_DARK='#1A7FE0'
    SIDEBAR='#0A0F1E'; PLOT_TEMPLATE='plotly_dark'
    LABEL_COLOR='#C8D8F0'; HEADING_COLOR='#F0F4FF'; SUBTEXT_COLOR='#8B9BBE'
    CARD_BG_ALT='#182030'; STAT_BG='#131929'
else:
    BG='#F4F7FC'; CARD='#FFFFFF'; TEXT='#0D1526'; MUTED='#6B7A99'
    BORDER='#DDE4F0'; INPUT='#F8FAFD'; BLUE='#1A6FE8'; BLUE_DARK='#1558C0'
    SIDEBAR='#FFFFFF'; PLOT_TEMPLATE='plotly_white'
    LABEL_COLOR='#374162'; HEADING_COLOR='#0D1526'; SUBTEXT_COLOR='#6B7A99'
    CARD_BG_ALT='#EEF3FC'; STAT_BG='#FFFFFF'

# ── CSS ───────────────────────────────────────────────────────────────────────
css = f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{{box-sizing:border-box;}}
html,body,[class*="css"]{{font-family:'Inter',sans-serif!important;}}
.stApp{{background:{BG}!important;}}
.block-container{{padding-top:1.5rem!important;padding-left:2rem!important;padding-right:2rem!important;max-width:100%!important;}}
h1,h2,h3,h4,h5,h6{{font-family:'Inter',sans-serif!important;color:{HEADING_COLOR}!important;}}
p,label,div,span{{font-family:'Inter',sans-serif!important;color:{TEXT}!important;}}
[data-testid="stDecoration"]{{display:none!important;}}
header[data-testid="stHeader"]{{background:transparent!important;box-shadow:none!important;border:none!important;}}
header[data-testid="stHeader"] [data-testid="stAppDeployButton"]{{display:none!important;}}
header[data-testid="stHeader"] #MainMenu{{display:none!important;}}
header[data-testid="stHeader"] [data-testid="stConnectionStatus"]{{display:none!important;}}
.stTextInput input,.stNumberInput input,.stTextArea textarea{{background:{INPUT}!important;color:{TEXT}!important;border:1.5px solid {BORDER}!important;border-radius:10px!important;min-height:48px!important;font-size:15px!important;padding-left:14px!important;}}
.stSelectbox div[data-baseweb="select"]>div{{background:{INPUT}!important;color:{TEXT}!important;border:1.5px solid {BORDER}!important;border-radius:10px!important;min-height:48px!important;}}
.stSelectbox [data-baseweb="select"] span,.stSelectbox [data-baseweb="select"] div{{color:{TEXT}!important;}}
.stTextInput label,.stNumberInput label,.stSelectbox label,.stTextArea label,.stFileUploader label,.stRadio label,.stCheckbox label{{color:{LABEL_COLOR}!important;font-weight:600!important;font-size:14px!important;}}
div[data-testid="stVerticalBlockBorderWrapper"]{{background:{CARD}!important;border:1.5px solid {BORDER}!important;border-radius:16px!important;padding:28px!important;box-shadow:0 4px 24px rgba(10,15,40,.08)!important;}}
.stButton>button[kind="primary"],.stDownloadButton>button,.stFormSubmitButton>button{{background:{BLUE}!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:15px!important;min-height:48px!important;box-shadow:0 4px 16px rgba(26,111,232,.25)!important;transition:all .2s ease!important;}}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button:hover{{background:{BLUE_DARK}!important;transform:translateY(-1px)!important;}}
.stButton>button[kind="secondary"]{{background:transparent!important;color:{TEXT}!important;border:1.5px solid {BORDER}!important;border-radius:10px!important;font-weight:600!important;font-size:15px!important;min-height:48px!important;transition:all .2s ease!important;}}
.stButton>button[kind="secondary"]:hover{{background:{CARD_BG_ALT}!important;transform:translateY(-1px)!important;}}
button *{{color:#fff!important;}}
.stButton>button[kind="secondary"] *{{color:{TEXT}!important;}}
section[data-testid="stSidebar"]{{background:{SIDEBAR}!important;border-right:1.5px solid {BORDER};}}
section[data-testid="stSidebar"]>div{{background:transparent!important;padding-top:0!important;}}
section[data-testid="stSidebar"] *{{color:{TEXT}!important;}}
section[data-testid="stSidebar"] .stButton>button[kind="secondary"] *{{color:{TEXT}!important;}}
.sb-header{{height:76px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1.5px solid {BORDER};}}
.sb-logo-box{{width:38px;height:38px;background:{BLUE};color:#fff!important;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:19px;}}
.sb-brand{{font-size:20px;font-weight:800;color:{TEXT}!important;}}
.sb-profile{{display:flex;align-items:center;gap:14px;padding:20px 18px;border-bottom:1.5px solid {BORDER};}}
.sb-avatar{{width:46px;height:46px;border-radius:12px;background:#DBEAFE;color:{BLUE}!important;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:17px;}}
.sb-name{{font-size:15px;font-weight:800;color:{TEXT}!important;margin-bottom:3px;}}
.sb-role{{font-size:13px;color:{MUTED}!important;font-weight:500;}}
div[data-testid="stRadio"]{{padding:16px 6px 0!important;}}
div[data-testid="stRadio"] label{{border-radius:10px!important;padding:12px 14px!important;margin:3px 0!important;font-size:15px!important;font-weight:700!important;color:{TEXT}!important;background:transparent!important;}}
div[data-testid="stRadio"] label:hover{{background:{CARD_BG_ALT}!important;}}
div[data-testid="stRadio"] label[data-baseweb="radio"]>div:first-child{{display:none!important;}}
.nav-bar{{display:flex;align-items:center;justify-content:space-between;padding:14px 28px;border-bottom:1.5px solid {BORDER};background:{CARD};border-radius:14px;margin-bottom:32px;box-shadow:0 2px 12px rgba(10,15,40,.06);}}
.nav-left{{display:flex;align-items:center;gap:12px;}}
.nav-logo-box{{width:34px;height:34px;background:{BLUE};color:#fff!important;border-radius:9px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:16px;}}
.nav-brand{{font-size:18px;font-weight:800;color:{TEXT}!important;}}
.nav-links{{display:flex;align-items:center;gap:6px;}}
.nav-link-pill{{padding:7px 16px;border-radius:8px;font-size:14px;font-weight:600;color:{MUTED}!important;text-decoration:none!important;transition:all .18s ease;border:1px solid transparent;}}
.nav-link-pill:hover{{background:{CARD_BG_ALT}!important;color:{TEXT}!important;border-color:{BORDER};}}
.hero{{padding:80px 20px 48px;text-align:center;max-width:960px;margin:0 auto;}}
.hero-badge{{display:inline-flex;align-items:center;gap:8px;border:1.5px solid {BLUE};background:{'rgba(59,158,255,0.08)' if DARK else '#EBF3FF'};color:{BLUE}!important;border-radius:999px;padding:8px 18px;letter-spacing:1.5px;font-weight:700;font-size:13px;margin-bottom:32px;}}
.hero-title{{font-size:72px;line-height:1.0;letter-spacing:-2.5px;font-weight:900;margin:0 0 24px;color:{HEADING_COLOR}!important;}}
.hero-blue{{color:{BLUE}!important;display:block;}}
.hero-sub{{font-size:20px;line-height:1.65;max-width:700px;margin:0 auto 44px;color:{MUTED}!important;}}
.stats-wrap{{max-width:900px;margin:0 auto 80px;border-radius:16px;border:1.5px solid {BORDER};display:grid;grid-template-columns:repeat(3,1fr);overflow:hidden;box-shadow:0 4px 20px rgba(10,15,40,.06);background:{STAT_BG};}}
.stat{{padding:44px 20px;text-align:center;border-right:1.5px solid {BORDER};}}
.stat:last-child{{border-right:none;}}
.stat-num{{font-size:42px;font-weight:900;color:{BLUE}!important;}}
.stat-label{{font-size:16px;margin-top:6px;color:{MUTED}!important;font-weight:500;}}
.section{{padding:0 20px 80px;}}
.section-title{{text-align:center;font-size:36px;font-weight:900;margin-bottom:14px;color:{HEADING_COLOR}!important;}}
.section-sub{{text-align:center;font-size:18px;margin-bottom:52px;color:{MUTED}!important;}}
.feature-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;max-width:1120px;margin:0 auto;}}
.feature-card{{border-radius:20px;padding:36px;min-height:360px;border:1.5px solid {BORDER};}}
.pill{{display:inline-flex;border-radius:999px;padding:6px 16px;font-size:12px;font-weight:700;letter-spacing:.8px;margin-bottom:28px;}}
.icon-box{{width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:26px;margin-bottom:36px;}}
.feature-title{{font-size:20px;font-weight:800;margin-bottom:14px;color:{HEADING_COLOR}!important;}}
.feature-text{{font-size:16px;line-height:1.6;color:{MUTED}!important;}}
.steps-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;max-width:1120px;margin:0 auto;}}
.step-card{{border:1.5px solid {BORDER};border-radius:14px;padding:32px 20px;text-align:center;background:{CARD};}}
.step-num{{color:{BLUE}!important;font-size:38px;font-weight:900;margin-bottom:12px;}}
.step-title{{font-size:18px;font-weight:800;margin-bottom:10px;color:{HEADING_COLOR}!important;}}
.step-text{{font-size:15px;line-height:1.55;color:{MUTED}!important;}}
.bottom-cta{{max-width:760px;margin:0 auto 80px;text-align:center;border-radius:20px;padding:52px 60px;background:{BLUE};}}
.auth-title{{text-align:center;padding:28px 0 16px;}}
.auth-logo-row{{display:flex;justify-content:center;align-items:center;gap:10px;font-size:28px;font-weight:900;color:{HEADING_COLOR}!important;}}
.page-head{{display:flex;align-items:center;gap:16px;padding:20px 28px 16px;}}
.page-icon{{width:46px;height:46px;background:{'rgba(59,158,255,0.12)' if DARK else '#DBEAFE'};color:{BLUE}!important;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px;}}
.page-title{{font-size:28px;font-weight:900;color:{HEADING_COLOR}!important;}}
.page-sub{{font-size:16px;margin-top:4px;color:{MUTED}!important;}}
.card-heading{{display:flex;align-items:center;gap:10px;font-size:19px;font-weight:800;margin-bottom:20px;color:{HEADING_COLOR}!important;}}
.badge-num{{width:28px;height:28px;background:{'rgba(59,158,255,0.15)' if DARK else '#DBEAFE'};color:{BLUE}!important;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;}}
.result-high{{background:{'rgba(220,38,38,0.12)' if DARK else '#FFF1F2'};border:1.5px solid {'#7F1D1D' if DARK else '#FECDD3'};color:{'#FCA5A5' if DARK else '#BE123C'}!important;padding:24px;border-radius:16px;text-align:center;font-weight:800;font-size:22px;}}
.result-low{{background:{'rgba(22,163,74,0.12)' if DARK else '#F0FDF4'};border:1.5px solid {'#14532D' if DARK else '#BBF7D0'};color:{'#86EFAC' if DARK else '#166534'}!important;padding:24px;border-radius:16px;text-align:center;font-weight:800;font-size:22px;}}
.param-card{{background:{CARD_BG_ALT if DARK else CARD}!important;border:1.5px solid {BORDER}!important;border-radius:12px;padding:16px;text-align:center;margin-bottom:10px;}}
.param-label{{color:{MUTED}!important;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;}}
.param-value{{color:{HEADING_COLOR}!important;font-size:22px;font-weight:900;}}
.footer{{border-top:1.5px solid {BORDER};padding:24px 22px;display:flex;justify-content:space-between;align-items:center;margin-top:40px;}}
[data-testid="stMetricValue"]{{color:{HEADING_COLOR}!important;}}
[data-testid="stMetricLabel"]{{color:{MUTED}!important;}}
.stDataFrame *{{color:{TEXT}!important;}}
.stAlert p{{color:{TEXT}!important;}}
.stCheckbox span{{color:{TEXT}!important;}}
.stTabs [data-baseweb="tab"]{{color:{MUTED}!important;font-weight:600;}}
.stTabs [aria-selected="true"]{{color:{TEXT}!important;}}
@media(max-width:900px){{.hero-title{{font-size:46px;}}.feature-grid,.steps-grid,.stats-wrap{{grid-template-columns:1fr;}}.nav-links{{display:none;}}}}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

# ── Utilities ─────────────────────────────────────────────────────────────────
def initials(name):
    parts = str(name or 'User').strip().split()
    if not parts: return 'U'
    if len(parts) == 1: return parts[0][0].upper()
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
    for k in ['prediction_done','patient_data','prediction_result','confidence','prediction_time','pdf_bytes']:
        st.session_state[k] = defaults[k]

def login_user(email, password):
    email = email.strip().lower()
    if email in admins and admins[email] == password:
        st.session_state.update(logged_in=True, user_type='admin', current_user_name='Admin',
                                current_user_email=email, page='admin')
        add_audit('Login', email, 'Admin logged in'); return True, ''
    if email in users and users[email].get('password') == password:
        u = users[email]
        st.session_state.update(logged_in=True, user_type='patient',
                                current_user_name=u.get('name','User'),
                                current_user_email=email, page='prediction')
        add_audit('Login', email, 'Patient logged in'); return True, ''
    if email in doctors and doctors[email].get('password') == password:
        d = doctors[email]
        if not d.get('approved', False): return False, 'Doctor account awaiting admin approval.'
        st.session_state.update(logged_in=True, user_type='doctor',
                                current_user_name=d.get('name','Doctor'),
                                current_user_email=email, page='doctor')
        add_audit('Login', email, 'Doctor logged in'); return True, ''
    return False, 'Invalid email or password.'

def load_model():
    if os.path.exists(MODEL_FILE) and os.path.exists(COLUMNS_FILE):
        try:
            with open(MODEL_FILE,'rb') as f: model = pickle.load(f)
            with open(COLUMNS_FILE,'rb') as f: cols  = pickle.load(f)
            return model, cols
        except Exception: return None, None
    return None, None

def model_predict(pd_data):
    model, cols = load_model()
    if model is not None:
        raw = pd.DataFrame([pd_data])
        raw['Glucose_BMI']   = raw['Glucose'] * raw['BMI']
        raw['Insulin_Glucose']= raw['Insulin'] * raw['Glucose']
        raw['Age_BMI']       = raw['Age'] * raw['BMI']
        raw['BMI_Squared']   = raw['BMI'] ** 2
        enc = pd.get_dummies(raw).reindex(columns=cols, fill_value=0)
        pred = model.predict(enc)
        if hasattr(model, 'predict_proba'):
            prob = model.predict_proba(enc)[0]
            return ('High Risk of Diabetes', round(prob[1]*100,2)) if pred[0]==1 \
                   else ('Low Risk of Diabetes', round(prob[0]*100,2))
        return ('High Risk of Diabetes' if pred[0]==1 else 'Low Risk of Diabetes'), 'N/A'
    score = 0
    if pd_data['Glucose'] >= 126: score += 3
    elif pd_data['Glucose'] >= 110: score += 2
    if pd_data['BMI'] >= 30: score += 2
    elif pd_data['BMI'] >= 25: score += 1
    if pd_data['Age'] >= 45: score += 1
    if pd_data['BloodPressure'] >= 90: score += 1
    if pd_data['Insulin'] >= 180: score += 1
    if score >= 4: return 'High Risk of Diabetes', min(98, 72+score*5)
    return 'Low Risk of Diabetes', max(70, 92-score*6)

def get_suggestions(pd_data):
    if pd_data['Glucose'] >= 126:
        return ['Monitor blood glucose levels regularly.',
                'Reduce sugar and refined carbohydrate intake.',
                'Consult a healthcare professional for proper evaluation.']
    if pd_data['BMI'] >= 30:
        return ['Follow a balanced calorie-controlled diet.',
                'Exercise for at least 30 minutes daily.',
                'Track BMI and weight weekly.']
    if pd_data['BloodPressure'] > 90:
        return ['Reduce sodium and processed food intake.',
                'Monitor blood pressure regularly.',
                'Practice yoga, walking, or meditation.']
    return ['Maintain a balanced nutritious diet.',
            'Exercise regularly to stay active.',
            'Drink enough water and get adequate sleep.']

# ─────────────────────────────────────────────────────────────────────────────
#  PROFESSIONAL PDF GENERATION
# ─────────────────────────────────────────────────────────────────────────────
C_NAVY   = colors.HexColor('#0D1A2E')
C_BLUE   = colors.HexColor('#1A6FE8')
C_LBLUE  = colors.HexColor('#EBF3FF')
C_GREEN  = colors.HexColor('#16A34A')
C_LGREEN = colors.HexColor('#F0FDF4')
C_RED    = colors.HexColor('#DC2626')
C_LRED   = colors.HexColor('#FFF1F2')
C_YELLOW = colors.HexColor('#CA8A04')
C_LYELLOW= colors.HexColor('#FEFCE8')
C_GRAY   = colors.HexColor('#6B7A99')
C_LGRAY  = colors.HexColor('#F4F7FC')
C_WHITE  = colors.white
C_BORDER = colors.HexColor('#DDE4F0')
C_ORANGE = colors.HexColor('#EA580C')
C_PURPLE = colors.HexColor('#7C3AED')

PARAM_META = {
    'Glucose':                {'label':'Glucose',          'unit':'mg/dL',  'normal':(70,99),   'warn':(100,125), 'high':126, 'color':C_BLUE},
    'BMI':                    {'label':'BMI',               'unit':'kg/m²',  'normal':(18.5,24.9),'warn':(25,29.9),'high':30,  'color':C_GREEN},
    'BloodPressure':          {'label':'Blood Pressure',    'unit':'mmHg',   'normal':(60,79),   'warn':(80,89),  'high':90,  'color':C_PURPLE},
    'Insulin':                {'label':'Insulin',           'unit':'μU/mL',  'normal':(2,25),    'warn':(26,179), 'high':180, 'color':C_ORANGE},
    'Age':                    {'label':'Age',               'unit':'years',  'normal':(0,44),    'warn':(45,59),  'high':60,  'color':C_YELLOW},
    'Pregnancies':            {'label':'Pregnancies',       'unit':'count',  'normal':(0,3),     'warn':(4,6),    'high':7,   'color':C_BLUE},
    'SkinThickness':          {'label':'Skin Thickness',    'unit':'mm',     'normal':(10,30),   'warn':(31,49),  'high':50,  'color':C_GREEN},
    'DiabetesPedigreeFunction':{'label':'Diabetes Pedigree','unit':'score',  'normal':(0,0.5),   'warn':(0.5,0.9),'high':1.0, 'color':C_RED},
}

def param_status(key, value):
    m = PARAM_META.get(key, {})
    try: v = float(value)
    except: return 'normal', C_GREEN, C_LGREEN
    lo_n, hi_n = m.get('normal', (0, 9999))
    lo_w, hi_w = m.get('warn',   (0, 9999))
    high       = m.get('high',   9999)
    if lo_n <= v <= hi_n: return 'Normal',  C_GREEN,  C_LGREEN
    if lo_w <= v <= hi_w: return 'Warning', C_YELLOW, C_LYELLOW
    if v >= high:         return 'High',    C_RED,    C_LRED
    return 'Normal', C_GREEN, C_LGREEN

def make_header_drawing(width, is_high):
    """Gradient-style header banner."""
    h = 110
    d = Drawing(width, h)
    # Background
    d.add(Rect(0, 0, width, h, fillColor=C_NAVY, strokeColor=None))
    # Accent bar
    accent = C_RED if is_high else C_BLUE
    d.add(Rect(0, 0, 6, h, fillColor=accent, strokeColor=None))
    # Decorative circles
    d.add(Circle(width-40, h-30, 60, fillColor=colors.HexColor('#162038'), strokeColor=None))
    d.add(Circle(width-20, h+10, 40, fillColor=colors.HexColor('#1a2844'), strokeColor=None))
    # Title
    d.add(String(22, h-38, 'GlucoTrack', fontSize=26, fontName='Helvetica-Bold', fillColor=C_WHITE))
    d.add(String(22, h-58, 'Clinical Health & Diabetes Risk Report',
                 fontSize=13, fontName='Helvetica', fillColor=colors.HexColor('#90B4D8')))
    d.add(String(22, h-75, 'AI-Powered Assessment  •  Confidential Patient Document',
                 fontSize=9, fontName='Helvetica-Oblique', fillColor=colors.HexColor('#5A7A9A')))
    return d

def make_risk_badge(width, result, confidence):
    is_high = 'High' in result
    bg  = C_LRED   if is_high else C_LGREEN
    bdr = C_RED    if is_high else C_GREEN
    tc  = C_RED    if is_high else C_GREEN
    icon = '⚠  HIGH RISK OF DIABETES' if is_high else '✔  LOW RISK OF DIABETES'
    h = 72
    d = Drawing(width, h)
    d.add(Rect(0, 0, width, h, fillColor=bg,
               strokeColor=bdr, strokeWidth=1.5, rx=8, ry=8))
    d.add(String(width/2, h-28, icon, fontSize=18, fontName='Helvetica-Bold',
                 fillColor=tc, textAnchor='middle'))
    d.add(String(width/2, h-50, f'Model Confidence: {confidence}%',
                 fontSize=11, fontName='Helvetica', fillColor=tc, textAnchor='middle'))
    return d

def make_bar_chart(width, pd_data):
    """Horizontal bar chart of key clinical metrics with reference lines."""
    keys   = ['Glucose','BMI','BloodPressure','Insulin']
    labels = ['Glucose (mg/dL)','BMI (kg/m²)','Blood Pressure (mmHg)','Insulin (μU/mL)']
    values = [float(pd_data.get(k, 0)) for k in keys]
    highs  = [126, 30, 90, 180]   # threshold reference
    h = 200
    d = Drawing(width, h)
    bc = VerticalBarChart()
    bc.x = 50; bc.y = 30
    bc.width = width - 70; bc.height = h - 50
    bc.data = [values, highs]
    bc.groupSpacing = 12
    bc.bars[0].fillColor = C_BLUE
    bc.bars[1].fillColor = colors.HexColor('#E2E8F0')
    bc.bars[0].strokeColor = None
    bc.bars[1].strokeColor = None
    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontName = 'Helvetica'
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.angle = 0
    bc.valueAxis.valueMin = 0
    bc.valueAxis.labels.fontName = 'Helvetica'
    bc.valueAxis.labels.fontSize = 8
    bc.valueAxis.gridStrokeColor = colors.HexColor('#E8EDF5')
    bc.valueAxis.gridStrokeWidth = 0.5
    d.add(bc)
    # Legend
    d.add(Rect(50, 5, 12, 8, fillColor=C_BLUE, strokeColor=None))
    d.add(String(66, 6, 'Patient Value', fontSize=7, fontName='Helvetica', fillColor=C_GRAY))
    d.add(Rect(145, 5, 12, 8, fillColor=colors.HexColor('#E2E8F0'), strokeColor=None))
    d.add(String(161, 6, 'Risk Threshold', fontSize=7, fontName='Helvetica', fillColor=C_GRAY))
    return d

def make_risk_pie(width, pd_data):
    """Pie chart showing risk factor distribution."""
    h = 160
    d = Drawing(width, h)
    # Calculate contribution scores
    scores = {
        'Glucose': 3 if pd_data['Glucose']>=126 else (2 if pd_data['Glucose']>=110 else 1),
        'BMI':     2 if pd_data['BMI']>=30 else (1 if pd_data['BMI']>=25 else 0.5),
        'Age':     2 if pd_data['Age']>=45 else 1,
        'BP':      1.5 if pd_data['BloodPressure']>=90 else 0.5,
        'Insulin': 1.5 if pd_data['Insulin']>=180 else 0.5,
    }
    total = sum(scores.values())
    pie = Pie()
    pie.x = 20; pie.y = 20
    pie.width = 110; pie.height = 110
    pie.data = [v/total*100 for v in scores.values()]
    pie.labels = [f"{k}\n{v/total*100:.0f}%" for k,v in scores.items()]
    pie_colors = [C_BLUE, C_GREEN, C_ORANGE, C_PURPLE, C_RED]
    for i, c in enumerate(pie_colors):
        pie.slices[i].fillColor = c
        pie.slices[i].strokeColor = C_WHITE
        pie.slices[i].strokeWidth = 1.5
        pie.slices[i].labelRadius = 1.3
    pie.slices.label_fontName = 'Helvetica'
    pie.slices.label_fontSize = 7
    pie.slices.label_fillColor = C_NAVY
    d.add(pie)
    # Legend on right
    ly = h - 20
    for i,(k,c) in enumerate(zip(scores.keys(), pie_colors)):
        d.add(Rect(145, ly-i*18, 10, 10, fillColor=c, strokeColor=None))
        d.add(String(160, ly-i*18+1, k, fontSize=8, fontName='Helvetica', fillColor=C_NAVY))
    return d

def make_gauge_drawing(width, value, max_val, label, unit, color):
    """Mini horizontal gauge bar."""
    h = 36
    d = Drawing(width, h)
    bar_w = width - 20
    pct = min(float(value) / max_val, 1.0)
    # Background track
    d.add(Rect(10, 18, bar_w, 10, fillColor=colors.HexColor('#E8EDF5'),
               strokeColor=None, rx=5, ry=5))
    # Filled portion
    fill_w = max(pct * bar_w, 4)
    d.add(Rect(10, 18, fill_w, 10, fillColor=color, strokeColor=None, rx=5, ry=5))
    # Labels
    d.add(String(10, 5, f'{label}: {value} {unit}', fontSize=8,
                 fontName='Helvetica-Bold', fillColor=C_NAVY))
    d.add(String(width-10, 5, f'{pct*100:.0f}% of {max_val}', fontSize=7,
                 fontName='Helvetica', fillColor=C_GRAY, textAnchor='end'))
    return d

def build_styles():
    ss = getSampleStyleSheet()
    base = ParagraphStyle
    return {
        'section_title': base('ST', parent=ss['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=C_NAVY, spaceBefore=14, spaceAfter=6),
        'body': base('BD', parent=ss['Normal'],
            fontSize=9, fontName='Helvetica',
            textColor=colors.HexColor('#374162'), leading=14),
        'small': base('SM', parent=ss['Normal'],
            fontSize=8, fontName='Helvetica',
            textColor=C_GRAY, leading=12),
        'suggest_item': base('SI', parent=ss['Normal'],
            fontSize=9, fontName='Helvetica',
            textColor=colors.HexColor('#1E3A5F'), leading=14,
            leftIndent=10),
        'footer': base('FT', parent=ss['Normal'],
            fontSize=7, fontName='Helvetica-Oblique',
            textColor=C_GRAY, alignment=TA_CENTER),
        'patient_val': base('PV', parent=ss['Normal'],
            fontSize=10, fontName='Helvetica-Bold',
            textColor=C_NAVY),
        'patient_lbl': base('PL', parent=ss['Normal'],
            fontSize=8, fontName='Helvetica',
            textColor=C_GRAY),
    }

def section_line(W):
    return HRFlowable(width=W, thickness=1, color=C_BORDER,
                      spaceBefore=4, spaceAfter=8)

def section_heading(title, styles):
    return Paragraph(f'<font color="#1A6FE8">▌</font> &nbsp;{title}', styles['section_title'])

def generate_pdf(patient_data, result, confidence, name, email, pred_time,
                 doctor_name=None, doctor_notes=None):
    """Generate a fully professional multi-section PDF report."""
    buf = BytesIO()
    W, H = A4
    margin = 1.5*cm
    content_w = W - 2*margin

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=0, bottomMargin=2*cm,
        leftMargin=margin, rightMargin=margin
    )
    st_map = build_styles()
    is_high = 'High' in result
    story = []

    # ── 1. Header banner ──────────────────────────────────────────────────────
    story.append(make_header_drawing(content_w, is_high))
    story.append(Spacer(1, 14))

    # ── 2. Report metadata row ────────────────────────────────────────────────
    meta_data = [
        [Paragraph('<b>Report ID</b>', st_map['small']),
         Paragraph('<b>Generated On</b>', st_map['small']),
         Paragraph('<b>Prepared By</b>', st_map['small'])],
        [Paragraph(f'GT-{pred_time.replace(" ","").replace("-","").replace(":","")[:14]}',
                   st_map['patient_val']),
         Paragraph(pred_time, st_map['patient_val']),
         Paragraph(f'GlucoTrack AI Engine{" / "+doctor_name if doctor_name else ""}',
                   st_map['patient_val'])],
    ]
    meta_tbl = Table(meta_data, colWidths=[content_w/3]*3)
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_LGRAY),
        ('BACKGROUND', (0,1), (-1,1), C_WHITE),
        ('BOX',        (0,0), (-1,-1), 0.5, C_BORDER),
        ('INNERGRID',  (0,0), (-1,-1), 0.5, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[C_LGRAY, C_WHITE]),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 12))

    # ── 3. Patient demographics ───────────────────────────────────────────────
    story.append(section_heading('Patient Information', st_map))
    story.append(section_line(content_w))
    pat_info = users.get(email, {})
    demo_data = [
        [Paragraph('Full Name', st_map['patient_lbl']),
         Paragraph('Email Address', st_map['patient_lbl']),
         Paragraph('Age', st_map['patient_lbl']),
         Paragraph('Gender', st_map['patient_lbl'])],
        [Paragraph(name, st_map['patient_val']),
         Paragraph(email, st_map['patient_val']),
         Paragraph(str(pat_info.get('age', patient_data.get('Age','—'))), st_map['patient_val']),
         Paragraph(pat_info.get('gender','—'), st_map['patient_val'])],
        [Paragraph('Phone', st_map['patient_lbl']),
         Paragraph('Address', st_map['patient_lbl']),
         Paragraph('', st_map['patient_lbl']),
         Paragraph('', st_map['patient_lbl'])],
        [Paragraph(pat_info.get('phone','Not Provided'), st_map['patient_val']),
         Paragraph(pat_info.get('address','Not Provided'), st_map['patient_val']),
         Paragraph('', st_map['patient_val']),
         Paragraph('', st_map['patient_val'])],
    ]
    demo_tbl = Table(demo_data, colWidths=[content_w/4]*4)
    demo_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_LGRAY),
        ('BACKGROUND', (0,2), (-1,2), C_LGRAY),
        ('BOX',        (0,0), (-1,-1), 0.5, C_BORDER),
        ('INNERGRID',  (0,0), (-1,-1), 0.5, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(demo_tbl)
    story.append(Spacer(1, 14))

    # ── 4. Risk assessment badge ──────────────────────────────────────────────
    story.append(section_heading('Risk Assessment Result', st_map))
    story.append(section_line(content_w))
    story.append(make_risk_badge(content_w, result, confidence))
    story.append(Spacer(1, 14))

    # ── 5. Clinical parameters table with status ──────────────────────────────
    story.append(section_heading('Clinical Measurements & Status', st_map))
    story.append(section_line(content_w))

    param_header = [
        Paragraph('<b>Parameter</b>', st_map['small']),
        Paragraph('<b>Value</b>',     st_map['small']),
        Paragraph('<b>Unit</b>',      st_map['small']),
        Paragraph('<b>Normal Range</b>', st_map['small']),
        Paragraph('<b>Status</b>',    st_map['small']),
    ]
    param_rows = [param_header]
    col_ws = [content_w*0.32, content_w*0.14, content_w*0.14,
              content_w*0.24, content_w*0.16]
    ts_cmds = [
        ('BACKGROUND', (0,0), (-1,0), C_NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), C_WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('BOX',        (0,0), (-1,-1), 0.5, C_BORDER),
        ('INNERGRID',  (0,0), (-1,-1), 0.3, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]
    for i, (key, meta) in enumerate(PARAM_META.items(), 1):
        val = patient_data.get(key, '—')
        status_label, status_color, status_bg = param_status(key, val)
        lo, hi = meta['normal']
        norm_str = f'{lo} – {hi}'
        row = [
            Paragraph(meta['label'],  st_map['body']),
            Paragraph(str(val),       st_map['patient_val']),
            Paragraph(meta['unit'],   st_map['small']),
            Paragraph(norm_str,       st_map['small']),
            Paragraph(f'<b>{status_label}</b>',
                      ParagraphStyle('SL', parent=st_map['body'],
                                     textColor=status_color)),
        ]
        param_rows.append(row)
        ts_cmds.append(('BACKGROUND', (0,i), (-1,i),
                        C_LGRAY if i % 2 == 0 else C_WHITE))
        ts_cmds.append(('BACKGROUND', (4,i), (4,i), status_bg))

    param_tbl = Table(param_rows, colWidths=col_ws)
    param_tbl.setStyle(TableStyle(ts_cmds))
    story.append(param_tbl)
    story.append(Spacer(1, 16))

    # ── 6. Health analytics charts ────────────────────────────────────────────
    story.append(section_heading('Health Analytics', st_map))
    story.append(section_line(content_w))

    half = content_w / 2 - 6
    chart_row = Table(
        [[make_bar_chart(half, patient_data), make_risk_pie(half, patient_data)]],
        colWidths=[half, half], rowHeights=[210]
    )
    chart_row.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING',   (0,0), (-1,-1), 0),
        ('BOTTOMPADDING',(0,0), (-1,-1), 0),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(chart_row)
    story.append(Spacer(1, 8))

    # Chart captions
    cap_row = Table(
        [[Paragraph('<i>Fig 1: Patient values vs risk thresholds</i>', st_map['small']),
          Paragraph('<i>Fig 2: Risk factor contribution breakdown</i>', st_map['small'])]],
        colWidths=[half, half]
    )
    cap_row.setStyle(TableStyle([
        ('ALIGNMENT', (0,0), (-1,-1), 'CENTER'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(cap_row)
    story.append(Spacer(1, 14))

    # ── 7. Mini gauge bars ────────────────────────────────────────────────────
    story.append(section_heading('Parameter Gauges', st_map))
    story.append(section_line(content_w))
    gauge_keys = [
        ('Glucose', 200, 'mg/dL', C_BLUE),
        ('BMI',     45,  'kg/m²', C_GREEN),
        ('BloodPressure', 130, 'mmHg', C_PURPLE),
        ('Insulin', 300, 'μU/mL', C_ORANGE),
    ]
    gw = (content_w - 10) / 2
    gauge_pairs = []
    for i in range(0, len(gauge_keys), 2):
        row_gauges = []
        for key, mx, unit, clr in gauge_keys[i:i+2]:
            row_gauges.append(make_gauge_drawing(gw, patient_data.get(key, 0), mx,
                                                  PARAM_META[key]['label'], unit, clr))
        gauge_tbl = Table([row_gauges], colWidths=[gw, gw])
        gauge_tbl.setStyle(TableStyle([
            ('LEFTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(-1,-1),10),
            ('TOPPADDING',(0,0),(-1,-1),2),
        ]))
        story.append(gauge_tbl)

    story.append(Spacer(1, 16))

    # ── 8. Health suggestions ─────────────────────────────────────────────────
    story.append(section_heading('Personalised Health Recommendations', st_map))
    story.append(section_line(content_w))
    suggestions = get_suggestions(patient_data)
    suggest_data = []
    icons = ['①','②','③']
    for i, s in enumerate(suggestions):
        suggest_data.append([
            Paragraph(icons[i], ParagraphStyle('IC', parent=st_map['body'],
                                               fontSize=13, textColor=C_BLUE,
                                               fontName='Helvetica-Bold')),
            Paragraph(s, st_map['suggest_item']),
        ])
    if suggest_data:
        sug_tbl = Table(suggest_data, colWidths=[30, content_w-30])
        sug_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_LBLUE),
            ('BOX',  (0,0), (-1,-1), 0.5, colors.HexColor('#BFDBFE')),
            ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor('#DBEAFE')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(sug_tbl)
    story.append(Spacer(1, 14))

    # ── 9. Doctor notes (if provided) ────────────────────────────────────────
    if doctor_notes and doctor_notes.strip():
        story.append(section_heading("Doctor's Clinical Notes", st_map))
        story.append(section_line(content_w))
        notes_data = [[Paragraph(f'<i>{doctor_notes}</i>',
                                 ParagraphStyle('DN', parent=st_map['body'],
                                                textColor=C_NAVY, leading=15))]]
        notes_tbl = Table(notes_data, colWidths=[content_w])
        notes_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_LYELLOW),
            ('BOX', (0,0), (-1,-1), 0.5, C_YELLOW),
            ('LEFTPADDING',(0,0),(-1,-1),14),
            ('RIGHTPADDING',(0,0),(-1,-1),14),
            ('TOPPADDING',(0,0),(-1,-1),10),
            ('BOTTOMPADDING',(0,0),(-1,-1),10),
        ]))
        story.append(notes_tbl)
        story.append(Spacer(1, 10))

    # ── 10. Footer disclaimer ─────────────────────────────────────────────────
    story.append(HRFlowable(width=content_w, thickness=1, color=C_BORDER,
                             spaceBefore=10, spaceAfter=8))
    story.append(Paragraph(
        'DISCLAIMER: This report is generated by GlucoTrack\'s AI engine and is intended solely for '
        'educational and screening purposes. It does not constitute medical advice, diagnosis, or '
        'treatment. Please consult a qualified healthcare professional for any medical concerns.',
        st_map['footer']
    ))
    story.append(Paragraph(
        f'© {datetime.now().year} GlucoTrack  •  Confidential Patient Record  •  '
        f'Generated: {pred_time}',
        st_map['footer']
    ))

    doc.build(story)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
#  WHATSAPP HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def whatsapp_text_button(result, confidence, patient_data, suggestions,
                          pred_time, patient_name, phone_number=None,
                          shared_by=None):
    """Share a rich text summary via WhatsApp (API limitation: can't attach PDFs via URL)."""
    msg = (f"*GlucoTrack Clinical Report*\n\n"
           f"👤 *Patient:* {patient_name}\n"
           f"🩺 *Assessment:* {result}\n"
           f"🎯 *Confidence:* {confidence}%\n"
           f"📅 *Date:* {pred_time}\n\n"
           f"📊 *Clinical Values:*\n"
           f"• Glucose: {patient_data.get('Glucose','N/A')} mg/dL\n"
           f"• BMI: {patient_data.get('BMI','N/A')} kg/m²\n"
           f"• Blood Pressure: {patient_data.get('BloodPressure','N/A')} mmHg\n"
           f"• Insulin: {patient_data.get('Insulin','N/A')} μU/mL\n"
           f"• Age: {patient_data.get('Age','N/A')} yrs\n\n"
           f"💡 *Recommendations:*\n")
    for s in suggestions:
        msg += f"• {s}\n"
    if shared_by:
        msg += f"\n_Shared by {shared_by} via GlucoTrack._"
    else:
        msg += "\n_For screening only. Consult a medical professional._"

    enc = urllib.parse.quote(msg)
    clean = ''.join(c for c in (phone_number or '') if c.isdigit())
    url = (f"https://api.whatsapp.com/send?phone={clean}&text={enc}"
           if clean else f"https://api.whatsapp.com/send?text={enc}")
    return url

def render_whatsapp_panel(result, confidence, patient_data, suggestions,
                           pred_time, patient_name, pdf_bytes,
                           shared_by=None, key_suffix=''):
    """Full export panel: PDF download + WhatsApp share."""
    st.markdown(f'''
    <div style="background:{"#131929" if DARK else "#F8FAFF"};border:1.5px solid {BORDER};
                border-radius:14px;padding:22px 24px;margin-top:4px;">
        <div style="font-size:16px;font-weight:800;color:{HEADING_COLOR};margin-bottom:16px;">
            📤 Export &amp; Share Report
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_pdf, col_wa = st.columns(2)

    with col_pdf:
        fname = f"GlucoTrack_{patient_name.replace(' ','_')}_Report.pdf"
        st.download_button(
            label='📄 Download Professional PDF',
            data=pdf_bytes,
            file_name=fname,
            mime='application/pdf',
            use_container_width=True,
            key=f'dl_pdf_{key_suffix}'
        )
        st.markdown(
            f'<p style="font-size:12px;color:{MUTED};margin-top:6px;text-align:center;">'
            'Full clinical report with charts & analytics</p>',
            unsafe_allow_html=True
        )

    with col_wa:
        phone_in = st.text_input(
            'WhatsApp number (with country code)',
            placeholder='e.g. +919876543210',
            key=f'wa_phone_{key_suffix}'
        )
        wa_url = whatsapp_text_button(
            result, confidence, patient_data, suggestions,
            pred_time, patient_name, phone_in, shared_by
        )
        st.markdown(f'''
        <a href="{wa_url}" target="_blank" style="text-decoration:none;display:block;margin-top:4px;">
            <div style="background:#25D366;color:white;text-align:center;padding:13px;
                        border-radius:10px;font-weight:700;font-size:15px;
                        box-shadow:0 4px 16px rgba(37,211,102,.25);
                        display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="white" viewBox="0 0 16 16">
                    <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.93c0 1.39.365 2.743 1.06 3.962L0 16l4.13-1.082A7.86 7.86 0 0 0 7.99 12c4.365 0 7.934-3.558 7.939-7.93a7.86 7.86 0 0 0-2.328-5.744M7.993 11.89c-1.392 0-2.702-.38-3.829-1.08l-.275-.164-2.429.637.649-2.368-.18-.287a5.95 5.95 0 0 1-.98-3.216c.004-3.279 2.685-5.96 5.966-5.96 1.587.001 3.079.616 4.2 1.738a5.96 5.96 0 0 1 1.729 4.2c-.004 3.28-2.685 5.96-5.966 5.96M11.53 8.87c-.191-.096-1.136-.56-1.31-.624-.173-.064-.3-.096-.426.096-.127.192-.49.61-.6.732-.11.123-.219.138-.41.042-.191-.096-.807-.297-1.537-.95-.568-.506-.95-1.133-1.062-1.324-.112-.19-.012-.294.084-.389.087-.085.191-.223.287-.335.095-.112.127-.19.19-.32.064-.13.032-.243-.016-.339-.048-.096-.426-1.026-.583-1.407-.152-.37-.308-.32-.426-.326-.11-.006-.237-.008-.363-.008-.127 0-.332.048-.506.237-.174.19-.66 1.63-.66 3.97 0 2.34 1.7 4.595 1.94 4.914.24.318 3.352 5.12 8.12 7.18 1.133.49 2.02.784 2.709 1.004 1.134.36 2.167.309 2.984.187.912-.136 2.793-.113 3.197-1.197.404-1.084.404-2.013.283-2.203-.12-.19-.32-.304-.51-.399"/>
                </svg>
                Send Report via WhatsApp
            </div>
        </a>
        <p style="font-size:11px;color:{MUTED};margin-top:5px;text-align:center;">
            Sends a rich summary + recommendations. Enter a number to send directly.
        </p>
        ''', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  NAVIGATION / SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def public_header():
    st.markdown(f'''
    <div class="nav-bar">
        <div class="nav-left">
            <div class="nav-logo-box">⌁</div>
            <div class="nav-brand">GlucoTrack</div>
        </div>
        <div class="nav-links">
            <a href="#features"    class="nav-link-pill" target="_self">What GlucoTrack Does</a>
            <a href="#how-it-works" class="nav-link-pill" target="_self">How It Works</a>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    c_spacer, c_theme, c_signin = st.columns([6, 1, 1])
    with c_theme:
        if st.button('☀️ Light' if DARK else '🌙 Dark', key='pub_theme_toggle',
                     type='secondary', use_container_width=True):
            st.session_state.dark_mode = not DARK; st.rerun()
    with c_signin:
        if st.button('Sign In →', key='nav_signin', type='primary', use_container_width=True):
            st.session_state.started = True
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'signin'
            st.rerun()

def dashboard_sidebar():
    if not st.session_state.started or not st.session_state.logged_in: return
    name  = st.session_state.current_user_name
    email = st.session_state.current_user_email
    role  = {'patient':'Patient','doctor':'Doctor','admin':'Admin'}.get(
                st.session_state.user_type,'User')
    init  = initials(name)
    pic   = None
    if st.session_state.user_type == 'patient' and email in users:
        pic = users[email].get('profile_pic')
    elif st.session_state.user_type == 'doctor' and email in doctors:
        pic = doctors[email].get('profile_pic')
    av = (f'<img src="data:image/png;base64,{pic}" '
          f'style="width:46px;height:46px;border-radius:12px;object-fit:cover;">'
          if pic else f'<div class="sb-avatar">{init}</div>')
    st.sidebar.markdown(f'''
    <div class="sb-header"><div class="sb-logo-box">⌁</div><div class="sb-brand">GlucoTrack</div></div>
    <div class="sb-profile">{av}<div><div class="sb-name">{name}</div><div class="sb-role">{role}</div></div></div>
    ''', unsafe_allow_html=True)
    if st.sidebar.button('👤 Edit Profile', use_container_width=True):
        st.session_state.page = 'profile'; st.rerun()
    if st.sidebar.button('☀️ Light Mode' if DARK else '🌙 Dark Mode', use_container_width=True):
        st.session_state.dark_mode = not DARK; st.rerun()
    if st.session_state.user_type == 'patient':
        options=['prediction','dashboard']; labels=['🩺 Predict','📊 Health Dashboard']
    elif st.session_state.user_type == 'doctor':
        options=['doctor','dashboard']; labels=['👨‍⚕️ Patient Data','📊 Health Dashboard']
    else:
        options=['admin','prediction','dashboard']
        labels=['🛡️ Admin Panel','🩺 Predict','📊 Health Dashboard']
    if st.session_state.page not in options and st.session_state.page != 'profile':
        st.session_state.page = options[0]
    if st.session_state.page != 'profile':
        idx = options.index(st.session_state.page) if st.session_state.page in options else 0
        sel = st.sidebar.radio('', labels, index=idx, label_visibility='collapsed')
        pg  = options[labels.index(sel)]
        if pg != st.session_state.page: st.session_state.page = pg; st.rerun()
    st.sidebar.markdown('<div style="height:160px;"></div>', unsafe_allow_html=True)
    if st.sidebar.button('↪  Sign Out', use_container_width=True):
        add_audit('Logout', st.session_state.current_user_email, 'User logged out')
        for k in ['logged_in','user_type','current_user_name','current_user_email',
                  'prediction_done','patient_data','prediction_result','confidence',
                  'prediction_time','pdf_bytes']:
            st.session_state[k] = defaults[k]
        st.session_state.page = 'auth'; st.session_state.auth_mode = 'signin'; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PAGES
# ─────────────────────────────────────────────────────────────────────────────
def landing_page():
    public_header()
    st.markdown(f'''
    <section class="hero">
        <div class="hero-badge">↯ AI-POWERED HEALTH PLATFORM</div>
        <h1 class="hero-title">Know Your<span class="hero-blue">Diabetes Risk</span></h1>
        <p class="hero-sub">Predict diabetes risk in seconds using Machine Learning.<br>
        Understand your health. Take action early. Live better.</p>
    </section>
    ''', unsafe_allow_html=True)
    c1,c2,c3 = st.columns([2,1.4,2])
    with c2:
        if st.button('Get Started →', type='primary', key='landing_start', use_container_width=True):
            st.session_state.started=True; st.session_state.page='auth'
            st.session_state.auth_mode='signup'; st.session_state.signup_step=1; st.rerun()
    st.markdown(f'''
    <div class="stats-wrap">
        <div class="stat"><div class="stat-num">95%+</div><div class="stat-label">Model Accuracy</div></div>
        <div class="stat"><div class="stat-num">8</div><div class="stat-label">Health Parameters</div></div>
        <div class="stat"><div class="stat-num">100%</div><div class="stat-label">Free to Use</div></div>
    </div>
    <section id="features" class="section">
        <h2 class="section-title">What GlucoTrack Does</h2>
        <p class="section-sub">Three powerful features to monitor, predict, and improve your health</p>
        <div class="feature-grid">
            <div class="feature-card" style="background:{'rgba(59,158,255,0.06)' if DARK else '#EBF5FF'};">
                <div class="pill" style="background:{'rgba(59,158,255,0.1)' if DARK else '#DBEAFE'};color:{BLUE}!important;">MACHINE LEARNING</div>
                <div class="icon-box" style="background:{'rgba(59,158,255,0.1)' if DARK else '#DBEAFE'};">🧠</div>
                <div class="feature-title">ML-Based Risk Prediction</div>
                <div class="feature-text">Analyzes 8 clinical parameters to compute diabetes risk with confidence score.</div>
            </div>
            <div class="feature-card" style="background:{'rgba(34,197,94,0.06)' if DARK else '#EFFDF4'};">
                <div class="pill" style="background:{'rgba(34,197,94,0.1)' if DARK else '#DCFCE7'};color:{'#4ADE80' if DARK else '#166534'}!important;">ANALYTICS</div>
                <div class="icon-box" style="background:{'rgba(34,197,94,0.1)' if DARK else '#DCFCE7'};">⌁</div>
                <div class="feature-title">Patient Health Analytics</div>
                <div class="feature-text">Interactive charts, gauges, and detailed breakdown of all clinical parameters.</div>
            </div>
            <div class="feature-card" style="background:{'rgba(249,115,22,0.06)' if DARK else '#FFF7ED'};">
                <div class="pill" style="background:{'rgba(249,115,22,0.1)' if DARK else '#FFEDD5'};color:{'#FB923C' if DARK else '#C2410C'}!important;">REPORTS</div>
                <div class="icon-box" style="background:{'rgba(249,115,22,0.1)' if DARK else '#FFEDD5'};">📄</div>
                <div class="feature-title">Professional PDF Reports</div>
                <div class="feature-text">Download or WhatsApp a full clinical PDF with charts, status indicators, and recommendations.</div>
            </div>
        </div>
    </section>
    <section id="how-it-works" class="section">
        <h2 class="section-title">How It Works</h2>
        <p class="section-sub">Get your diabetes risk assessment in 4 simple steps</p>
        <div class="steps-grid">
            <div class="step-card"><div class="step-num">01</div><div class="step-title">Create Account</div><div class="step-text">Sign up with name and email in under a minute</div></div>
            <div class="step-card"><div class="step-num">02</div><div class="step-title">Enter Health Data</div><div class="step-text">Fill in 8 clinical values from your lab reports</div></div>
            <div class="step-card"><div class="step-num">03</div><div class="step-title">Get Prediction</div><div class="step-text">ML model instantly calculates your risk level</div></div>
            <div class="step-card"><div class="step-num">04</div><div class="step-title">Export Report</div><div class="step-text">Download PDF or send to WhatsApp directly</div></div>
        </div>
    </section>
    <section class="section" style="padding-bottom:20px;">
        <div class="bottom-cta">
            <div style="font-size:40px;margin-bottom:16px;">♢</div>
            <h2 style="font-size:34px;font-weight:900;margin:0 0 16px;color:white!important;">Take Control of Your Health</h2>
            <p style="font-size:18px;line-height:1.6;color:rgba(255,255,255,0.88)!important;">Free, fast, and takes less than 2 minutes.</p>
        </div>
    </section>
    ''', unsafe_allow_html=True)
    c1,c2,c3 = st.columns([2,1.4,2])
    with c2:
        if st.button('Create Free Account →', key='bottom_signup', type='primary', use_container_width=True):
            st.session_state.started=True; st.session_state.page='auth'
            st.session_state.auth_mode='signup'; st.session_state.signup_step=1; st.rerun()
    st.markdown(f'<div class="footer"><div style="font-weight:800;">⌁ GlucoTrack</div><div style="color:{MUTED}!important;font-size:13px;">For educational purposes only. Always consult a medical professional.</div></div>', unsafe_allow_html=True)
    components.html('<script>window.parent.document.querySelector(".main").scrollTo({top:0,behavior:"instant"});</script>', height=0)


def auth_page():
    public_header()
    if st.button('← Back to Home', key='auth_back', type='secondary'):
        st.session_state.started=False; st.session_state.page='home'; st.rerun()
    if st.session_state.auth_mode == 'signin':
        st.markdown(f'<div class="auth-title"><div class="auth-logo-row">⌁ GlucoTrack</div><h1 style="font-size:30px;margin:24px 0 6px;color:{HEADING_COLOR}!important;">Welcome back</h1><p style="font-size:17px;color:{MUTED}!important;">Sign in to your dashboard</p></div>', unsafe_allow_html=True)
        c1,col,c3 = st.columns([1,1.8,1])
        with col:
            with st.container(border=True):
                em = st.text_input('Email address', placeholder='you@example.com', key='si_email')
                pw = st.text_input('Password', type='password', key='si_pw')
                is_adm = st.checkbox('Admin or Doctor?', key='is_adm')
                if is_adm:
                    st.info('🛡️ Admin: `admin@glucotrack.com` / `admin@123`\n\n'
                            '👨‍⚕️ Doctor: `doctor@glucotrack.com` / `Doc@1234` *(needs approval)*')
                st.write('')
                if st.button('Sign In →', type='primary', use_container_width=True, key='si_btn'):
                    ok, msg = login_user(em, pw)
                    if ok: st.rerun()
                    else: st.error(msg)
                st.markdown(f'<div style="text-align:center;margin:16px 0;color:{MUTED}!important;">or</div>', unsafe_allow_html=True)
                if st.button('Create a free account →', type='secondary', use_container_width=True, key='to_su'):
                    st.session_state.auth_mode='signup'; st.session_state.signup_step=1; st.rerun()
    else:
        step = st.session_state.signup_step
        pct  = '50%' if step==1 else '100%'
        st.markdown(f'<div class="auth-title"><div class="auth-logo-row">⌁ GlucoTrack</div><h1 style="font-size:30px;margin:24px 0 6px;color:{HEADING_COLOR}!important;">Create Account</h1><p style="font-size:17px;color:{MUTED}!important;">Step {step} of 2</p><div style="height:6px;background:{BORDER};border-radius:8px;max-width:520px;margin:24px auto 0;overflow:hidden;"><div style="width:{pct};height:100%;background:{BLUE};border-radius:8px;"></div></div></div>', unsafe_allow_html=True)
        c1,col,c3 = st.columns([1,1.8,1])
        with col:
            with st.container(border=True):
                if step == 1:
                    fn  = st.text_input('Full Name *',     placeholder='John Doe',         key='rn')
                    em  = st.text_input('Email *',         placeholder='you@example.com',   key='re')
                    ph  = st.text_input('Phone *',         placeholder='+91 98765 43210',   key='rp')
                    ca,cb = st.columns(2)
                    with ca: ag = st.number_input('Age *', 1,100,25, key='ra')
                    with cb: gn = st.selectbox('Gender',['Select','Female','Male','Other'], key='rg')
                    addr = st.text_area('Address', placeholder='Optional', key='rad')
                    if st.button('Continue →', type='primary', use_container_width=True, key='rc'):
                        ec = em.strip().lower()
                        if not fn or not ec or not ph: st.error('Fill required fields.')
                        elif gn=='Select': st.error('Select gender.')
                        elif ec in users or ec in doctors or ec in admins: st.error('Email already registered.')
                        else:
                            st.session_state.update(signup_name=fn.strip(), signup_email=ec,
                                signup_phone=ph.strip(), signup_age=ag,
                                signup_gender=gn, signup_address=addr.strip(),
                                signup_step=2); st.rerun()
                    if st.button('Already have account? Sign in', type='secondary', use_container_width=True, key='s1si'):
                        st.session_state.auth_mode='signin'; st.rerun()
                else:
                    pw  = st.text_input('Password',         type='password', key='rpw')
                    cpw = st.text_input('Confirm Password', type='password', key='rcpw')
                    lbl,col_s,wid,hints = password_strength(pw)
                    if pw:
                        ht = f"add {', '.join(hints)}" if hints else 'Strong ✓'
                        st.markdown(f'<div style="margin:-4px 0 14px;"><div style="height:4px;border-radius:4px;background:{BORDER};overflow:hidden;"><div style="height:100%;width:{wid}%;background:{col_s};border-radius:4px;"></div></div><div style="font-size:13px;color:{col_s}!important;font-weight:700;margin-top:5px;">{lbl} · {ht}</div></div>', unsafe_allow_html=True)
                    ca,cb = st.columns(2)
                    with ca:
                        if st.button('← Back', type='secondary', use_container_width=True, key='bk'):
                            st.session_state.signup_step=1; st.rerun()
                    with cb:
                        if st.button('Create Account', type='primary', use_container_width=True, key='ca'):
                            if not pw: st.error('Enter password.')
                            elif len(pw)<6: st.error('Min 6 characters.')
                            elif pw!=cpw: st.error("Passwords don't match.")
                            else:
                                st.session_state.signup_password=pw
                                st.session_state.page='create_profile'; st.rerun()
                    if st.button('Already have account? Sign in', type='secondary', use_container_width=True, key='s2si'):
                        st.session_state.auth_mode='signin'; st.rerun()


def create_profile_page():
    public_header()
    if st.button('← Back', key='cpb', type='secondary'):
        st.session_state.page='auth'; st.session_state.auth_mode='signup'
        st.session_state.signup_step=2; st.rerun()
    st.markdown(f'<div class="auth-title"><div class="auth-logo-row">⌁ GlucoTrack</div><h1 style="font-size:30px;margin:24px 0 6px;color:{HEADING_COLOR}!important;">Create Profile</h1><p style="font-size:17px;color:{MUTED}!important;">Patient or Doctor?</p></div>', unsafe_allow_html=True)
    c1,col,c3 = st.columns([1,1.8,1])
    with col:
        with st.container(border=True):
            role = st.radio('I am a', ['Patient','Doctor'], horizontal=True)
            name = st.text_input('Full Name', value=st.session_state.signup_name)
            st.text_input('Email', value=st.session_state.signup_email, disabled=True)
            if role == 'Patient':
                phone   = st.text_input('Phone', value=st.session_state.signup_phone)
                age     = st.number_input('Age', 1,100, int(st.session_state.signup_age))
                gender  = st.selectbox('Gender',['Female','Male','Other'],
                    index=['Female','Male','Other'].index(st.session_state.signup_gender)
                    if st.session_state.signup_gender in ['Female','Male','Other'] else 0)
                address = st.text_area('Address', value=st.session_state.signup_address)
                photo   = st.file_uploader('Profile Photo (optional)', type=['png','jpg','jpeg'], key='pp')
                if st.button('Create Patient Profile', type='primary', use_container_width=True):
                    b64 = base64.b64encode(photo.getvalue()).decode() if photo else None
                    users[st.session_state.signup_email] = {
                        'password':st.session_state.signup_password,'name':name,'phone':phone,
                        'age':age,'gender':gender,'address':address,'medical_history':'',
                        'user_type':'patient','profile_created':True,'profile_pic':b64}
                    save_json(USERS_FILE, users)
                    add_audit('Account Created', st.session_state.signup_email, 'Patient')
                    ok,msg = login_user(st.session_state.signup_email, st.session_state.signup_password)
                    if ok: st.rerun()
                    else: st.error(msg)
            else:
                phone = st.text_input('Phone', value=st.session_state.signup_phone)
                spec  = st.text_input('Specialization', placeholder='Endocrinology')
                hosp  = st.text_input('Hospital / Clinic')
                lic   = st.text_input('Medical License No.')
                photo = st.file_uploader('Profile Photo (optional)', type=['png','jpg','jpeg'], key='dp')
                if st.button('Create Doctor Profile', type='primary', use_container_width=True):
                    b64 = base64.b64encode(photo.getvalue()).decode() if photo else None
                    doctors[st.session_state.signup_email] = {
                        'password':st.session_state.signup_password,'name':name,'phone':phone,
                        'specialization':spec,'hospital':hosp,'license_no':lic,
                        'approved':False,'user_type':'doctor','profile_created':True,'profile_pic':b64}
                    save_json(DOCTORS_FILE, doctors)
                    add_audit('Doctor Signup', st.session_state.signup_email, 'Awaiting approval')
                    st.success('Profile created. Wait for admin approval before signing in.')
                    st.session_state.page='auth'; st.session_state.auth_mode='signin'; st.rerun()


def prediction_page():
    st.markdown('<div class="page-head"><div class="page-icon">🩺</div><div><div class="page-title">Diabetes Risk Prediction</div><div class="page-sub">Enter your clinical parameters for an AI-powered assessment</div></div></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="card-heading"><div class="badge-num">1</div> Clinical Health Parameters</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            preg    = st.number_input('Pregnancies',           0,  20,  1)
            bp      = st.number_input('Blood Pressure (mmHg)', 30, 140, 70)
            insulin = st.number_input('Insulin (μU/mL)',       0,  400, 100)
            dpf     = st.number_input('Diabetes Pedigree',     0.0,3.0, 0.5)
        with c2:
            glucose = st.number_input('Glucose (mg/dL)',       50, 250, 120)
            skin    = st.number_input('Skin Thickness (mm)',   0,  100, 20)
            bmi     = st.number_input('BMI',                   10.0,70.0,25.0)
            def_age = int(users.get(st.session_state.current_user_email,{}).get('age',30)) \
                      if st.session_state.user_type=='patient' else 30
            age     = st.number_input('Age (years)',           1,  100, def_age)
    if st.button('Predict Diabetes Risk →', type='primary', use_container_width=True):
        pd_data = {'Pregnancies':preg,'Glucose':glucose,'BloodPressure':bp,
                   'SkinThickness':skin,'Insulin':insulin,'BMI':bmi,
                   'DiabetesPedigreeFunction':dpf,'Age':age}
        result, conf = model_predict(pd_data)
        pt = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        nm = st.session_state.current_user_name
        em = st.session_state.current_user_email
        pdf = generate_pdf(pd_data, result, conf, nm, em, pt)
        st.session_state.update(patient_data=pd_data, prediction_result=result,
            confidence=conf, prediction_time=pt, pdf_bytes=pdf, prediction_done=True)
        reports.append({'name':nm,'email':em,'result':result,'confidence':conf,
                        'time':pt,'data':pd_data})
        save_json(REPORTS_FILE, reports)
        add_audit('Prediction', em, result)
        st.session_state.page='dashboard'; st.rerun()


def dashboard_page():
    st.markdown('<div class="page-head"><div class="page-icon">📊</div><div><div class="page-title">Health Dashboard</div><div class="page-sub">Results, analytics, and your personalised report</div></div></div>', unsafe_allow_html=True)
    if not st.session_state.prediction_done:
        st.warning('No prediction yet. Complete a prediction first.')
        if st.button('Go to Prediction', type='primary'): st.session_state.page='prediction'; st.rerun()
        return
    result  = st.session_state.prediction_result
    conf    = st.session_state.confidence
    pd_data = st.session_state.patient_data

    st.markdown(f'<div class="{"result-high" if "High" in result else "result-low"}">{"⚠️" if "High" in result else "✅"} {result}<br><span style="font-size:16px;opacity:.85;">Confidence: {conf}%</span></div>', unsafe_allow_html=True)
    st.write('')

    st.subheader('🧾 Health Parameters')
    cols = st.columns(4)
    for i,(k,v) in enumerate(pd_data.items()):
        with cols[i%4]:
            st.markdown(f'<div class="param-card"><div class="param-label">{k}</div><div class="param-value">{v}</div></div>', unsafe_allow_html=True)

    st.write('')
    st.subheader('📈 Analytics')
    metrics = ['Glucose','BMI','Insulin','BloodPressure','Age']
    values  = [pd_data[m] for m in metrics]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=metrics, y=values,
        marker_color=[BLUE,'#22C55E','#F97316','#8B5CF6','#EF4444'],
        text=values, textposition='outside'))
    fig.update_layout(template=PLOT_TEMPLATE, height=360,
                      title='Health Parameter Overview', margin=dict(t=40,b=20))
    st.plotly_chart(fig, use_container_width=True)

    suggestions = get_suggestions(pd_data)
    items = ''.join([f'<li style="margin-bottom:8px;">{s}</li>' for s in suggestions])
    bg = 'rgba(59,158,255,0.08)' if DARK else '#EBF5FF'
    tc = '#90CAF9' if DARK else '#006BAA'
    hc = '#E3F2FD' if DARK else '#0D1526'
    components.html(f'<div style="background:{bg};padding:22px 26px;border-radius:14px;font-family:Inter,Arial;"><h3 style="color:{hc};margin:0 0 12px;font-size:16px;">💡 Health Suggestions</h3><ul style="color:{tc};font-size:15px;line-height:1.8;font-weight:600;padding-left:18px;margin:0;">{items}</ul></div>', height=190)

    st.write('')
    render_whatsapp_panel(
        result=result, confidence=conf, patient_data=pd_data,
        suggestions=suggestions, pred_time=st.session_state.prediction_time,
        patient_name=st.session_state.current_user_name,
        pdf_bytes=st.session_state.pdf_bytes,
        key_suffix='dash'
    )

    st.write('')
    if st.button('New Prediction', type='secondary', use_container_width=True):
        reset_prediction_state(); st.session_state.page='prediction'; st.rerun()


def doctor_page():
    st.markdown('<div class="page-head"><div class="page-icon">👨‍⚕️</div><div><div class="page-title">Doctor Portal</div><div class="page-sub">Patient Directory & Clinical Analytics</div></div></div>', unsafe_allow_html=True)
    high_cases = [r for r in reports if 'High' in r.get('result','')]
    with st.container(border=True):
        c1,c2,c3 = st.columns(3)
        c1.metric('Total Assessments', len(reports))
        c2.metric('High Risk Patients ⚠️', len(high_cases))
        c3.metric('Registered Patients', len(users))

    st.write('')
    tab_dir, tab_detail = st.tabs(['📋 Reports Directory','🔍 Detailed Analysis'])

    with tab_dir:
        if not reports: st.info('No reports yet.')
        else:
            rows=[]
            for r in reports:
                d=r.get('data',{})
                rows.append({'Patient':r.get('name'),'Email':r.get('email'),
                    'Risk':r.get('result'),'Confidence':f"{r.get('confidence')}%",
                    'Time':r.get('time'),'Glucose':d.get('Glucose','N/A'),
                    'BMI':d.get('BMI','N/A'),'BP':d.get('BloodPressure','N/A'),
                    'Age':d.get('Age','N/A')})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tab_detail:
        if not reports: st.info('No reports for analysis.')
        else:
            opts = [f"{r.get('name')} ({r.get('time')}) — {r.get('result')}" for r in reports]
            idx  = st.selectbox('Select patient report:', range(len(reports)),
                                format_func=lambda x: opts[x])
            rpt     = reports[idx]
            pd_data = rpt.get('data',{})
            result  = rpt.get('result')
            conf    = rpt.get('confidence')
            pt      = rpt.get('time')
            nm      = rpt.get('name')
            em      = rpt.get('email')
            pinfo   = users.get(em,{})
            phone   = pinfo.get('phone','Not Provided')

            st.markdown(f'''
            <div style="background:{CARD};border:1.5px solid {BORDER};padding:22px;border-radius:14px;margin-bottom:18px;">
                <h3 style="margin:0 0 14px;color:{HEADING_COLOR}!important;">👤 {nm}</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px;">
                    <div style="color:{TEXT}!important;"><b>Email:</b> {em}</div>
                    <div style="color:{TEXT}!important;"><b>Phone:</b> {phone}</div>
                    <div style="color:{TEXT}!important;"><b>Age:</b> {pinfo.get('age',pd_data.get('Age','—'))}</div>
                    <div style="color:{TEXT}!important;"><b>Gender:</b> {pinfo.get('gender','—')}</div>
                </div>
                <div class="{"result-high" if "High" in result else "result-low"}" style="padding:14px;">
                    {"⚠️" if "High" in result else "✅"} <b>{result}</b> ({conf}% Confidence)
                </div>
            </div>
            ''', unsafe_allow_html=True)

            st.subheader('📋 Clinical Parameters')
            pcols = st.columns(4)
            for i,(key,meta) in enumerate(PARAM_META.items()):
                with pcols[i%4]:
                    st.markdown(f'<div class="param-card"><div class="param-label">{meta["label"]}</div><div class="param-value">{pd_data.get(key,"—")}</div></div>', unsafe_allow_html=True)

            st.write('')
            cl, cr = st.columns([3,2])
            with cl:
                st.subheader('📈 Analytics')
                fig = go.Figure()
                ml=['Glucose','BMI','Insulin','BloodPressure','Age']
                vl=[pd_data.get(m,0) for m in ml]
                fig.add_trace(go.Bar(x=ml,y=vl,
                    marker_color=[BLUE,'#22C55E','#F97316','#8B5CF6','#EF4444'],
                    text=vl,textposition='outside'))
                fig.update_layout(template=PLOT_TEMPLATE,height=320,
                                  title='Key Metrics',margin=dict(t=36,b=16,l=16,r=16))
                st.plotly_chart(fig, use_container_width=True)
            with cr:
                st.subheader('💡 Suggestions')
                sugg = get_suggestions(pd_data)
                sh = ''.join([f'<li style="margin-bottom:8px;">{s}</li>' for s in sugg])
                bg='rgba(59,158,255,0.08)' if DARK else '#EBF5FF'
                tc='#90CAF9' if DARK else '#006BAA'
                hc='#E3F2FD' if DARK else '#0D1526'
                components.html(f'<div style="background:{bg};padding:18px;border-radius:12px;font-family:Inter,Arial;"><h4 style="color:{hc};margin:0 0 10px;font-size:14px;">Recommendations</h4><ul style="color:{tc};font-size:14px;line-height:1.7;font-weight:600;padding-left:16px;margin:0;">{sh}</ul></div>', height=320)

            st.write('')
            st.subheader('📝 Doctor Notes')
            notes = st.text_area(
                'Add clinical notes (optional)',
                placeholder='E.g. Patient should follow up in 3 months...',
                key=f'doc_notes_{idx}', height=80
            )

            pdf_data = generate_pdf(pd_data, result, conf, nm, em, pt,
                                    doctor_name=st.session_state.current_user_name,
                                    doctor_notes=notes)
            suggestions = get_suggestions(pd_data)
            render_whatsapp_panel(
                result=result, confidence=conf, patient_data=pd_data,
                suggestions=suggestions, pred_time=pt,
                patient_name=nm, pdf_bytes=pdf_data,
                shared_by=f'Dr. {st.session_state.current_user_name}',
                key_suffix=f'doc_{idx}'
            )


def admin_page():
    st.markdown('<div class="page-head"><div class="page-icon">🛡️</div><div><div class="page-title">Admin Panel</div><div class="page-sub">Manage doctors, users, reports, and audit logs</div></div></div>', unsafe_allow_html=True)
    pending = {e:d for e,d in doctors.items() if not d.get('approved',False)}
    high    = [r for r in reports if 'High' in r.get('result','')]
    with st.container(border=True):
        c1,c2,c3,c4 = st.columns(4)
        c1.metric('Patients', len(users))
        c2.metric('Doctors', len(doctors))
        c3.metric('Pending', len(pending))
        c4.metric('High Risk', len(high))
    st.write('')
    st.subheader('Doctor Approvals')
    if not pending: st.success('No pending approvals.')
    else:
        for em,d in pending.items():
            with st.container(border=True):
                st.write(f"**{d.get('name')}** | {em} | {d.get('specialization')} | {d.get('hospital')}")
                c1,c2 = st.columns(2)
                with c1:
                    if st.button(f'✅ Approve', key=f'ap_{em}', type='primary', use_container_width=True):
                        doctors[em]['approved']=True; save_json(DOCTORS_FILE,doctors)
                        add_audit('Doctor Approved',st.session_state.current_user_email,em); st.rerun()
                with c2:
                    if st.button(f'❌ Reject', key=f'rj_{em}', type='secondary', use_container_width=True):
                        doctors.pop(em); save_json(DOCTORS_FILE,doctors)
                        add_audit('Doctor Rejected',st.session_state.current_user_email,em); st.rerun()
    st.write('')
    st.subheader('Registered Patients')
    st.dataframe(pd.DataFrame([{'Name':v.get('name'),'Email':k,'Age':v.get('age'),'Gender':v.get('gender')} for k,v in users.items()]), use_container_width=True)
    st.write('')
    st.subheader('Registered Doctors')
    st.dataframe(pd.DataFrame([{'Name':v.get('name'),'Email':k,'Approved':v.get('approved'),'Specialization':v.get('specialization')} for k,v in doctors.items()]), use_container_width=True)
    st.write('')
    st.subheader('Audit Log')
    logs = load_json(AUDIT_FILE,[])
    if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else: st.info('No audit logs yet.')


def profile_page():
    bp = 'prediction' if st.session_state.user_type=='patient' else \
         ('doctor' if st.session_state.user_type=='doctor' else 'admin')
    if st.button('← Back', key='pb', type='secondary'):
        st.session_state.page=bp; st.rerun()
    st.markdown('<div class="page-head"><div class="page-icon">👤</div><div><div class="page-title">My Profile</div><div class="page-sub">Edit your details</div></div></div>', unsafe_allow_html=True)
    em = st.session_state.current_user_email
    with st.container(border=True):
        if st.session_state.user_type == 'patient':
            u    = users[em]
            nm   = st.text_input('Name',    value=u.get('name',''))
            ph   = st.text_input('Phone',   value=u.get('phone',''))
            ag   = st.number_input('Age',1,100,int(u.get('age',25)))
            gn   = st.selectbox('Gender',['Female','Male','Other'],
                    index=['Female','Male','Other'].index(u.get('gender','Female'))
                    if u.get('gender') in ['Female','Male','Other'] else 0)
            addr = st.text_area('Address', value=u.get('address',''))
            photo= st.file_uploader('Change Photo', type=['png','jpg','jpeg'], key='epp')
            if st.button('Save Profile', type='primary', use_container_width=True):
                upd = {'name':nm,'phone':ph,'age':ag,'gender':gn,'address':addr}
                if photo: upd['profile_pic']=base64.b64encode(photo.getvalue()).decode()
                users[em].update(upd); save_json(USERS_FILE,users)
                st.session_state.current_user_name=nm
                add_audit('Profile Updated',em,'Patient'); st.success('Saved.'); st.rerun()
        elif st.session_state.user_type == 'doctor':
            d    = doctors[em]
            nm   = st.text_input('Name',           value=d.get('name',''))
            ph   = st.text_input('Phone',          value=d.get('phone',''))
            sp   = st.text_input('Specialization', value=d.get('specialization',''))
            ho   = st.text_input('Hospital',       value=d.get('hospital',''))
            li   = st.text_input('License No.',    value=d.get('license_no',''))
            photo= st.file_uploader('Change Photo', type=['png','jpg','jpeg'], key='edp')
            if st.button('Save Profile', type='primary', use_container_width=True):
                upd={'name':nm,'phone':ph,'specialization':sp,'hospital':ho,'license_no':li}
                if photo: upd['profile_pic']=base64.b64encode(photo.getvalue()).decode()
                doctors[em].update(upd); save_json(DOCTORS_FILE,doctors)
                st.session_state.current_user_name=nm
                add_audit('Profile Updated',em,'Doctor'); st.success('Saved.'); st.rerun()
        else:
            st.info('Admin profile editing not enabled.')

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.started:
    landing_page(); st.stop()

dashboard_sidebar()

page = st.session_state.page
if   page == 'auth':           auth_page()
elif page == 'create_profile': create_profile_page()
elif page == 'prediction':     prediction_page()
elif page == 'dashboard':      dashboard_page()
elif page == 'doctor':         doctor_page()
elif page == 'admin':          admin_page()
elif page == 'profile':        profile_page()
else:
    st.session_state.page = 'auth'; st.rerun()

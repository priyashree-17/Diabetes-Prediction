import os
import json
import pickle
import base64
from datetime import datetime
from io import BytesIO
import urllib.parse
import tempfile
import time
import webbrowser
from pathlib import Path
from zoneinfo import ZoneInfo


import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt


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
        'password': 'user@123',
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

_migrated = False
if 'user@gmail.com' in users and users['user@gmail.com'].get('password') == 'Pass1234':
    users['user@gmail.com']['password'] = 'user@123'
    _migrated = True
if _migrated:
    save_json(USERS_FILE, users)


defaults = {
    'started': False,
    'page': 'home',
    'auth_mode': 'signin',   # signin | signup | forgot_password
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
    'current_prediction_patient_name': '',
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

DARK = st.session_state.dark_mode

if DARK:
    BG = '#0A1628'
    BG2 = '#0D1E38'
    CARD = '#112240'
    CARD2 = '#162B50'
    TEXT = '#E8F0FF'
    MUTED = '#8BA8D4'
    BORDER = '#1E3A5F'
    INPUT = '#112240'
    GRAD1 = '#818CF8'
    GRAD2 = '#F472B6'
    GRAD3 = '#60A5FA'
    BLUE = '#60A5FA'
    BLUE_DARK = '#3B82F6'
    TEAL = '#A5B4FC'
    INDIGO = '#F472B6'
    SIDEBAR = '#0A1628'
    PLOT_TEMPLATE = 'plotly_dark'
    RESULT_HIGH_BG = '#2D0A14'
    RESULT_HIGH_BORDER = '#F43F5E'
    RESULT_HIGH_TEXT = '#FDA4AF'
    RESULT_LOW_BG = '#0A1F3A'
    RESULT_LOW_BORDER = '#818CF8'
    RESULT_LOW_TEXT = '#C7D2FE'
    BOX_SUGGESTION_BG = '#0D1E38'
    BOX_SUGGESTION_TITLE = '#E8F0FF'
    BOX_SUGGESTION_TEXT = '#A5B4FC'
    HERO_OVERLAY = 'rgba(10,22,40,0.85)'
else:
    BG = '#F0F4FF'
    BG2 = '#E8EDFF'
    CARD = '#FFFFFF'
    CARD2 = '#F7F9FF'
    TEXT = '#1A0533'
    MUTED = '#6B52A0'
    BORDER = '#C7D2FE'
    INPUT = '#FFFFFF'
    GRAD1 = '#6D28D9'
    GRAD2 = '#EC4899'
    GRAD3 = '#3B82F6'
    BLUE = '#4F46E5'
    BLUE_DARK = '#3730A3'
    TEAL = '#8B5CF6'
    INDIGO = '#EC4899'
    SIDEBAR = '#FFFFFF'
    PLOT_TEMPLATE = 'plotly_white'
    RESULT_HIGH_BG = '#FFF1F2'
    RESULT_HIGH_BORDER = '#FB7185'
    RESULT_HIGH_TEXT = '#BE123C'
    RESULT_LOW_BG = '#F5F3FF'
    RESULT_LOW_BORDER = '#8B5CF6'
    RESULT_LOW_TEXT = '#5B21B6'
    BOX_SUGGESTION_BG = '#FAF5FF'
    BOX_SUGGESTION_TITLE = '#1A0533'
    BOX_SUGGESTION_TEXT = '#6D28D9'
    HERO_OVERLAY = 'rgba(245,243,255,0.92)'

GRAD_PRIMARY = f'linear-gradient(135deg, {GRAD1} 0%, {GRAD2} 100%)'
GRAD_CARD = f'linear-gradient(135deg, {GRAD1}18 0%, {GRAD2}18 100%)' if not DARK else f'linear-gradient(135deg, {GRAD1}22 0%, {GRAD2}22 100%)'
GRAD_HERO = 'linear-gradient(135deg, #3B82F6 0%, #6D28D9 40%, #EC4899 100%)'

css = f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800;900&family=DM+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif !important; }}
.stApp {{
    background: {'linear-gradient(135deg, #0A1628 0%, #0f1e3c 50%, #1a0d2e 100%)' if DARK else 'linear-gradient(135deg, #A5B4FC 0%, #C4B5FD 40%, #DDD6FE 100%)'} !important;
    min-height: 100vh !important;
}}
.block-container {{ padding-top: 0.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; max-width: 100% !important; }}
h1,h2,h3,h4,h5,h6 {{ font-family: 'Sora', sans-serif !important; color: {TEXT} !important; }}
p, label, span {{ font-family: 'DM Sans', sans-serif !important; color: {TEXT} !important; }}
.hero-card h1, .hero-card h2, .hero-card p, .hero-card span, .hero-card div {{ color: white !important; -webkit-text-fill-color: white !important; }}
.hero-sub {{ color: rgba(255,255,255,0.85) !important; -webkit-text-fill-color: rgba(255,255,255,0.85) !important; }}

/* ── Sidebar nav items ── */
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* Sidebar collapse / expand arrow fix */
[data-testid="stSidebarCollapsedControl"] {{
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    background: {'rgba(30,20,60,0.96)' if DARK else '#4C1D95'} !important;
    border-radius: 0 14px 14px 0 !important;
    box-shadow: 4px 0 18px rgba(76,29,149,0.50) !important;
    width: 34px !important;
    height: 54px !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    overflow: hidden !important;
    cursor: pointer !important;
}}
[data-testid="stSidebarCollapsedControl"]:hover {{
    width: 38px !important;
    box-shadow: 6px 0 22px rgba(76,29,149,0.70) !important;
}}
[data-testid="stSidebarCollapsedControl"] button {{
    font-size: 0 !important;
    color: transparent !important;
    background: transparent !important;
    border: none !important;
    width: 100% !important;
    height: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    position: relative !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
[data-testid="stSidebarCollapsedControl"] button *,
[data-testid="stSidebarCollapsedControl"] button span,
[data-testid="stSidebarCollapsedControl"] button svg {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    font-size: 0 !important;
    color: transparent !important;
}}
[data-testid="stSidebarCollapsedControl"] button::before {{
    content: "»" !important;
    font-size: 26px !important;
    font-weight: 900 !important;
    color: #DDD6FE !important;
    -webkit-text-fill-color: #DDD6FE !important;
    font-family: Arial, Helvetica, sans-serif !important;
    line-height: 1 !important;
    display: block !important;
    opacity: 1 !important;
}}

section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"] button[data-testid="baseButton-header"] {{
    font-size: 0 !important;
    color: transparent !important;
    background: {'rgba(109,40,217,0.28)' if DARK else 'rgba(109,40,217,0.15)'} !important;
    border: 1.5px solid {'rgba(196,181,253,0.40)' if DARK else 'rgba(109,40,217,0.35)'} !important;
    border-radius: 12px !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    position: relative !important;
    cursor: pointer !important;
}}
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"]:hover,
section[data-testid="stSidebar"] button[data-testid="baseButton-header"]:hover {{
    background: {'rgba(109,40,217,0.50)' if DARK else 'rgba(109,40,217,0.32)'} !important;
}}
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"] *,
section[data-testid="stSidebar"] button[data-testid="baseButton-header"] *,
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"] span,
section[data-testid="stSidebar"] button[data-testid="baseButton-header"] span,
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"] svg,
section[data-testid="stSidebar"] button[data-testid="baseButton-header"] svg {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    font-size: 0 !important;
    color: transparent !important;
}}
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"]::before,
section[data-testid="stSidebar"] button[data-testid="baseButton-header"]::before {{
    content: "«" !important;
    font-size: 26px !important;
    font-weight: 900 !important;
    color: {'#DDD6FE' if DARK else '#4C1D95'} !important;
    -webkit-text-fill-color: {'#DDD6FE' if DARK else '#4C1D95'} !important;
    font-family: Arial, Helvetica, sans-serif !important;
    line-height: 1 !important;
    display: block !important;
    opacity: 1 !important;
}}
header button[data-testid="baseButton-headerNoPadding"],
header button[data-testid="baseButton-header"] {{
    display: none !important;
}}


/* ── Sidebar: remove top gap ── */
section[data-testid="stSidebar"] > div:first-child {{
    padding-top: 0 !important; margin-top: 0 !important;
}}
section[data-testid="stSidebar"] > div > div {{
    padding-top: 0 !important; margin-top: 0 !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding-top: 0 !important; margin-top: 0 !important;
}}
section[data-testid="stSidebar"] > div:first-child > div:first-child {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}

/* Header cleanup */
[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; box-shadow: none !important; border: none !important; }}
header[data-testid="stHeader"] [data-testid="stAppDeployButton"] {{ display: none !important; }}
header[data-testid="stHeader"] #MainMenu {{ display: none !important; }}
header[data-testid="stHeader"] [data-testid="stConnectionStatus"] {{ display: none !important; }}

.nav-link {{ text-decoration: none !important; color: {TEXT} !important; font-weight: 600 !important; font-size: 15px !important; transition: all 0.2s ease !important; font-family: 'DM Sans', sans-serif !important; }}
.nav-link:hover {{ color: {GRAD1} !important; }}

/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: {INPUT} !important; color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important; border-radius: 14px !important;
    min-height: 52px !important; font-size: 15px !important; padding-left: 16px !important;
    font-family: 'DM Sans', sans-serif !important; transition: border-color 0.2s ease !important;
}}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
    border-color: {GRAD1} !important; box-shadow: 0 0 0 3px {GRAD1}22 !important;
}}
.stSelectbox div[data-baseweb="select"]>div {{
    background: {INPUT} !important; color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important; border-radius: 14px !important; min-height: 52px !important;
}}

/* ── Number input +/- buttons: clean professional controls ── */
[data-testid="stNumberInput"] {{
    position: relative !important;
}}

/* Hide the tooltip/help button that was becoming an extra top + */
[data-testid="stNumberInput"] label button,
[data-testid="stNumberInput"] [data-testid="stTooltipHoverTarget"],
[data-testid="stNumberInput"] [data-testid="stTooltipIcon"] {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}}

/* Input box */
[data-testid="stNumberInput"] div[data-baseweb="input"] {{
    background: {INPUT} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    min-height: 54px !important;
    box-shadow: {'0 8px 22px rgba(0,0,0,0.20)' if DARK else '0 8px 20px rgba(109,40,217,0.08)'} !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within {{
    border-color: {GRAD1} !important;
    box-shadow: 0 0 0 3px {GRAD1}26 !important;
}}

[data-testid="stNumberInput"] input {{
    border: none !important;
    background: transparent !important;
    color: {TEXT} !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    padding-left: 16px !important;
    padding-right: 88px !important;
    min-height: 54px !important;
    box-shadow: none !important;
    appearance: none !important;
    -moz-appearance: textfield !important;
    -webkit-appearance: none !important;
}}

[data-testid="stNumberInput"] input::-webkit-outer-spin-button,
[data-testid="stNumberInput"] input::-webkit-inner-spin-button {{
    -webkit-appearance: none !important;
    appearance: none !important;
    margin: 0 !important;
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

/* Style only the real stepper buttons inside the input box */
[data-testid="stNumberInput"] div[data-baseweb="input"] button {{
    background: {'linear-gradient(180deg, rgba(129,140,248,0.24), rgba(244,114,182,0.18))' if DARK else 'linear-gradient(180deg, rgba(109,40,217,0.12), rgba(236,72,153,0.10))'} !important;
    border: none !important;
    border-left: 1px solid {BORDER} !important;
    color: transparent !important;
    width: 42px !important;
    min-width: 42px !important;
    height: 54px !important;
    padding: 0 !important;
    margin: 0 !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    border-radius: 0 !important;
    position: relative !important;
    overflow: hidden !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button:hover {{
    background: {GRAD_PRIMARY} !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button:focus {{
    outline: none !important;
    box-shadow: none !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button *,
[data-testid="stNumberInput"] div[data-baseweb="input"] button span,
[data-testid="stNumberInput"] div[data-baseweb="input"] button p,
[data-testid="stNumberInput"] div[data-baseweb="input"] button svg {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    font-size: 0 !important;
    width: 0 !important;
    height: 0 !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button::before {{
    color: {'#EDE9FE' if DARK else '#4C1D95'} !important;
    -webkit-text-fill-color: {'#EDE9FE' if DARK else '#4C1D95'} !important;
    font-family: 'Sora', Arial, sans-serif !important;
    font-size: 22px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    display: block !important;
    opacity: 1 !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button:hover::before {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button:first-of-type::before {{
    content: "−" !important;
}}

[data-testid="stNumberInput"] div[data-baseweb="input"] button:last-of-type::before {{
    content: "+" !important;
}}

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {'rgba(15,30,60,0.88)' if DARK else 'rgba(255,255,255,0.92)'} !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid {'rgba(129,140,248,0.20)' if DARK else 'rgba(255,255,255,0.60)'} !important;
    border-radius: 22px !important; padding: 28px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.10) !important;
}}

/* Buttons */
.stButton>button[kind="primary"], .stDownloadButton>button, .stFormSubmitButton>button {{
    background: {GRAD_PRIMARY} !important; color: white !important; border: none !important;
    border-radius: 14px !important; font-weight: 700 !important; font-size: 15px !important;
    min-height: 52px !important; font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 8px 24px rgba(109,40,217,0.30) !important; transition: all 0.2s ease !important;
}}
.stButton>button[kind="primary"]:hover, .stDownloadButton>button:hover {{
    transform: translateY(-2px) !important; box-shadow: 0 14px 32px rgba(109,40,217,0.42) !important;
}}
.stButton>button[kind="secondary"] {{
    background: transparent !important; color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important; border-radius: 14px !important;
    font-weight: 600 !important; font-size: 15px !important; min-height: 52px !important;
    font-family: 'DM Sans', sans-serif !important; transition: all 0.2s ease !important;
}}
.stButton>button[kind="secondary"]:hover {{ background: {BORDER}44 !important; transform: translateY(-1px) !important; }}
.stButton>button[kind="primary"] *, .stDownloadButton>button *, .stFormSubmitButton>button * {{ color: white !important; }}
.stButton>button[kind="secondary"] * {{ color: {TEXT} !important; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {'linear-gradient(180deg, #0A1628 0%, #0f1e3c 35%, #1a0d2e 65%, #0D1117 100%)' if DARK else 'linear-gradient(180deg, #A5B4FC 0%, #B9AAFF 30%, #C4B5FD 60%, #DDD6FE 100%)'} !important;
    border-right: 1px solid {'rgba(129,140,248,0.15)' if DARK else 'rgba(167,139,250,0.50)'} !important;
    box-shadow: {'4px 0 24px rgba(0,0,0,0.4)' if DARK else '4px 0 24px rgba(139,92,246,0.22)'} !important;
}}
section[data-testid="stSidebar"]>div {{ background: transparent !important; padding-top: 0 !important; }}
section[data-testid="stSidebar"] * {{ color: {'#E2D9F3' if DARK else '#3B0764'} !important; }}
.sb-header {{
    display: flex; align-items: center; gap: 12px;
    padding: 18px 18px 16px 18px; border-bottom: 1px solid {'rgba(167,139,250,0.30)' if DARK else 'rgba(139,92,246,0.30)'};
    background: {'rgba(109,40,217,0.25)' if DARK else 'rgba(139,92,246,0.18)'};
}}
.sb-logo-box {{
    width: 42px; height: 42px; background: {GRAD_PRIMARY};
    color: white !important; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 20px; box-shadow: 0 4px 16px rgba(109,40,217,0.30);
}}
.sb-brand {{ font-size: 20px; font-weight: 800; color: {'#C4B5FD' if DARK else '#4C1D95'} !important; font-family: 'Sora', sans-serif !important; }}
.sb-profile {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 8px; padding: 20px 16px 18px;
    border-bottom: 1px solid {'rgba(167,139,250,0.28)' if DARK else 'rgba(139,92,246,0.28)'};
    background: {'linear-gradient(180deg, rgba(109,40,217,0.26), rgba(236,72,153,0.10))' if DARK else 'linear-gradient(180deg, rgba(255,255,255,0.34), rgba(139,92,246,0.14))'};
    text-align: center;
}}
.sb-avatar, .sb-avatar-img {{
    width: 76px; height: 76px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; border: 3px solid rgba(255,255,255,0.78);
    box-shadow: 0 10px 26px rgba(0,0,0,0.26), 0 0 0 5px {'rgba(129,140,248,0.18)' if DARK else 'rgba(109,40,217,0.14)'};
}}
.sb-avatar {{
    background: {GRAD_PRIMARY};
    color: white !important;
    font-weight: 900; font-size: 24px; font-family: 'Sora', sans-serif !important;
}}
.sb-avatar-img {{
    object-fit: cover;
    background: {CARD};
}}
.sb-info {{ display: flex; flex-direction: column; align-items: center; gap: 4px; width: 100%; min-width: 0; overflow: hidden; }}
.sb-name {{
    max-width: 100%;
    font-size: 15px; font-weight: 800; color: {'#F8F7FF' if DARK else '#3B0764'} !important;
    font-family: 'Sora', sans-serif !important;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.25;
}}
.sb-role {{
    display: inline-flex; align-items: center; justify-content: center;
    padding: 5px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 800;
    color: {'#FCE7F3' if DARK else '#5B21B6'} !important;
    background: {'rgba(244,114,182,0.20)' if DARK else 'rgba(255,255,255,0.42)'};
    border: 1px solid {'rgba(244,114,182,0.28)' if DARK else 'rgba(109,40,217,0.18)'};
    line-height: 1.2; white-space: nowrap;
}}


div[data-testid="stRadio"] {{ padding: 14px 8px 0 !important; }}
div[data-testid="stRadio"] label {{
    border-radius: 12px !important; padding: 12px 14px !important; margin: 3px 0 !important;
    font-size: 14px !important; font-weight: 600 !important; background: transparent !important;
    transition: all 0.18s ease !important; border: 1px solid transparent !important;
}}
div[data-testid="stRadio"] label:hover {{ background: {'rgba(139,92,246,0.20)' if DARK else 'rgba(109,40,217,0.15)'} !important; }}
div[data-testid="stRadio"] label[data-baseweb="radio"]>div:first-child {{ display: none !important; }}

section[data-testid="stSidebar"] .stButton>button {{
    background: {'rgba(139,92,246,0.18)' if DARK else 'rgba(109,40,217,0.12)'} !important;
    border: 1px solid {'rgba(167,139,250,0.30)' if DARK else 'rgba(109,40,217,0.30)'} !important;
    color: {'#E2D9F3' if DARK else '#4C1D95'} !important; border-radius: 12px !important; font-weight: 600 !important;
    font-size: 14px !important; transition: all 0.18s ease !important; box-shadow: none !important;
}}
section[data-testid="stSidebar"] .stButton>button:hover {{
    background: {GRAD_PRIMARY} !important; border-color: transparent !important;
    color: white !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(109,40,217,0.35) !important;
}}
section[data-testid="stSidebar"] .stButton>button:hover * {{ color: white !important; -webkit-text-fill-color: white !important; }}
section[data-testid="stSidebar"] .stButton>button * {{ color: {'#E2D9F3' if DARK else '#4C1D95'} !important; -webkit-text-fill-color: {'#E2D9F3' if DARK else '#4C1D95'} !important; }}

/* HERO */
.hero-section {{
    position: relative; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center;
    padding: 0 20px 40px; overflow: hidden;
}}
.hero-card {{
    width: 100%; max-width: 1200px; margin: 0 auto; border-radius: 28px;
    background: {GRAD_HERO}; padding: 64px 48px 52px; position: relative; overflow: hidden;
    box-shadow: 0 24px 80px rgba(109,40,217,0.35), 0 8px 32px rgba(236,72,153,0.18);
}}
.hero-card::before {{
    content: ''; position: absolute; width: 600px; height: 600px; border-radius: 50%;
    background: rgba(255,255,255,0.07); top: -200px; right: -150px; pointer-events: none;
}}
.hero-card::after {{
    content: ''; position: absolute; width: 400px; height: 400px; border-radius: 50%;
    background: rgba(255,255,255,0.05); bottom: -150px; left: -100px; pointer-events: none;
}}
.hero-badge {{
    position: relative; z-index: 1; display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.18); color: white !important; border-radius: 999px;
    padding: 8px 22px; font-weight: 700; font-size: 12px; letter-spacing: 2px;
    font-family: 'DM Sans', sans-serif; text-transform: uppercase;
    border: 1px solid rgba(255,255,255,0.28); margin-bottom: 28px;
    backdrop-filter: blur(8px); animation: fadeInDown 0.6s ease both;
}}
.hero-title {{
    position: relative; z-index: 1; font-family: 'Sora', sans-serif;
    font-size: clamp(48px, 7vw, 88px); font-weight: 900; line-height: 1.0;
    letter-spacing: -2px; color: white !important; margin: 0 0 20px;
    animation: fadeInUp 0.7s ease 0.1s both;
}}
.hero-gradient-text {{ color: white !important; -webkit-text-fill-color: white; display: block; }}
.hero-sub {{
    position: relative; z-index: 1; font-size: clamp(16px, 2vw, 19px); line-height: 1.65;
    max-width: 600px; margin: 0 auto 40px; color: rgba(255,255,255,0.82) !important; font-weight: 400;
    animation: fadeInUp 0.7s ease 0.2s both;
}}
.hero-stats {{
    display: flex; justify-content: center; gap: 0; margin-top: 44px; position: relative; z-index: 1;
    border-top: 1px solid rgba(255,255,255,0.18); padding-top: 36px;
}}
.hero-stat {{ flex: 1; max-width: 220px; text-align: center; padding: 0 24px; border-right: 1px solid rgba(255,255,255,0.18); }}
.hero-stat:last-child {{ border-right: none; }}
.hero-stat-num {{ font-family: 'Sora', sans-serif; font-size: 38px; font-weight: 900; color: white !important; line-height: 1; margin-bottom: 6px; }}
.hero-stat-label {{ font-size: 13px; color: rgba(255,255,255,0.75) !important; font-weight: 600; }}
.stats-wrap {{ display: none; }} .stat {{ display: none; }}

/* Feature cards */
.section {{ padding: 0 20px 80px; }}
.section-title {{ text-align: center; font-family: 'Sora', sans-serif; font-size: clamp(28px, 4vw, 42px); font-weight: 900; margin-bottom: 14px; color: {TEXT} !important; }}
.section-sub {{ text-align: center; font-size: 19px; margin-bottom: 52px; color: {MUTED} !important; }}
.feature-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; max-width: 1200px; margin: 0 auto; }}
.feature-card {{
    border-radius: 24px; padding: 36px 32px; min-height: 380px; border: none;
    position: relative; overflow: hidden; transition: transform 0.25s ease, box-shadow 0.25s ease;
}}
.feature-card:hover {{ transform: translateY(-8px); box-shadow: 0 24px 56px rgba(0,0,0,0.25); }}
.feature-blue {{ background: linear-gradient(145deg, #6D28D9 0%, #7C3AED 50%, #8B5CF6 100%) !important; }}
.feature-green {{ background: linear-gradient(145deg, #7C3AED 0%, #8B5CF6 50%, #A855F7 100%) !important; }}
.feature-purple {{ background: linear-gradient(145deg, #8B5CF6 0%, #A78BFA 50%, #C4B5FD 100%) !important; }}
.pill {{ display: inline-flex; border-radius: 999px; padding: 6px 16px; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 28px; border: none; text-transform: uppercase; font-family: 'DM Sans', sans-serif; }}
.pill-blue {{ background: rgba(99,102,241,0.22) !important; color: #A5B4FC !important; }}
.pill-green {{ background: rgba(139,92,246,0.22) !important; color: #C4B5FD !important; }}
.pill-purple {{ background: rgba(236,72,153,0.22) !important; color: #F9A8D4 !important; }}
.icon-box {{ width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 26px; margin-bottom: 20px; }}
.icon-blue {{ background: rgba(99,102,241,0.18) !important; }} .icon-green {{ background: rgba(139,92,246,0.18) !important; }} .icon-purple {{ background: rgba(236,72,153,0.18) !important; }}
.feature-title {{ font-family: 'Sora', sans-serif; font-size: 20px; font-weight: 800; margin-bottom: 14px; color: #ffffff !important; }}
.feature-text {{ font-size: 16px; line-height: 1.6; color: rgba(255,255,255,0.72) !important; }}

/* Steps */
.steps-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; max-width: 1200px; margin: 0 auto; }}
.step-card {{ border: none; border-radius: 20px; padding: 32px 22px; text-align: center; background: {'rgba(255,255,255,0.07)' if DARK else 'rgba(255,255,255,0.75)'} !important; position: relative; overflow: hidden; transition: transform 0.2s ease; backdrop-filter: blur(10px); box-shadow: 0 4px 24px rgba(0,0,0,0.12); }}
.step-card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 36px rgba(0,0,0,0.20); }}
.step-num {{ font-family: 'Sora', sans-serif; font-size: 40px; font-weight: 900; background: {GRAD_PRIMARY}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 12px; }}
.step-title {{ font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 800; margin-bottom: 10px; color: {TEXT} !important; }}
.step-text {{ font-size: 15px; line-height: 1.55; color: {MUTED} !important; }}

/* CTA */
.bottom-cta {{ max-width: 860px; margin: 0 auto 80px; text-align: center; border-radius: 28px; padding: 60px; background: {GRAD_HERO}; position: relative; overflow: hidden; box-shadow: 0 20px 60px rgba(109,40,217,0.40); }}
.bottom-cta::before {{ content: ''; position: absolute; width: 400px; height: 400px; border-radius: 50%; background: rgba(255,255,255,0.08); top: -150px; right: -100px; pointer-events: none; }}

/* Auth */
.auth-title {{ text-align: center; padding: 28px 0 18px; }}
.auth-title h1 {{ font-family: 'Sora', sans-serif; font-size: 30px; margin: 24px 0 6px; color: {TEXT} !important; font-weight: 800; }}
.auth-title p {{ font-size: 16px; color: {MUTED} !important; }}
.auth-logo-row {{ display: flex; justify-content: center; align-items: center; gap: 12px; font-family: 'Sora', sans-serif; font-size: 28px; font-weight: 900; color: {TEXT} !important; }}
.logo-square {{ width: 40px; height: 40px; border-radius: 10px; background: {GRAD_PRIMARY}; color: white !important; display: flex; align-items: center; justify-content: center; font-weight: 900; }}

/* Page header — pure block layout, no absolute/relative stacking */
.page-head {{
    display: flex; align-items: center; gap: 16px;
    padding: 4px 0 18px; margin-bottom: 4px;
}}
.page-icon {{
    width: 50px; height: 50px; background: {GRAD_PRIMARY}; color: white !important;
    border-radius: 14px; display: flex; align-items: center; justify-content: center;
    font-size: 22px; box-shadow: 0 4px 16px rgba(109,40,217,0.30); flex-shrink: 0;
}}
.page-title-text {{ font-family: 'Sora', sans-serif; font-size: 26px; font-weight: 800; color: {TEXT} !important; line-height: 1.2; margin: 0; display: block; }}
.page-sub {{ font-size: 14px; margin-top: 2px; color: {MUTED} !important; line-height: 1.4; display: block; }}

.card-heading {{ display: flex; align-items: center; gap: 10px; font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 800; margin-bottom: 20px; color: {TEXT} !important; }}
.badge-num {{ width: 28px; height: 28px; background: {GRAD_PRIMARY}; color: white !important; border-radius: 999px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; }}

/* Results */
.result-high {{
    background: {RESULT_HIGH_BG}; border: 1.5px solid {RESULT_HIGH_BORDER};
    color: {RESULT_HIGH_TEXT} !important; padding: 28px; border-radius: 20px;
    text-align: center; font-weight: 800; font-size: 22px; font-family: 'Sora', sans-serif;
    margin: 8px 0;
}}
.result-low {{
    background: {RESULT_LOW_BG}; border: 1.5px solid {RESULT_LOW_BORDER};
    color: {RESULT_LOW_TEXT} !important; padding: 28px; border-radius: 20px;
    text-align: center; font-weight: 800; font-size: 22px; font-family: 'Sora', sans-serif;
    margin: 8px 0;
}}

/* Param cards */
.param-card {{ background: {CARD2} !important; border: 1px solid {BORDER} !important; border-radius: 16px; padding: 18px 14px; text-align: center; transition: transform 0.2s ease; margin-bottom: 8px; }}
.param-card:hover {{ transform: translateY(-3px); }}
.param-label {{ color: {MUTED} !important; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; display: block; }}
.param-value {{ font-family: 'Sora', sans-serif; color: {TEXT} !important; font-size: 22px; font-weight: 800; background: {GRAD_PRIMARY}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; display: block; }}

/* Footer */
.footer {{ border-top: 1px solid {BORDER}; padding: 26px 22px; display: flex; justify-content: space-between; color: {MUTED} !important; font-size: 14px; }}
.footer-logo {{ font-family: 'Sora', sans-serif; font-weight: 800; color: {TEXT} !important; }}
.grad-divider {{ height: 2px; background: {GRAD_PRIMARY}; border-radius: 999px; margin: 0 auto; opacity: 0.6; }}

/* WhatsApp share box — pure HTML via st.markdown, no iframe overlap */
.wa-share-box {{
    background: {'#031A0F' if DARK else '#F0FDF4'};
    border: 1.5px solid {'#166534' if DARK else '#BBF7D0'};
    border-radius: 18px; padding: 20px 24px; margin-top: 8px; margin-bottom: 12px;
}}
.wa-share-title {{
    display: flex; align-items: center; gap: 10px; margin-bottom: 6px;
}}
.wa-share-title-text {{
    font-family: 'Sora', sans-serif; font-weight: 800; font-size: 16px; color: {TEXT} !important;
}}
.wa-share-desc {{
    color: {MUTED} !important; font-size: 13px; margin: 0 0 0 32px; line-height: 1.5;
}}

/* Animations */
@keyframes fadeInDown {{ from {{ opacity: 0; transform: translateY(-16px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

/* ── Per-page background tints injected via .page-bg-* on block-container ── */
/* Login / Auth page */
.page-bg-auth .stApp {{
    background: {'linear-gradient(135deg, #0A1628 0%, #0f1e3c 50%, #1a0533 100%)' if DARK else 'linear-gradient(135deg, #EDE9FE 0%, #F5F0FF 35%, #FFF0FB 70%, #EEF2FF 100%)'} !important;
}}
/* Patient / User page */
.page-bg-patient .stApp {{
    background: {'linear-gradient(135deg, #0A1F2E 0%, #0D2B3E 50%, #091A2E 100%)' if DARK else 'linear-gradient(135deg, #E0F2FE 0%, #EFF6FF 40%, #F0F9FF 70%, #E8F5E9 100%)'} !important;
}}
/* Doctor page */
.page-bg-doctor .stApp {{
    background: {'linear-gradient(135deg, #0A2018 0%, #0D2E22 50%, #091A14 100%)' if DARK else 'linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 30%, #F0FDFA 60%, #EEF9FF 100%)'} !important;
}}
/* Admin page */
.page-bg-admin .stApp {{
    background: {'linear-gradient(135deg, #1A0A0A 0%, #2D0D0D 50%, #1A0A1A 100%)' if DARK else 'linear-gradient(135deg, #FFF7ED 0%, #FEF3C7 30%, #FFF1F2 60%, #FDF4FF 100%)'} !important;
}}

/* Visibility */
.stMarkdown, .stMarkdown *, .page-title-text, .card-heading, .section-title, .auth-title h1,
div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"],
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] * {{ color: {TEXT} !important; }}
.hero-card, .hero-card *, .hero-title, .hero-badge, .hero-stat-num, .hero-stat-label {{ color: white !important; -webkit-text-fill-color: white !important; }}
.hero-sub {{ color: rgba(255,255,255,0.85) !important; -webkit-text-fill-color: rgba(255,255,255,0.85) !important; }}
.page-sub, .section-sub, .step-text, .auth-title p, .param-label {{ color: {MUTED} !important; }}
.stDataFrame, .stDataFrame *, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {{ color: {TEXT} !important; font-weight: 600 !important; }}

@media(max-width:900px) {{
    .feature-grid, .steps-grid {{ grid-template-columns: 1fr; }}
    .hero-title {{ font-size: 52px; letter-spacing: -2px; }}
}}

/* Hide sidebar toggle text safely */
button[kind="header"],
button[data-testid="baseButton-headerNoPadding"],
button[data-testid="baseButton-header"] {{
    color: transparent !important;
    font-size: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
button[kind="header"] *,
button[data-testid="baseButton-headerNoPadding"] *,
button[data-testid="baseButton-header"] * {{
    font-size: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
}}
/* ── File uploader: prevent duplicate Upload text ── */
[data-testid="stFileUploaderDropzone"] {{
    background: {CARD2} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 14px !important;
}}

[data-testid="stFileUploader"] button,
[data-testid="stFileUploaderDropzone"] button {{
    background: {INPUT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 9px !important;
    padding: 8px 18px !important;
    min-height: 40px !important;
    width: auto !important;
    box-shadow: none !important;
    overflow: hidden !important;

    font-size: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
}}

[data-testid="stFileUploader"] button::before,
[data-testid="stFileUploaderDropzone"] button::before {{
    content: "Upload" !important;
    display: inline-block !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    color: {TEXT} !important;
    -webkit-text-fill-color: {TEXT} !important;
}}

[data-testid="stFileUploader"] button::after,
[data-testid="stFileUploaderDropzone"] button::after {{
    content: none !important;
    display: none !important;
}}

[data-testid="stFileUploader"] button *,
[data-testid="stFileUploaderDropzone"] button * {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    font-size: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
}}

[data-testid="stFileUploader"] small,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] {{
    color: {TEXT} !important;
    -webkit-text-fill-color: {TEXT} !important;
    font-weight: 500 !important;
}}
</style>
<script>
(function() {{
  function fixNumberInputs() {{
    document.querySelectorAll('[data-testid="stNumberInput"] input').forEach(function(el) {{
      if (el.dataset.fixedDouble) return;
      el.dataset.fixedDouble = '1';
      el.addEventListener('wheel', function(e) {{ e.preventDefault(); }}, {{ passive: false }});
    }});
  }}
  var obs = new MutationObserver(fixNumberInputs);
  obs.observe(document.body, {{ subtree: true, childList: true }});
  fixNumberInputs();
}})();
</script>
'''
st.markdown(css, unsafe_allow_html=True)

# Fix number input double-fire (wheel scroll)
import streamlit.components.v1 as components
components.html("""
<script>
(function() {
  function fixNumberInputs() {
    var inputs = window.parent.document.querySelectorAll('[data-testid="stNumberInput"] input');
    inputs.forEach(function(el) {
      if (el.dataset.fixedDouble) return;
      el.dataset.fixedDouble = '1';
      el.addEventListener('wheel', function(e) { e.preventDefault(); }, { passive: false });
    });
  }
  var obs = new window.parent.MutationObserver(fixNumberInputs);
  obs.observe(window.parent.document.body, { subtree: true, childList: true });
  fixNumberInputs();
})();
</script>
""", height=0)

# Sidebar icons handled entirely by CSS (font-size:0 + ::before Unicode)
def initials(name):
    parts = str(name or 'User').strip().split()
    if not parts: return 'U'
    if len(parts) == 1: return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


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



def current_report_datetime():
    """Current India date and time for PDF reports."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M %p")


def reset_prediction_state():
    for k in ['prediction_done', 'patient_data', 'prediction_result', 'confidence', 'prediction_time', 'pdf_bytes', 'current_prediction_patient_name']:
        st.session_state[k] = defaults[k]


def login_user(email, password):
    email = email.strip().lower()
    if email in admins and admins[email] == password:
        st.session_state.logged_in = True; st.session_state.user_type = 'admin'
        st.session_state.current_user_name = 'Admin'; st.session_state.current_user_email = email
        st.session_state.page = 'admin'; st.session_state.prediction_done = False; add_audit('Login', email, 'Admin logged in'); return True, ''
    if email in users and users[email].get('password') == password:
        user = users[email]; st.session_state.logged_in = True; st.session_state.user_type = 'patient'
        st.session_state.current_user_name = user.get('name', 'User'); st.session_state.current_user_email = email
        st.session_state.page = 'prediction'; add_audit('Login', email, 'Patient logged in'); return True, ''
    if email in doctors and doctors[email].get('password') == password:
        doctor = doctors[email]
        if not doctor.get('approved', False): return False, 'Doctor account is waiting for admin approval.'
        st.session_state.logged_in = True; st.session_state.user_type = 'doctor'
        st.session_state.current_user_name = doctor.get('name', 'Doctor'); st.session_state.current_user_email = email
        st.session_state.page = 'prediction'; add_audit('Login', email, 'Doctor logged in'); return True, ''
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
        return ['Monitor blood glucose levels daily and keep a log.', 'Reduce sugar and refined carbohydrate intake significantly.', 'Consult a healthcare professional for proper evaluation and treatment.']
    if patient_data['BMI'] >= 30:
        return ['Follow a balanced calorie-controlled diet with whole foods.', 'Exercise for at least 30 minutes daily — walking, swimming, or cycling.', 'Track your BMI and body weight weekly.']
    if patient_data['BloodPressure'] > 90:
        return ['Reduce sodium and processed food intake to lower BP.', 'Monitor blood pressure regularly with a home device.', 'Practice yoga, walking, or meditation to manage stress.']
    return ['Maintain a balanced, nutritious diet rich in vegetables and whole grains.', 'Exercise regularly — aim for 150 minutes of moderate activity per week.', 'Drink adequate water and get 7-9 hours of quality sleep nightly.']


def nice_label(key):
    label_map = {
        'Pregnancies': 'Pregnancies', 'Glucose': 'Glucose (mg/dL)',
        'BloodPressure': 'Blood Pressure (mmHg)', 'SkinThickness': 'Skin Thickness (mm)',
        'Insulin': 'Insulin (uU/mL)', 'BMI': 'BMI',
        'DiabetesPedigreeFunction': 'Diabetes Pedigree Function', 'Age': 'Age (years)'
    }
    return label_map.get(key, key)


def save_pdf_to_reports_folder(pdf_bytes, name):
    reports_dir = Path('generated_reports')
    reports_dir.mkdir(exist_ok=True)
    safe_name = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in str(name))
    file_path = reports_dir / f"glucotrack_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path.write_bytes(pdf_bytes)
    return str(file_path.resolve())


def create_pdf_chart_image(patient_data):
    labels = ['Glucose', 'BMI', 'Insulin', 'BP', 'Age']
    values = [patient_data['Glucose'], patient_data['BMI'], patient_data['Insulin'], patient_data['BloodPressure'], patient_data['Age']]
    colors = ['#0EA5E9', '#0D9488', '#6366F1', '#F97316', '#F43F5E']
    fig, ax = plt.subplots(figsize=(7.4, 3.15), dpi=190)
    fig.patch.set_facecolor('#FFFFFF'); ax.set_facecolor('#FFFFFF')
    bars = ax.bar(labels, values, color=colors, width=0.58, edgecolor='none')
    ax.set_title('Key Clinical Parameter Overview', fontsize=13, fontweight='bold', pad=14, color='#0A1628')
    ax.set_ylabel('Recorded value', fontsize=9, color='#4A6589')
    ax.spines[['top', 'right', 'left']].set_visible(False); ax.spines['bottom'].set_color('#C8DCF0')
    ax.tick_params(axis='x', labelsize=8, colors='#334155'); ax.tick_params(axis='y', labelsize=8, colors='#64748B', length=0)
    ax.grid(axis='y', alpha=0.18, color='#94A3B8'); ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.025, str(value), ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#0A1628')
    plt.tight_layout()
    img = BytesIO(); fig.savefig(img, format='png', bbox_inches='tight', facecolor='white'); plt.close(fig); img.seek(0)
    return img


def create_risk_gauge_image(confidence, is_high):
    fig, ax = plt.subplots(figsize=(4.8, 2.45), dpi=190, subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor('#FFFFFF'); ax.set_facecolor('#FFFFFF')
    ax.set_theta_offset(3.14159); ax.set_theta_direction(-1); ax.set_ylim(0, 1); ax.axis('off')
    theta = [i * 3.14159 / 180 for i in range(0, 181)]
    ax.plot(theta, [0.72]*len(theta), color='#E2E8F0', linewidth=22, solid_capstyle='round')
    val = max(0, min(float(confidence), 100))
    theta_val = [i * 3.14159 / 180 for i in range(0, int(180*val/100)+1)]
    color = '#F43F5E' if is_high else '#0D9488'
    ax.plot(theta_val, [0.72]*len(theta_val), color=color, linewidth=22, solid_capstyle='round')
    ax.text(3.14159/2, 0.30, f'{val:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold', color='#0A1628')
    ax.text(3.14159/2, 0.10, 'Model confidence', ha='center', va='center', fontsize=9, color='#64748B')
    img = BytesIO(); fig.savefig(img, format='png', bbox_inches='tight', facecolor='white'); plt.close(fig); img.seek(0)
    return img


def generate_pdf(patient_data, result, confidence, name, email, pred_time=None, extra=None):
    """Clean two-section PDF: patient/doctor info + full clinical report."""
    if extra is None: extra = {}
    pred_time = current_report_datetime()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    # ── Colour palette ──────────────────────────────────────────────────────
    C_NAVY   = (0.06,0.09,0.20)
    C_ROYAL  = (0.24,0.47,0.98)
    C_TEAL   = (0.05,0.58,0.53)
    C_SLATE  = (0.10,0.14,0.24)
    C_MUTED  = (0.38,0.44,0.58)
    C_SOFT   = (0.96,0.97,1.00)
    C_LINE   = (0.82,0.86,0.96)
    C_WHITE  = (1,1,1)
    high = 'High' in result

    def rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))

    def setc(c):   pdf.setFillColorRGB(*c)
    def setstroke(c): pdf.setStrokeColorRGB(*c)

    def rect_fill(x,y,w,h,fill,stroke_c=None,radius=10,lw=0.7):
        if stroke_c is None: stroke_c = C_LINE
        setc(fill); setstroke(stroke_c); pdf.setLineWidth(lw)
        pdf.roundRect(x,y,w,h,radius,fill=True,stroke=True)

    def section_title(x,y,text):
        pdf.setFont('Helvetica-Bold',11); setc(C_SLATE)
        pdf.drawString(x,y,text)
        setstroke(C_ROYAL); pdf.setLineWidth(1.5)
        pdf.line(x,y-4,x+len(text)*6.2,y-4)

    def field_row(x,y,label,value,lw=90):
        pdf.setFont('Helvetica',8); setc(C_MUTED); pdf.drawString(x,y,label)
        pdf.setFont('Helvetica-Bold',9); setc(C_SLATE); pdf.drawString(x+lw,y,str(value) if value else '—')

    # ════════════════════════════════════════════════════════════════════════
    # HEADER BANNER
    # ════════════════════════════════════════════════════════════════════════
    setc(C_NAVY); pdf.rect(0,H-90,W,90,fill=True,stroke=False)
    # Logo box
    setc(C_ROYAL); pdf.roundRect(30,H-72,44,44,8,fill=True,stroke=False)
    pdf.setFont('Helvetica-Bold',20); setc(C_WHITE); pdf.drawString(42,H-50,'🩺')
    # Title
    pdf.setFont('Helvetica-Bold',20); setc(C_WHITE); pdf.drawString(86,H-46,'GlucoTrack  Clinical Report')
    pdf.setFont('Helvetica',9); setc((0.65,0.78,0.95))
    pdf.drawString(86,H-62,'Diabetes Risk Assessment  ·  Health Analytics  ·  Action Plan')
    pdf.drawString(86,H-76,f'Generated: {pred_time}')
    # Risk badge
    badge_bg  = rgb('#FEE2E2') if high else rgb('#D1FAE5')
    badge_txt = rgb('#991B1B') if high else rgb('#065F46')
    rect_fill(W-148,H-72,118,28,badge_bg,badge_bg,radius=14,lw=0)
    pdf.setFont('Helvetica-Bold',10); setc(badge_txt)
    pdf.drawCentredString(W-89,H-54,'⚠ HIGH RISK' if high else '✓ LOW RISK')

    y = H - 110   # cursor below banner

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1 — PATIENT & DOCTOR INFORMATION
    # ════════════════════════════════════════════════════════════════════════
    section_title(30, y, 'Patient & Doctor Information')
    y -= 14

    # Patient info card (left half)
    p_age     = extra.get('age', patient_data.get('Age','N/A'))
    p_gender  = extra.get('gender','N/A')
    p_phone   = extra.get('phone','N/A')
    p_address = extra.get('address','N/A')
    doc_name  = extra.get('doctor_name','')
    doc_email_val = extra.get('doctor_email','')

    card_h = 108 if (doc_name or doc_email_val) else 80
    half   = (W - 72) / 2

    rect_fill(30, y-card_h, half, card_h, C_SOFT, C_LINE, radius=10)
    pdf.setFont('Helvetica-Bold',9); setc(C_ROYAL)
    pdf.drawString(42, y-14, 'PATIENT')
    field_row(42, y-28, 'Name:',    name)
    field_row(42, y-42, 'Email:',   email)
    field_row(42, y-56, 'Age / Gender:', f'{p_age} yrs  ·  {p_gender}')
    field_row(42, y-70, 'Phone:',   p_phone)
    if card_h > 80:
        field_row(42, y-84, 'Address:', p_address)

    # Doctor info card (right half) — only if doctor details present
    rx = 30 + half + 12
    if doc_name or doc_email_val:
        rect_fill(rx, y-card_h, half, card_h, C_SOFT, C_LINE, radius=10)
        pdf.setFont('Helvetica-Bold',9); setc(C_TEAL)
        pdf.drawString(rx+12, y-14, 'ASSESSED BY')
        field_row(rx+12, y-28, 'Doctor:',  f'Dr. {doc_name}')
        field_row(rx+12, y-42, 'Email:',   doc_email_val)
        field_row(rx+12, y-56, 'Date:',    pred_time.split(' ')[0] if ' ' in pred_time else pred_time)

    y -= card_h + 18

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2 — RISK RESULT
    # ════════════════════════════════════════════════════════════════════════
    section_title(30, y, 'Risk Assessment Result')
    y -= 14

    risk_bg  = rgb('#FEF2F2') if high else rgb('#ECFDF5')
    risk_bdr = rgb('#FCA5A5') if high else rgb('#6EE7B7')
    risk_txt = rgb('#991B1B') if high else rgb('#065F46')
    rect_fill(30, y-70, W-60, 70, risk_bg, risk_bdr, radius=14, lw=1.2)
    pdf.setFont('Helvetica-Bold',16); setc(risk_txt)
    pdf.drawString(48, y-30, result)
    pdf.setFont('Helvetica',9); setc(C_MUTED)
    pdf.drawString(48, y-52, 'Based on 8 clinical parameters via ML model')
    pdf.setFont('Helvetica-Bold',20); setc(risk_txt)
    pdf.drawRightString(W-48, y-28, f'{confidence}%')
    pdf.setFont('Helvetica',8); setc(C_MUTED)
    pdf.drawRightString(W-48, y-48, 'confidence score')

    y -= 92

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3 — QUICK HEALTH SUMMARY (4 cards in a row)
    # ════════════════════════════════════════════════════════════════════════
    section_title(30, y, 'Quick Health Summary')
    y -= 14

    summary = [
        ('Glucose',        f"{patient_data.get('Glucose','N/A')} mg/dL", '#0EA5E9'),
        ('BMI',            f"{patient_data.get('BMI','N/A')}",            '#0D9488'),
        ('Blood Pressure', f"{patient_data.get('BloodPressure','N/A')} mmHg", '#F97316'),
        ('Age',            f"{patient_data.get('Age','N/A')} yrs",        '#6366F1'),
    ]
    cw = (W - 72) / 4
    for i, (title, value, color_hex) in enumerate(summary):
        cx = 30 + i * (cw + 4)
        rect_fill(cx, y-72, cw, 72, C_WHITE, C_LINE, radius=12)
        setc(rgb(color_hex)); pdf.roundRect(cx+10,y-22,6,30,3,fill=True,stroke=False)
        pdf.setFont('Helvetica',8); setc(C_MUTED); pdf.drawString(cx+22,y-20,title)
        pdf.setFont('Helvetica-Bold',13); setc(C_SLATE); pdf.drawString(cx+22,y-50,value)

    y -= 94

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4 — CLINICAL MEASUREMENTS (2-column grid)
    # ════════════════════════════════════════════════════════════════════════
    section_title(30, y, 'Clinical Measurements')
    y -= 14

    items  = list(patient_data.items())
    col_w  = (W - 72) / 2
    row_h  = 40
    for idx, (key, value) in enumerate(items):
        col = idx % 2; row = idx // 2
        x   = 30 + col * (col_w + 12)
        yy  = y - row * row_h
        rect_fill(x, yy-32, col_w, 32, C_WHITE, C_LINE, radius=8, lw=0.5)
        pdf.setFont('Helvetica',8.5); setc(C_MUTED); pdf.drawString(x+12, yy-21, nice_label(key))
        pdf.setFont('Helvetica-Bold',9.5); setc(C_SLATE); pdf.drawRightString(x+col_w-12, yy-21, str(value))

    rows_used = (len(items) + 1) // 2
    y -= rows_used * row_h + 12

    # Page 1 bottom note to avoid empty-looking page
    setstroke(C_LINE)
    pdf.setLineWidth(0.6)
    pdf.line(30, 52, W-30, 52)
    pdf.setFont('Helvetica-Oblique', 7)
    setc(C_MUTED)
    pdf.drawCentredString(W/2, 38, 'Page 1 of 2  ·  Patient summary and clinical measurements')

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 2 — HEALTH ANALYTICS + ACTION PLAN
    # ════════════════════════════════════════════════════════════════════════

    # Start second page
    pdf.showPage()

    # Second page header
    setc(C_NAVY)
    pdf.rect(0, H-70, W, 70, fill=True, stroke=False)

    pdf.setFont('Helvetica-Bold', 16)
    setc(C_WHITE)
    pdf.drawString(30, H-42, 'GlucoTrack Clinical Report')

    pdf.setFont('Helvetica', 8)
    setc((0.65, 0.78, 0.95))
    pdf.drawString(30, H-56, f'Generated: {pred_time}')

    y = H - 105

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5 — HEALTH ANALYTICS
    # ════════════════════════════════════════════════════════════════════════

    section_title(30, y, 'Health Analytics')
    y -= 18

    chart_img = create_pdf_chart_image(patient_data)
    gauge_img = create_risk_gauge_image(confidence, high)
    chart_h   = 150
    chart_w   = int((W - 72) * 0.62)
    gauge_w   = int((W - 72) * 0.34)

    rect_fill(30, y-chart_h, chart_w, chart_h, C_WHITE, C_LINE, radius=10)
    pdf.drawImage(ImageReader(chart_img), 36, y-chart_h+6, width=chart_w-12, height=chart_h-12,
                  preserveAspectRatio=True, mask='auto')

    rect_fill(30+chart_w+12, y-chart_h, gauge_w, chart_h, C_WHITE, C_LINE, radius=10)
    gx = 30+chart_w+12
    pdf.drawImage(ImageReader(gauge_img), gx+6, y-chart_h+14, width=gauge_w-12, height=chart_h-28,
                  preserveAspectRatio=True, mask='auto')
    pdf.setFont('Helvetica-Bold',8); setc(C_SLATE)
    pdf.drawCentredString(gx+gauge_w/2, y-chart_h+6, 'Confidence Gauge')

    y -= chart_h + 18

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 6 — HEALTH ACTION PLAN
    # ════════════════════════════════════════════════════════════════════════

    suggestions = get_suggestions(patient_data)
    footer_y = 45



    section_title(30, y, 'Recommended Health Action Plan')
    y -= 22

    plan_h = max(110, len(suggestions) * 30 + 34)
    rect_fill(30, y-plan_h, W-60, plan_h, rgb('#F0FDFA'), rgb('#99F6E4'), radius=12)

    yy = y - 28
    for i, s in enumerate(suggestions, 1):
        s_clean = ''.join(c for c in s if ord(c)<65536 and not (0x1F000<=ord(c)<=0x1FFFF)).strip()
        setc(C_TEAL)
        pdf.circle(50, yy+4, 8, fill=True, stroke=False)
        setc(C_WHITE)
        pdf.setFont('Helvetica-Bold', 7.5)
        pdf.drawCentredString(50, yy+1.5, str(i))

        setc(C_SLATE)
        pdf.setFont('Helvetica', 9.5)
        pdf.drawString(68, yy, s_clean)
        yy -= 30

    # Footer on same fresh page, far below the action plan
    setstroke(C_LINE)
    pdf.setLineWidth(0.6)
    pdf.line(30, footer_y, W-30, footer_y)

    pdf.setFont('Helvetica-Oblique', 7)
    setc(C_MUTED)
    pdf.drawCentredString(W/2, footer_y - 14, 'Disclaimer: This report is for educational and screening purposes only — not a medical diagnosis.')
    pdf.drawCentredString(W/2, footer_y - 28, 'Please consult a qualified healthcare professional before making any medical decisions.')

    pdf.save()
    return buffer.getvalue()


def page_header(icon, title, subtitle):
    """Pure st.markdown page header — no components.html, no iframe overlap."""
    st.markdown(f'''
<div class="page-head">
    <div class="page-icon">{icon}</div>
    <div>
        <span class="page-title-text">{title}</span>
        <span class="page-sub">{subtitle}</span>
    </div>
</div>
''', unsafe_allow_html=True)


def public_header():
    col_logo, col_nav, col_spacer, col_theme, col_signin = st.columns([2.5, 4.0, 2.0, 1.2, 1.2])
    with col_logo:
        st.markdown(f'''
<div style="display:flex;align-items:center;gap:12px;font-family:'Sora',sans-serif;font-size:22px;font-weight:900;color:{TEXT};margin-top:10px;">
    <div style="width:38px;height:38px;border-radius:10px;background:{GRAD_PRIMARY};color:white;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;">🩺</div>
    GlucoTrack
</div>''', unsafe_allow_html=True)
    with col_nav:
        st.markdown(f'''
<div style="display:flex;gap:28px;margin-top:14px;">
    <a href="#features" class="nav-link" target="_self"> Features</a>
    <a href="#how-it-works" class="nav-link" target="_self"> How It Works</a>
</div>''', unsafe_allow_html=True)
    with col_theme:
        theme_label = ' Light' if st.session_state.dark_mode else ' Dark'
        if st.button(theme_label, key='pub_theme_toggle', type='secondary', use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode; st.rerun()
    with col_signin:
        if st.button('Sign In →', key='nav_signin', type='primary', use_container_width=True):
            st.session_state.started = True; st.session_state.page = 'auth'; st.session_state.auth_mode = 'signin'; st.rerun()
    st.markdown('<div class="grad-divider"></div>', unsafe_allow_html=True)


def dashboard_sidebar():
    if not st.session_state.started or not st.session_state.logged_in:
        return

    name = st.session_state.current_user_name
    email = st.session_state.current_user_email
    role = {
        'patient': '🧑 Patient',
        'doctor': '👨‍⚕️ Doctor',
        'admin': '🛡️ Admin'
    }.get(st.session_state.user_type, 'User')

    init = initials(name)

    profile_pic = None
    if st.session_state.user_type == 'patient' and email in users:
        profile_pic = users[email].get('profile_pic')
    elif st.session_state.user_type == 'doctor' and email in doctors:
        profile_pic = doctors[email].get('profile_pic')

    if profile_pic:
        avatar_html = f'<img src="data:image/png;base64,{profile_pic}" class="sb-avatar-img" alt="Profile photo">'
    else:
        avatar_html = f'<div class="sb-avatar">{init}</div>'

    st.sidebar.markdown(f'''
<div class="sb-header">
    <div class="sb-logo-box">🩺</div>
    <div class="sb-brand">GlucoTrack</div>
</div>
<div class="sb-profile">
    {avatar_html}
    <div class="sb-info">
        <div class="sb-name">{name if name else "User"}</div>
        <div class="sb-role">{role}</div>
    </div>
</div>
''', unsafe_allow_html=True)

    if st.sidebar.button(' Edit Profile', use_container_width=True):
        st.session_state.page = 'profile'
        st.rerun()

    st.sidebar.markdown('<div style="padding:10px 8px 4px;">', unsafe_allow_html=True)
    new_dark = st.sidebar.toggle(
        '🌙 Dark Mode' if st.session_state.dark_mode else '☀️ Light Mode',
        value=st.session_state.dark_mode,
        key='sidebar_dark_toggle'
    )
    if new_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.user_type == 'patient':
        options = ['prediction', 'dashboard']
        labels = ['🩺 Predict Risk', '📊 Health Dashboard']
    elif st.session_state.user_type == 'doctor':
        options = ['prediction', 'doctor', 'dashboard']
        labels = ['🩺 Predict Risk', '👨‍⚕️ Patient Data', '📊 Health Dashboard']
    else:
        options = ['admin']
        labels = ['🛡️ Admin Panel']

    if st.session_state.page not in options and st.session_state.page != 'profile':
        st.session_state.page = options[0]

    if st.session_state.page != 'profile':
        idx = options.index(st.session_state.page) if st.session_state.page in options else 0
        selected_label = st.sidebar.radio('', labels, index=idx, label_visibility='collapsed')
        selected_page = options[labels.index(selected_label)]
        if selected_page != st.session_state.page:
            st.session_state.page = selected_page
            st.rerun()

    st.sidebar.markdown(
        f'''
        <div style="height:120px;"></div>
        <div style="padding:0 8px 4px;">
            <div style="height:1px;background:{GRAD_PRIMARY};border-radius:99px;opacity:0.4;margin-bottom:14px;"></div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    if st.sidebar.button('↪ Sign Out', use_container_width=True):
        add_audit('Logout', st.session_state.current_user_email, 'User logged out')
        for key in [
            'logged_in', 'user_type', 'current_user_name', 'current_user_email',
            'prediction_done', 'patient_data', 'prediction_result',
            'confidence', 'prediction_time', 'pdf_bytes'
        ]:
            st.session_state[key] = defaults[key]
        st.session_state.page = 'auth'
        st.session_state.auth_mode = 'signin'
        st.rerun()



def landing_page():
    public_header()
    st.markdown(f'''
<section class="hero-section">
    <div class="hero-card">
        <div class="hero-badge"> AI-POWERED HEALTH PLATFORM</div>
        <h1 class="hero-title">Welcome To GlucoTrack !</h1>
        <p class="hero-sub">Predict diabetes risk in seconds using Machine Learning.<br>Understand your health. Take action early. Live better.</p>
        <div style="position:relative;z-index:2;display:flex;justify-content:center;gap:14px;margin-top:8px;">
            <a href="?hero_clicked=1" style="display:inline-flex;align-items:center;justify-content:center;gap:10px;background:rgba(255,255,255,0.22);color:white !important;text-decoration:none;border-radius:14px;padding:15px 44px;font-family:'DM Sans',sans-serif;font-weight:700;font-size:16px;cursor:pointer;border:2px solid rgba(255,255,255,0.40);backdrop-filter:blur(8px);"> Get Started </a>
        </div>
        <div class="hero-stats">
            <div class="hero-stat"><div class="hero-stat-num">95%+</div><div class="hero-stat-label">Model Accuracy</div></div>
            <div class="hero-stat"><div class="hero-stat-num">8</div><div class="hero-stat-label">Health Parameters</div></div>
            <div class="hero-stat"><div class="hero-stat-num">100%</div><div class="hero-stat-label">Free to Use</div></div>
        </div>
    </div>
</section>
''', unsafe_allow_html=True)

    params = st.query_params
    if params.get('hero_clicked') == '1':
        st.query_params.clear()
        st.session_state.started = True; st.session_state.page = 'auth'; st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()

    st.markdown(f'''
<section id="features" class="section" style="padding-top:48px;">
    <h2 class="section-title"> What GlucoTrack Does</h2>
    <p class="section-sub">Three powerful features to monitor, predict, and improve your health</p>
    <div class="feature-grid">
        <div class="feature-card feature-blue"><div class="pill pill-blue">🧠 MACHINE LEARNING</div><div class="icon-box icon-blue">🔬</div><div class="feature-title">AI-Powered Risk Prediction</div><div class="feature-text">Our trained ML model analyzes 8 clinical parameters — Glucose, BMI, Insulin, Blood Pressure, Age, Pregnancies, Skin Thickness, and DPF — to compute your diabetes risk with a confidence score.</div></div>
        <div class="feature-card feature-green"><div class="pill pill-green">📊 ANALYTICS</div><div class="icon-box icon-green">📈</div><div class="feature-title">Interactive Health Dashboard</div><div class="feature-text">Visualize your health data through dynamic charts, glucose gauges, and BMI indicators inside a clean, beautiful dashboard. Track your progress over time.</div></div>
        <div class="feature-card feature-purple"><div class="pill pill-purple">💡 PERSONALIZED</div><div class="icon-box icon-purple">🩺</div><div class="feature-title">Smart Health Recommendations</div><div class="feature-text">Get targeted, personalized health recommendations based on your specific clinical values — diet tips, exercise plans, and lifestyle changes tailored just for you.</div></div>
    </div>
</section>
<section id="how-it-works" class="section">
    <h2 class="section-title"> How It Works</h2>
    <p class="section-sub">Get your diabetes risk assessment in 4 simple steps</p>
    <div class="steps-grid">
        <div class="step-card"><div class="step-num">01</div><div class="step-title">🔐 Create Account</div><div class="step-text">Sign up free with your name and email address in under a minute</div></div>
        <div class="step-card"><div class="step-num">02</div><div class="step-title">🩺 Enter Health Data</div><div class="step-text">Fill in your 8 clinical health values from your latest lab report</div></div>
        <div class="step-card"><div class="step-num">03</div><div class="step-title">🤖 Get AI Prediction</div><div class="step-text">Our ML model instantly calculates your personalized diabetes risk</div></div>
        <div class="step-card"><div class="step-num">04</div><div class="step-title">📄 View & Share Report</div><div class="step-text">Download a PDF report or share it directly via WhatsApp with your doctor</div></div>
    </div>
</section>
<section class="section" style="padding-bottom:24px;">
    <div class="bottom-cta">
        <div style="font-size:48px;margin-bottom:16px;">❤️</div>
        <h2 style="font-family:'Sora',sans-serif;font-size:36px;font-weight:900;margin:0 0 16px;color:white !important;">Take Control of Your Health Today</h2>
        <p style="font-size:19px;line-height:1.6;margin-bottom:0;color:rgba(255,255,255,0.88) !important;">Join thousands using GlucoTrack to monitor their diabetes risk. Free, fast, and takes less than 2 minutes.</p>
    </div>
</section>
''', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.8, 1.5, 1.8])
    with c2:
        if st.button(' Create Account →', key='bottom_signup_btn', type='primary', use_container_width=True):
            st.session_state.started = True; st.session_state.page = 'auth'; st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()

    st.markdown(f'<div style="text-align:center;margin:16px 0 0;color:{MUTED};font-size:14px;">✅ Free forever &nbsp;·&nbsp; 🔒 Private &amp; secure &nbsp;·&nbsp; ⚡ Results in seconds</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="footer"><div class="footer-logo">🩺 GlucoTrack</div><div>For educational purposes only. Always consult a medical professional.</div><div>© 2025 GlucoTrack</div></div>', unsafe_allow_html=True)


def auth_page():
    st.markdown(f'''<style>.stApp{{background:{'linear-gradient(135deg,#0A1628 0%,#0f1e3c 50%,#1a0533 100%)' if DARK else 'linear-gradient(135deg,#A5B4FC 0%,#C4B5FD 45%,#DDD6FE 100%)'}!important;}}</style>''', unsafe_allow_html=True)
    public_header()
    if st.button('← Back to Home', key='auth_back_home', type='secondary'):
        st.session_state.started = False; st.session_state.page = 'home'; st.rerun()

    if st.session_state.auth_mode == 'signin':
        st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Welcome back 👋</h1><p>Sign in to continue to your health dashboard</p></div>', unsafe_allow_html=True)
        c1, col_card, c3 = st.columns([1, 1.8, 1])
        with col_card:
            with st.container(border=True):
                email = st.text_input(' Email address', placeholder='you@example.com', key='signin_email')
                password = st.text_input(' Password', type='password', placeholder='Your password', key='signin_password')
                # Forgot password — single right-aligned link only, no button shown
                # We use a query_param navigation, same as the original href approach
                st.markdown(f'''
<style>#fp_goto_btn {{ display:none !important; }}</style>
<div style="display:flex;justify-content:flex-end;margin:-4px 2px 10px;">
  <a href="?forgot_password=1" target="_self"
     style="color:{GRAD1};font-size:13px;font-weight:700;
            text-decoration:underline;text-underline-offset:3px;">
    Forgot password?
  </a>
</div>
''', unsafe_allow_html=True)
                is_admin = st.checkbox('Are you an admin or doctor?', key='is_admin_login')
                st.write('')
                if st.button('Sign In →', type='primary', use_container_width=True, key='signin_btn'):
                    ok, msg = login_user(email, password)
                    if ok: st.rerun()
                    else:
                        st.error(f'❌ {msg}')
                        col_hint, col_reset = st.columns([3, 1])
                        with col_hint:
                            st.markdown(f'<div style="font-size:12px;color:{MUTED};margin-top:4px;">💡 Use your registered password, or click Reset to restore demo credentials.</div>', unsafe_allow_html=True)
                        with col_reset:
                            if st.button('🔄 Reset Demo', key='reset_demo_btn', use_container_width=True):
                                users['user@gmail.com'] = DEFAULT_USERS['user@gmail.com'].copy()
                                save_json(USERS_FILE, users)
                                st.success('✅ Demo account reset! Use user@gmail.com / user@123'); st.rerun()
                st.markdown(f'<div style="text-align:center;margin:18px 0;color:{MUTED};">— or —</div>', unsafe_allow_html=True)
                if st.button(' Create account →', type='secondary', use_container_width=True, key='to_signup'):
                    st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()
                st.markdown(f'<p style="text-align:center;color:{MUTED};margin-top:20px;">🔒 Your health data is private and never shared.</p>', unsafe_allow_html=True)

    elif st.session_state.auth_mode == 'forgot_password':
        st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Reset Password </h1><p>Enter your registered email to reset your password</p></div>', unsafe_allow_html=True)
        c1, col_card, c3 = st.columns([1, 1.8, 1])
        with col_card:
            with st.container(border=True):
                fp_step = st.session_state.get('fp_step', 1)

                if fp_step == 1:
                    # Step 1: enter email
                    st.markdown(f'<div style="font-family:Sora,sans-serif;font-weight:700;font-size:15px;color:{TEXT};margin-bottom:14px;">Step 1 — Verify your email</div>', unsafe_allow_html=True)
                    fp_email = st.text_input(' Registered Email', placeholder='you@example.com', key='fp_email')
                    st.write('')
                    if st.button('Continue →', type='primary', use_container_width=True, key='fp_continue'):
                        fp_email_val = fp_email.strip().lower()
                        if fp_email_val in users:
                            st.session_state.fp_email_val = fp_email_val
                            st.session_state.fp_account_type = 'patient'
                            st.session_state.fp_step = 2; st.rerun()
                        elif fp_email_val in doctors:
                            st.session_state.fp_email_val = fp_email_val
                            st.session_state.fp_account_type = 'doctor'
                            st.session_state.fp_step = 2; st.rerun()
                        else:
                            st.error('❌ No account found with this email address.')

                elif fp_step == 2:
                    # Step 2: verify identity via phone (patients) or licence no (doctors)
                    fp_email_val   = st.session_state.get('fp_email_val','')
                    fp_account_type = st.session_state.get('fp_account_type','patient')
                    st.markdown(f'<div style="font-family:Sora,sans-serif;font-weight:700;font-size:15px;color:{TEXT};margin-bottom:6px;">Step 2 — Verify your identity</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:13px;color:{MUTED};margin-bottom:14px;">Account: <b>{fp_email_val}</b></div>', unsafe_allow_html=True)
                    if fp_account_type == 'doctor':
                        verify_val = st.text_input(' Registered Licence Number', placeholder='Your licence no.', key='fp_verify')
                        hint = 'licence number'
                        stored = doctors.get(fp_email_val,{}).get('license_no','')
                    else:
                        verify_val = st.text_input(' Registered Phone Number', placeholder='+91 98765 43210', key='fp_verify')
                        hint = 'phone number'
                        stored = users.get(fp_email_val,{}).get('phone','')
                    st.write('')
                    if st.button('Verify →', type='primary', use_container_width=True, key='fp_verify_btn'):
                        if verify_val.strip() == stored.strip():
                            st.session_state.fp_step = 3; st.rerun()
                        else:
                            st.error(f'❌ {hint.capitalize()} does not match our records.')

                elif fp_step == 3:
                    # Step 3: set new password
                    fp_email_val   = st.session_state.get('fp_email_val','')
                    fp_account_type = st.session_state.get('fp_account_type','patient')
                    st.markdown(f'<div style="font-family:Sora,sans-serif;font-weight:700;font-size:15px;color:{TEXT};margin-bottom:6px;">Step 3 — Set new password</div>', unsafe_allow_html=True)
                    new_pw  = st.text_input(' New Password', type='password', placeholder='Min 6 characters', key='fp_new_pw')
                    conf_pw = st.text_input(' Confirm Password', type='password', placeholder='Repeat new password', key='fp_conf_pw')
                    st.write('')
                    if st.button('Reset Password ✓', type='primary', use_container_width=True, key='fp_reset_btn'):
                        if len(new_pw) < 6:
                            st.error('❌ Password must be at least 6 characters.')
                        elif new_pw != conf_pw:
                            st.error('❌ Passwords do not match.')
                        else:
                            if fp_account_type == 'doctor':
                                doctors[fp_email_val]['password'] = new_pw
                                save_json(DOCTORS_FILE, doctors)
                            else:
                                users[fp_email_val]['password'] = new_pw
                                save_json(USERS_FILE, users)
                            st.success('✅ Password reset successfully! Please sign in.')
                            for k in ['fp_step','fp_email_val','fp_account_type']:
                                st.session_state.pop(k, None)
                            st.session_state.auth_mode = 'signin'
                            st.rerun()

                st.markdown(f'<div style="text-align:center;margin-top:18px;"></div>', unsafe_allow_html=True)
                if st.button('← Back to Sign In', key='fp_back', use_container_width=True):
                    for k in ['fp_step','fp_email_val','fp_account_type']:
                        st.session_state.pop(k, None)
                    st.session_state.auth_mode = 'signin'; st.rerun()
    elif st.session_state.auth_mode == 'signup':
        if st.session_state.signup_step == 1:
            st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Create your account 🎉</h1><p>Step 1 of 2 — Personal Details</p><div style="height:6px;background:{GRAD_PRIMARY};border-radius:8px;max-width:560px;margin:28px auto 0;width:50%;"></div></div>', unsafe_allow_html=True)
            c1, col_card, c3 = st.columns([1, 1.8, 1])
            with col_card:
                with st.container(border=True):
                    full_name = st.text_input(' Full Name *', placeholder='John Doe', key='reg_name')
                    email = st.text_input('Email Address *', placeholder='you@example.com', key='reg_email')
                    phone = st.text_input(' Phone Number *', placeholder='+91 98765 43210', key='reg_phone')
                    c_a, c_b = st.columns(2)
                    with c_a: age = st.number_input(' Age *', 1, 100, 25, key='reg_age')
                    with c_b: gender = st.selectbox('⚧ Gender', ['Select', 'Female', 'Male', 'Other'], key='reg_gender')
                    address = st.text_area(' Address', placeholder='Your address (optional)', key='reg_address')
                    if st.button('Continue →', type='primary', use_container_width=True, key='reg_continue'):
                        email_clean = email.strip().lower()
                        if not full_name or not email_clean or not phone: st.error('⚠️ Please fill all required fields.')
                        elif gender == 'Select': st.error('⚠️ Please select your gender.')
                        elif email_clean in users or email_clean in doctors or email_clean in admins: st.error('❌ Email already registered. Please sign in.')
                        else:
                            st.session_state.signup_name = full_name.strip(); st.session_state.signup_email = email_clean
                            st.session_state.signup_phone = phone.strip(); st.session_state.signup_age = age
                            st.session_state.signup_gender = gender; st.session_state.signup_address = address.strip()
                            st.session_state.signup_step = 2; st.rerun()
                    if st.button('Already have an account? Sign in', type='secondary', use_container_width=True, key='step1_to_signin'):
                        st.session_state.auth_mode = 'signin'; st.rerun()
        else:
            st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Almost there! 🔐</h1><p>Step 2 of 2 — Set Your Password</p><div style="height:6px;background:{GRAD_PRIMARY};border-radius:8px;max-width:560px;margin:28px auto 0;width:100%;"></div></div>', unsafe_allow_html=True)
            c1, col_card, c3 = st.columns([1, 1.8, 1])
            with col_card:
                with st.container(border=True):
                    password = st.text_input('🔒 Create Password', type='password', placeholder='At least 6 characters', key='reg_password')
                    confirm = st.text_input('🔑 Confirm Password', type='password', placeholder='Re-enter password', key='reg_confirm')
                    label, color, width_pct, hints = password_strength(password)
                    if password:
                        hint_text = f"add {', '.join(hints)}" if hints else 'Strong password ✓'
                        st.markdown(f'<div style="margin:-4px 0 18px;"><div style="height:5px;border-radius:5px;background:#E2E8F0;overflow:hidden;"><div style="height:100%;width:{width_pct}%;background:{color};border-radius:5px;"></div></div><div style="font-size:13px;color:{color};font-weight:700;margin-top:6px;">{label} · {hint_text}</div></div>', unsafe_allow_html=True)
                    c_a, c_b = st.columns(2)
                    with c_a:
                        if st.button('← Back', type='secondary', use_container_width=True, key='back_signup'):
                            st.session_state.signup_step = 1; st.rerun()
                    with c_b:
                        if st.button('Create Account ✓', type='primary', use_container_width=True, key='create_account_btn'):
                            if not password: st.error('⚠️ Please enter a password.')
                            elif len(password) < 6: st.error('⚠️ Password must be at least 6 characters.')
                            elif password != confirm: st.error('❌ Passwords do not match.')
                            else:
                                st.session_state.signup_password = password; st.session_state.page = 'create_profile'; st.rerun()
                    if st.button('Already have an account? Sign in', type='secondary', use_container_width=True, key='step2_to_signin'):
                        st.session_state.auth_mode = 'signin'; st.rerun()


def create_profile_page():
    st.markdown(f'''<style>.stApp{{background:{'linear-gradient(135deg,#0A1628 0%,#0f1e3c 50%,#1a0533 100%)' if DARK else 'linear-gradient(135deg,#A5B4FC 0%,#C4B5FD 45%,#DDD6FE 100%)'}!important;}}</style>''', unsafe_allow_html=True)
    public_header()

    # ── Doctor approval-pending confirmation screen ──────────────────────
    if st.session_state.get('doctor_signup_done'):
        c1, col_card, c3 = st.columns([1, 1.8, 1])
        with col_card:
            st.markdown(f'''
<div style="text-align:center;padding:40px 24px 32px;">
    <div style="font-size:68px;margin-bottom:18px;">🎉</div>
    <h2 style="font-family:Sora,sans-serif;font-size:26px;font-weight:900;
               color:{TEXT};margin-bottom:10px;">Doctor Account Created!</h2>
    <p style="font-size:15px;color:{MUTED};line-height:1.7;margin-bottom:28px;">
        Your profile has been submitted successfully.<br>
        An <b style="color:{TEXT};">admin will review and approve</b> your account shortly.<br>
        You can sign in once approved.
    </p>
    <div style="background:{'rgba(109,40,217,0.12)' if DARK else 'rgba(109,40,217,0.06)'};
                border:1px solid {BORDER};border-radius:16px;
                padding:20px 24px;margin-bottom:28px;text-align:left;">
        <div style="font-family:Sora,sans-serif;font-weight:800;font-size:14px;
                    color:{TEXT};margin-bottom:14px;">📋 What happens next?</div>
''', unsafe_allow_html=True)
            for num, step in enumerate([
                'Admin reviews your licence number and hospital details',
                'Your account gets approved (usually within 24 hours)',
                'Sign in with your registered email and password',
            ], 1):
                st.markdown(f'''
<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
    <div style="min-width:28px;height:28px;border-radius:50%;
                background:linear-gradient(135deg,{GRAD1},{GRAD2});
                color:white;display:flex;align-items:center;justify-content:center;
                font-weight:800;font-size:12px;flex-shrink:0;">{num}</div>
    <span style="font-size:14px;color:{MUTED};">{step}</span>
</div>
''', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)
            if st.button('→ Go to Sign In', type='primary',
                         use_container_width=True, key='doctor_done_signin'):
                st.session_state.doctor_signup_done = False
                st.session_state.page      = 'auth'
                st.session_state.auth_mode = 'signin'
                st.rerun()
        return  # ← don't render the form below

    # ── Normal back button (only shown on the form, not on success screen) ──
    if st.button('← Back to Password Setup', key='create_profile_back', type='secondary'):
        st.session_state.page = 'auth'
        st.session_state.auth_mode = 'signup'
        st.session_state.signup_step = 2
        st.rerun()

    st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Choose Your Profile 👤</h1><p>Are you a patient or a healthcare professional?</p></div>', unsafe_allow_html=True)

    c1, col_card, c3 = st.columns([1, 1.8, 1])
    with col_card:
        with st.container(border=True):
            role = st.radio('I am a', ['🧑 Patient', '👨‍⚕️ Doctor'], horizontal=True)
            name  = st.text_input(' Full Name', value=st.session_state.signup_name)
            email = st.text_input(' Email', value=st.session_state.signup_email, disabled=True)

            # ── PATIENT ──────────────────────────────────────────────────
            if '🧑' in role:
                phone  = st.text_input(' Phone', value=st.session_state.signup_phone)
                age    = st.number_input(' Age', 1, 100, int(st.session_state.signup_age))
                gender = st.selectbox(' Gender', ['Female', 'Male', 'Other'],
                                      index=['Female','Male','Other'].index(st.session_state.signup_gender)
                                      if st.session_state.signup_gender in ['Female','Male','Other'] else 0)
                address        = st.text_area(' Address', value=st.session_state.signup_address)
                uploaded_photo = st.file_uploader(' Upload Profile Photo (Optional)',
                                                  type=['png','jpg','jpeg'], key='patient_photo')
                if st.button(' Create Patient Profile', type='primary', use_container_width=True):
                    base64_photo = None
                    if uploaded_photo:
                        base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                    users[st.session_state.signup_email] = {
                        'password': st.session_state.signup_password, 'name': name,
                        'phone': phone, 'age': age, 'gender': gender, 'address': address,
                        'medical_history': '', 'user_type': 'patient',
                        'profile_created': True, 'profile_pic': base64_photo,
                    }
                    save_json(USERS_FILE, users)
                    add_audit('Account Created', st.session_state.signup_email, 'Patient profile created')
                    ok, msg = login_user(st.session_state.signup_email, st.session_state.signup_password)
                    if ok: st.rerun()
                    else:  st.error(msg)

            # ── DOCTOR ───────────────────────────────────────────────────
            else:
                phone          = st.text_input(' Phone', value=st.session_state.signup_phone,
                                               key='doc_signup_phone')
                specialization = st.text_input(' Specialization', placeholder='e.g. Endocrinology',
                                               key='doc_signup_spec')
                hospital       = st.text_input(' Hospital / Clinic', placeholder='e.g. City Hospital',
                                               key='doc_signup_hospital')
                license_no     = st.text_input(' Medical License No.', placeholder='e.g. MCI-12345',
                                               key='doc_signup_license')
                uploaded_photo = st.file_uploader(' Upload Profile Photo (Optional)',
                                                  type=['png','jpg','jpeg'], key='doctor_photo')

                # Approval notice
                st.markdown(f'''
<div style="background:{'rgba(244,114,182,0.08)' if DARK else '#FFF5F7'};
            border:1px solid {'rgba(244,114,182,0.25)' if DARK else '#FBCFE8'};
            border-radius:12px;padding:11px 15px;margin:6px 0 14px;">
    <span style="font-size:13px;color:{MUTED};">
        ℹ️ &nbsp;Doctor accounts require <b style="color:{TEXT};">admin approval</b>
        before sign-in. Ensure your licence and hospital details are correct.
    </span>
</div>
''', unsafe_allow_html=True)

                if st.button('✅ Create Doctor Profile', type='primary', use_container_width=True):
                    if not name.strip():
                        st.error('⚠️ Please enter your full name.')
                    elif not specialization.strip():
                        st.error('⚠️ Specialization is required.')
                    elif not hospital.strip():
                        st.error('⚠️ Hospital / Clinic name is required.')
                    elif not license_no.strip():
                        st.error('⚠️ Medical licence number is required.')
                    else:
                        base64_photo = None
                        if uploaded_photo:
                            base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                        doctors[st.session_state.signup_email] = {
                            'password': st.session_state.signup_password, 'name': name,
                            'phone': phone, 'specialization': specialization,
                            'hospital': hospital, 'license_no': license_no,
                            'approved': False, 'user_type': 'doctor',
                            'profile_created': True, 'profile_pic': base64_photo,
                        }
                        save_json(DOCTORS_FILE, doctors)
                        add_audit('Doctor Signup', st.session_state.signup_email, 'Waiting for approval')
                        st.session_state.doctor_signup_done = True  # ← show confirmation screen
                        st.rerun()

def prediction_page():
    st.markdown(f'''<style>.stApp{{background:{'linear-gradient(135deg,#071520 0%,#0D2B3E 45%,#091A2E 100%)' if DARK else 'linear-gradient(135deg,#A5B4FC 0%,#BAC8FF 45%,#DDD6FE 100%)'}!important;}}</style>''', unsafe_allow_html=True)
    page_header('🩺', 'Diabetes Risk Prediction', 'Enter your clinical parameters for an AI-powered assessment')

    # Pure st.markdown info box — no components.html iframe
    st.markdown(f'''
<div style="background:linear-gradient(135deg,{GRAD1}18,{GRAD2}12);border:1px solid {GRAD1}44;
            border-radius:18px;padding:18px 24px;margin-bottom:18px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <span style="font-size:20px;">🔬</span>
        <span style="font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:{TEXT};">About This Assessment</span>
    </div>
    <p style="color:{MUTED};font-size:14px;margin:0;line-height:1.6;">
        Fill in your latest clinical values below. Our ML model analyzes these 8 parameters to calculate your diabetes risk level.
        All values should come from a recent lab test or medical report for best accuracy.
    </p>
</div>
''', unsafe_allow_html=True)

    # ── Doctor: two-step flow ──────────────────────────────────────────────────
    if st.session_state.user_type == 'doctor':
        if 'doctor_patient_step' not in st.session_state:
            st.session_state.doctor_patient_step = 1

        if st.session_state.doctor_patient_step == 1:
            st.markdown(f'''
<div style="background:linear-gradient(135deg,{GRAD1}18,{GRAD2}12);border:1px solid {GRAD1}44;
            border-radius:18px;padding:18px 24px;margin-bottom:18px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <span style="font-size:20px;">👤</span>
        <span style="font-family:Sora,sans-serif;font-weight:800;font-size:16px;color:{TEXT};">Step 1 — Patient Details</span>
    </div>
    <p style="color:{MUTED};font-size:14px;margin:0;line-height:1.6;">
        Fill in the patient's personal information before proceeding to clinical assessment.
    </p>
</div>''', unsafe_allow_html=True)
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    doc_patient_name    = st.text_input(' Patient Full Name *', placeholder='e.g. Ramesh Kumar',         key='doc_patient_name',    value=st.session_state.get('doc_patient_name',''))
                    doc_patient_age     = st.number_input('Age *', 1, 120, int(st.session_state.get('doc_patient_age_val', 30)), key='doc_patient_age_num')
                    doc_patient_gender  = st.selectbox(' Gender *', ['Male','Female','Other'],
                                                        index=['Male','Female','Other'].index(st.session_state.get('doc_patient_gender_val','Male')),
                                                        key='doc_patient_gender_sel')
                with c2:
                    doc_patient_email   = st.text_input(' Email *', placeholder='patient@example.com',                  key='doc_patient_email',   value=st.session_state.get('doc_patient_email',''))
                    doc_patient_phone   = st.text_input(' Contact Number *', placeholder='+91 98765 43210',             key='doc_patient_phone',   value=st.session_state.get('doc_patient_phone',''))
                    doc_patient_address = st.text_input(' Address', placeholder='123, Main St, City',                   key='doc_patient_address', value=st.session_state.get('doc_patient_address',''))

            if st.button('Proceed to Clinical Assessment →', type='primary', use_container_width=True):
                p_name  = st.session_state.get('doc_patient_name','').strip()
                p_email = st.session_state.get('doc_patient_email','').strip().lower()
                p_phone = st.session_state.get('doc_patient_phone','').strip()
                if not p_name or not p_email or not p_phone:
                    st.error('⚠️ Patient name, email and contact number are required.')
                    st.stop()
                # persist all values before rerun (widget keys reset after rerun)
                st.session_state.doc_patient_age_val     = doc_patient_age
                st.session_state.doc_patient_gender_val  = doc_patient_gender
                st.session_state.doc_patient_address_val = doc_patient_address
                st.session_state.doc_patient_phone_val   = p_phone
                st.session_state.doc_patient_name_val    = p_name
                st.session_state.doc_patient_email_val   = p_email
                st.session_state.doctor_patient_step = 2
                st.rerun()
            return   # don't show clinical form until step 1 is complete

        # Step 2 header — show patient summary
        p_name    = st.session_state.get('doc_patient_name_val', st.session_state.get('doc_patient_name','')).strip()
        p_email   = st.session_state.get('doc_patient_email_val', st.session_state.get('doc_patient_email','')).strip().lower()
        p_phone   = st.session_state.get('doc_patient_phone_val', st.session_state.get('doc_patient_phone','')).strip()
        p_age     = st.session_state.get('doc_patient_age_val', 30)
        p_gender  = st.session_state.get('doc_patient_gender_val', 'Male')
        p_address = st.session_state.get('doc_patient_address_val', '')

        st.markdown(f'''
<div style="background:linear-gradient(135deg,{GRAD1}18,{GRAD2}12);border:1px solid {GRAD1}44;
            border-radius:18px;padding:16px 24px;margin-bottom:18px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
    <span style="font-size:20px;">👤</span>
    <div>
        <span style="font-family:Sora,sans-serif;font-weight:800;font-size:15px;color:{TEXT};">Step 2 — Clinical Assessment for: {p_name}</span><br>
        <span style="font-size:13px;color:{MUTED};">📧 {p_email} &nbsp;·&nbsp; 📞 {p_phone} &nbsp;·&nbsp; 🎂 {p_age} yrs &nbsp;·&nbsp; ⚧ {p_gender}</span>
    </div>
    <div style="margin-left:auto;">
        <button onclick="window.location.reload()" style="background:none;border:1px solid {GRAD1}55;border-radius:8px;padding:6px 14px;cursor:pointer;font-size:12px;color:{MUTED};">← Change Patient</button>
    </div>
</div>''', unsafe_allow_html=True)
        if st.button('← Change Patient Details', key='change_patient_btn', type='secondary'):
            st.session_state.doctor_patient_step = 1; st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-heading"><div class="badge-num">1</div>Clinical Health Parameters</div>', unsafe_allow_html=True)
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown(f'<p style="color:{MUTED};font-size:13px;margin-bottom:12px;"> Metabolic Indicators</p>', unsafe_allow_html=True)
            preg = st.number_input(' Pregnancies', 0, 20, 1, help='Number of times pregnant')
            glucose = st.number_input(' Glucose (mg/dL)', 50, 250, 120, help='Plasma glucose concentration (2hr OGTT)')
            insulin = st.number_input(' Insulin (μU/mL)', 0, 400, 100, help='2-Hour serum insulin. Normal: 16-166 μU/mL')
            dpf = st.number_input(' Diabetes Pedigree', 0.0, 3.0, 0.5, help='Diabetes pedigree function — family history score')
        with c_right:
            st.markdown(f'<p style="color:{MUTED};font-size:13px;margin-bottom:12px;"> Physical Indicators</p>', unsafe_allow_html=True)
            bp = st.number_input(' Blood Pressure (mmHg)', 30, 140, 70, help='Diastolic blood pressure. Normal: 60-80 mmHg')
            skin = st.number_input(' Skin Thickness (mm)', 0, 100, 20, help='Triceps skin fold thickness')
            bmi = st.number_input(' BMI', 10.0, 70.0, 25.0, help='Body Mass Index. Normal: 18.5-24.9')
            default_age = int(users.get(st.session_state.current_user_email, {}).get('age', 30)) if st.session_state.user_type == 'patient' else 35
            age = st.number_input(' Age (years)', 1, 100, default_age)

    # Pure st.markdown reference cards — no components.html
    st.markdown(f'''
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px;margin-bottom:8px;">
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:18px;margin-bottom:4px;">🩸</div>
        <div style="font-size:11px;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Glucose</div>
        <div style="font-size:12px;color:{TEXT};font-weight:700;margin-top:2px;">Normal &lt;140</div>
    </div>
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:18px;margin-bottom:4px;">⚖️</div>
        <div style="font-size:11px;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">BMI</div>
        <div style="font-size:12px;color:{TEXT};font-weight:700;margin-top:2px;">Normal 18.5–24.9</div>
    </div>
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:18px;margin-bottom:4px;">💓</div>
        <div style="font-size:11px;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Blood Pressure</div>
        <div style="font-size:12px;color:{TEXT};font-weight:700;margin-top:2px;">Normal 60–80</div>
    </div>
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:18px;margin-bottom:4px;">💉</div>
        <div style="font-size:11px;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Insulin</div>
        <div style="font-size:12px;color:{TEXT};font-weight:700;margin-top:2px;">Normal 16–166</div>
    </div>
</div>
''', unsafe_allow_html=True)

    st.write('')
    btn_label = '🔍 Predict Patient Diabetes Risk →' if st.session_state.user_type == 'doctor' else '🔍 Predict My Diabetes Risk →'
    if st.button(btn_label, type='primary', use_container_width=True):
        if st.session_state.user_type == 'doctor':
            name  = st.session_state.get('doc_patient_name_val', st.session_state.get('doc_patient_name','')).strip()
            email = st.session_state.get('doc_patient_email_val', st.session_state.get('doc_patient_email','')).strip().lower()
        else:
            name  = st.session_state.current_user_name
            email = st.session_state.current_user_email

        patient_data = {'Pregnancies': preg, 'Glucose': glucose, 'BloodPressure': bp, 'SkinThickness': skin, 'Insulin': insulin, 'BMI': bmi, 'DiabetesPedigreeFunction': dpf, 'Age': age}
        result, confidence = model_predict(patient_data)
        pred_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

        # Build extra info dict for PDF
        if st.session_state.user_type == 'doctor':
            extra_info = {
                'phone':        st.session_state.get('doc_patient_phone_val', st.session_state.get('doc_patient_phone','')),
                'gender':       st.session_state.get('doc_patient_gender_val',''),
                'age':          st.session_state.get('doc_patient_age_val', age),
                'address':      st.session_state.get('doc_patient_address_val',''),
                'doctor_name':  st.session_state.current_user_name,
                'doctor_email': st.session_state.current_user_email,
            }
        else:
            u = users.get(st.session_state.current_user_email, {})
            extra_info = {
                'phone':   u.get('phone',''),
                'gender':  u.get('gender',''),
                'age':     u.get('age', age),
                'address': u.get('address',''),
            }

        pdf = generate_pdf(patient_data, result, confidence, name, email, pred_time, extra=extra_info)
        st.session_state.patient_data = patient_data; st.session_state.prediction_result = result
        st.session_state.confidence = confidence; st.session_state.prediction_time = pred_time
        st.session_state.pdf_bytes = pdf; st.session_state.prediction_done = True
        st.session_state.current_prediction_patient_name = name
        report_entry = {
            'name': name, 'email': email, 'result': result, 'confidence': confidence,
            'time': pred_time, 'data': patient_data, 'extra': extra_info,
        }
        if st.session_state.user_type == 'doctor':
            report_entry['doctor_email'] = st.session_state.current_user_email
            report_entry['doctor_name']  = st.session_state.current_user_name
        reports.append(report_entry)
        save_json(REPORTS_FILE, reports); add_audit('Prediction', email, result)
        # Reset doctor step for next patient
        if st.session_state.user_type == 'doctor':
            st.session_state.doctor_patient_step = 1
        st.session_state.page = 'dashboard'; st.rerun()


def _render_whatsapp_share(phone_key, pdf_bytes, patient_name, result, confidence, pred_time, patient_data, selected_idx=None):
    """WhatsApp share — header via st.markdown (no iframe), JS button via components.html."""
    import base64 as _b64

    # Header: pure st.markdown — zero overlap risk
    st.markdown(f'''
<div class="wa-share-box">
    <div class="wa-share-title">
        <span style="font-size:22px;">📱</span>
        <span class="wa-share-title-text">Share PDF Report via WhatsApp</span>
    </div>
    <p class="wa-share-desc">
        Opens your device share sheet — select WhatsApp to send the PDF file directly.
        Works on mobile &amp; supported desktop browsers.
    </p>
</div>
''', unsafe_allow_html=True)

    caption = (
        f"GlucoTrack Diabetes Risk Report\n"
        f"Patient: {patient_name}\nResult: {result}\nConfidence: {confidence}%\n"
        f"Date: {pred_time}\nGlucose: {patient_data.get('Glucose','N/A')} mg/dL\n"
        f"BMI: {patient_data.get('BMI','N/A')}\nBP: {patient_data.get('BloodPressure','N/A')} mmHg"
    )
    safe_caption = caption.replace("`", "'").replace("\\", "\\\\")
    file_name = f"GlucoTrack_{patient_name.replace(' ', '_')}_Report.pdf"
    pdf_b64 = _b64.b64encode(pdf_bytes).decode("utf-8")

    col_share, col_dl = st.columns([3, 2])
    with col_share:
        # Only the interactive JS button uses components.html
        components.html(f"""
<div>
  <button id="sharePdfBtn_{phone_key}" style="
      width:100%;background:linear-gradient(135deg,#16A34A 0%,#22C55E 100%);
      color:white;border:none;padding:14px 20px;border-radius:14px;cursor:pointer;
      font-weight:700;font-size:15px;font-family:'DM Sans',Arial,sans-serif;
      box-shadow:0 8px 20px rgba(34,197,94,0.30);
      display:flex;align-items:center;justify-content:center;gap:8px;transition:all 0.2s ease;">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="white" viewBox="0 0 16 16">
      <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.93c0 1.39.365 2.743 1.06 3.962L0 16l4.13-1.082A7.86 7.86 0 0 0 7.99 12c4.365 0 7.934-3.558 7.939-7.93a7.86 7.86 0 0 0-2.328-5.744M7.993 11.89c-1.392 0-2.702-.38-3.829-1.08l-.275-.164-2.429.637.649-2.368-.18-.287a5.95 5.95 0 0 1-.98-3.216c.004-3.279 2.685-5.96 5.966-5.96 1.587.001 3.079.616 4.2 1.738a5.96 5.96 0 0 1 1.729 4.2c-.004 3.28-2.685 5.96-5.966 5.96M11.53 8.87c-.191-.096-1.136-.56-1.31-.624-.173-.064-.3-.096-.426.096-.127.192-.49.61-.6.732-.11.123-.219.138-.41.042-.191-.096-.807-.297-1.537-.95-.568-.506-.95-1.133-1.062-1.324-.112-.19-.012-.294.084-.389.087-.085.191-.223.287-.335.095-.112.127-.19.19-.32.064-.13.032-.243-.016-.339-.048-.096-.426-1.026-.583-1.407-.152-.37-.308-.32-.426-.326-.11-.006-.237-.008-.363-.008-.127 0-.332.048-.506.237-.174.19-.66 1.63-.66 3.97 0 2.34 1.7 4.595 1.94 4.914.24.318 3.352 5.12 8.12 7.18 1.133.49 2.02.784 2.709 1.004 1.134.36 2.167.309 2.984.187.912-.136 2.793-.113 3.197-1.197.404-1.084.404-2.013.283-2.203-.12-.19-.32-.304-.51-.399"/>
    </svg>
    &nbsp;Share PDF on WhatsApp
  </button>
  <p id="shareStatus_{phone_key}" style="font-family:Arial,sans-serif;font-size:12px;color:#64748B;margin:8px 0 0;min-height:16px;"></p>
</div>
<script>
(function() {{
  var btn = document.getElementById('sharePdfBtn_{phone_key}');
  var status = document.getElementById('shareStatus_{phone_key}');
  btn.onmouseenter = function() {{ btn.style.transform='translateY(-2px)'; }};
  btn.onmouseleave = function() {{ btn.style.transform='translateY(0)'; }};
  btn.onclick = async function() {{
    try {{
      var b64 = "{pdf_b64}";
      var binary = atob(b64);
      var bytes = new Uint8Array(binary.length);
      for (var i = 0; i < binary.length; i++) {{ bytes[i] = binary.charCodeAt(i); }}
      var file = new File([bytes], "{file_name}", {{ type: "application/pdf" }});
      if (navigator.canShare && navigator.canShare({{ files: [file] }})) {{
        await navigator.share({{ title: "GlucoTrack Diabetes Report", text: `{safe_caption}`, files: [file] }});
        status.style.color = "#16A34A";
        status.innerText = "Share panel opened — select WhatsApp to send the PDF.";
      }} else {{
        status.style.color = "#F97316";
        status.innerText = "Your browser does not support file sharing. Please download the PDF and send manually.";
      }}
    }} catch(err) {{
      if (err.name !== "AbortError") {{
        status.style.color = "#EF4444";
        status.innerText = "Sharing cancelled or not supported. Download the PDF and attach it in WhatsApp.";
      }}
    }}
  }};
}})();
</script>
""", height=100)

    with col_dl:
        st.download_button("📥 Download PDF", data=pdf_bytes, file_name=file_name, mime="application/pdf", use_container_width=True, key=f"wa_dl_{phone_key}")

    st.caption("ℹ️ Works best on mobile Chrome/Safari. On desktop, download and attach in WhatsApp Web manually.")


def dashboard_page():
    st.markdown(f'''<style>.stApp{{background:{'linear-gradient(135deg,#071520 0%,#0D2B3E 45%,#091A2E 100%)' if DARK else 'linear-gradient(135deg,#A5B4FC 0%,#BAC8FF 45%,#DDD6FE 100%)'}!important;}}</style>''', unsafe_allow_html=True)
    page_header('📊', 'Health Dashboard', 'Your prediction result, analytics, and personalized recommendations')

    if not st.session_state.prediction_done:
        st.warning('⚠️ No prediction found. Please complete a prediction first.')
        if st.button('🩺 Go to Prediction', type='primary'): st.session_state.page = 'prediction'; st.rerun()
        return

    result = st.session_state.prediction_result
    confidence = st.session_state.confidence
    patient_data = st.session_state.patient_data
    is_high = 'High' in result

    st.markdown(f'<div class="{"result-high" if is_high else "result-low"}">{"⚠️" if is_high else "✅"} {result}<br><span style="font-size:16px;font-weight:600;opacity:0.85;">Model Confidence: {confidence}%</span></div>', unsafe_allow_html=True)

    st.write('')
    st.subheader('🧾 Submitted Health Parameters')
    params = list(patient_data.items())
    cols = st.columns(4)
    for i, (k, v) in enumerate(params):
        with cols[i % 4]:
            st.markdown(f'<div class="param-card"><span class="param-label">{nice_label(k)}</span><span class="param-value">{v}</span></div>', unsafe_allow_html=True)

    st.write('')
    st.subheader('📈 Health Analytics')
    metrics = ['Glucose', 'BMI', 'Insulin', 'BloodPressure', 'Age']
    values = [patient_data[m] for m in metrics]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=metrics, y=values, marker=dict(color=[GRAD1, TEAL, INDIGO, '#F97316', '#F43F5E'], line=dict(width=0)), text=values, textposition='outside'))
    fig.update_layout(template=PLOT_TEMPLATE, height=360, title='Health Parameter Overview', font=dict(family='DM Sans'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    suggestions = get_suggestions(patient_data)
    suggestion_rows = ''.join([
        f'<div style="display:flex;align-items:flex-start;gap:14px;padding:14px 0;border-bottom:1px solid {BORDER};">'
        f'<div style="min-width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,{GRAD1},{GRAD2});color:white;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;flex-shrink:0;">{i}</div>'
        f'<div style="font-size:15px;line-height:1.65;color:{BOX_SUGGESTION_TEXT};font-weight:600;padding-top:4px;">{s}</div></div>'
        for i, s in enumerate(suggestions, 1)
    ])
    st.markdown(f'''
<div style="background:{BOX_SUGGESTION_BG};padding:24px 28px;border-radius:20px;border:1px solid {BORDER};margin-top:8px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <span style="font-size:22px;">💡</span>
        <h3 style="font-family:Sora,sans-serif;font-size:18px;font-weight:800;margin:0;color:{BOX_SUGGESTION_TITLE};">Personalized Health Suggestions</h3>
    </div>
    <p style="color:{MUTED};font-size:13px;margin:0 0 12px 32px;">Based on your clinical values</p>
    {suggestion_rows}
</div>
''', unsafe_allow_html=True)

    st.write('')
    # For doctors, use the patient name stored at prediction time; for patients use their own name
    display_name = st.session_state.get('current_prediction_patient_name') or st.session_state.current_user_name
    _render_whatsapp_share(
        phone_key='patient_dash', pdf_bytes=st.session_state.pdf_bytes,
        patient_name=display_name, result=result, confidence=confidence,
        pred_time=st.session_state.prediction_time, patient_data=patient_data
    )
    st.write('')
    if st.button('🔄 New Prediction', type='secondary', use_container_width=True):
        reset_prediction_state(); st.session_state.page = 'prediction'; st.rerun()


def doctor_page():
    st.markdown(f'''<style>.stApp{{background:{'linear-gradient(135deg,#071E14 0%,#0A2E1E 45%,#06180F 100%)' if DARK else 'linear-gradient(135deg,#A5B4FC 0%,#C4B5FD 45%,#DDD6FE 100%)'}!important;}}</style>''', unsafe_allow_html=True)
    page_header('👨‍⚕️', 'Doctor Portal', 'Your Patient Directory & Clinical Health Analytics')
    doctor_email = st.session_state.current_user_email
    # Only show reports that this doctor created
    my_reports = [r for r in reports if r.get('doctor_email') == doctor_email]
    high_cases = [r for r in my_reports if 'High' in r.get('result', '')]
    # Unique patient emails seen by this doctor
    my_patient_emails = list({r.get('email') for r in my_reports})
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric('📋 My Assessments', len(my_reports))
        c2.metric('⚠️ High Risk Patients', len(high_cases))
        c3.metric('🧑 My Patients', len(my_patient_emails))

    if not my_reports:
        st.info('📭 You have no patient reports yet. Use the 🩺 Predict Risk page to assess a patient.')
        return

    st.write('')
    tab_dir, tab_detail = st.tabs(['📋 Patient Reports Directory', '🔍 Detailed Patient Analysis'])
    with tab_dir:
        st.subheader('My Patient Reports')
        if not my_reports: st.info(' No patient reports available yet.')
        else:
            report_data = []
            for idx, r in enumerate(my_reports):
                data_dict = r.get('data', {})
                report_data.append({'ID': idx, 'Patient Name': r.get('name'), 'Email': r.get('email'), 'Risk Level': r.get('result'), 'Confidence': f"{r.get('confidence')}%", 'Assessment Time': r.get('time'), 'Glucose': data_dict.get('Glucose', 'N/A'), 'BMI': data_dict.get('BMI', 'N/A'), 'BP': data_dict.get('BloodPressure', 'N/A'), 'Age': data_dict.get('Age', 'N/A')})
            st.dataframe(pd.DataFrame(report_data).drop(columns=['ID']), use_container_width=True)

    with tab_detail:
        if not my_reports: st.info(' No patient reports available.')
        else:
            report_options = [f"{r.get('name')} ({r.get('time')}) — {r.get('result')}" for r in my_reports]
            selected_idx = st.selectbox('🔍 Select Patient Report:', range(len(my_reports)), format_func=lambda x: report_options[x])
            selected_report = my_reports[selected_idx]
            patient_data = selected_report.get('data', {})
            result = selected_report.get('result'); confidence = selected_report.get('confidence')
            pred_time = selected_report.get('time'); name = selected_report.get('name'); email = selected_report.get('email')
            patient_info = users.get(email, {}); phone = patient_info.get('phone', 'Not Provided')
            age = patient_info.get('age', patient_data.get('Age', 'N/A')); gender = patient_info.get('gender', 'Not Provided')
            is_high_d = 'High' in result

            saved_extra = selected_report.get('extra', {})
            s_phone   = saved_extra.get('phone',   phone)
            s_gender  = saved_extra.get('gender',  gender)
            s_age     = saved_extra.get('age',     age)
            s_address = saved_extra.get('address', 'N/A')
            s_doc_name  = saved_extra.get('doctor_name',  doctors.get(doctor_email,{}).get('name',''))
            s_doc_email = saved_extra.get('doctor_email', doctor_email)

            st.markdown(f'''
<div style="background:{CARD};border:1px solid {BORDER};padding:24px;border-radius:20px;margin-bottom:20px;">
    <h3 style="margin-top:0;font-family:Sora,sans-serif;color:{TEXT};"> Patient Profile: {name}</h3>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:14px;font-size:14px;color:{TEXT};">
        <div><b> Email:</b><br>{email}</div>
        <div><b> Phone:</b><br>{s_phone or 'N/A'}</div>
        <div><b> Age:</b><br>{s_age}</div>
        <div><b> Gender:</b><br>{s_gender or 'N/A'}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:14px;font-size:14px;color:{TEXT};">
        <div><b> Address:</b><br>{s_address}</div>
        <div><b> Assessed By:</b><br>Dr. {s_doc_name} &nbsp;·&nbsp; {s_doc_email}</div>
    </div>
    <div class="{"result-high" if is_high_d else "result-low"}" style="padding:14px;">
        {"⚠️" if is_high_d else "✅"} <b>Assessment:</b> {result} &nbsp;·&nbsp; {confidence}% Confidence
    </div>
</div>
''', unsafe_allow_html=True)

            st.subheader('📋 Clinical Health Parameters')
            param_labels = {'Pregnancies': ' Pregnancies', 'Glucose': ' Glucose (mg/dL)', 'BloodPressure': ' Blood Pressure (mmHg)', 'SkinThickness': ' Skin Thickness (mm)', 'Insulin': ' Insulin (μU/mL)', 'BMI': ' BMI (kg/m²)', 'DiabetesPedigreeFunction': ' Diabetes Pedigree', 'Age': ' Age (years)'}
            cols = st.columns(4)
            for i, (key, label) in enumerate(param_labels.items()):
                with cols[i % 4]:
                    st.markdown(f'<div class="param-card"><span class="param-label">{label}</span><span class="param-value">{patient_data.get(key, "N/A")}</span></div>', unsafe_allow_html=True)

            st.write('')
            c_left, c_right = st.columns([3, 2])
            with c_left:
                st.subheader('📈 Health Analytics')
                metrics_list = ['Glucose', 'BMI', 'Insulin', 'BloodPressure', 'Age']
                values_list = [patient_data.get(m, 0) for m in metrics_list]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=metrics_list, y=values_list, marker=dict(color=[GRAD1, TEAL, INDIGO, '#F97316', '#F43F5E'], line=dict(width=0)), text=values_list, textposition='outside'))
                fig.update_layout(template=PLOT_TEMPLATE, height=320, title='Key Metrics', font=dict(family='DM Sans'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            with c_right:
                st.subheader('💡 Clinical Suggestions')
                suggestions = get_suggestions(patient_data)
                doc_rows = ''.join([
                    f'<div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};">'
                    f'<div style="min-width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,{GRAD1},{GRAD2});color:white;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;flex-shrink:0;">{i2}</div>'
                    f'<div style="font-size:14px;line-height:1.6;color:{BOX_SUGGESTION_TEXT};font-weight:600;padding-top:2px;">{sug}</div></div>'
                    for i2, sug in enumerate(suggestions, 1)
                ])
                st.markdown(f'<div style="background:{BOX_SUGGESTION_BG};padding:18px 20px;border-radius:16px;border:1px solid {BORDER};margin-top:4px;"><h4 style="font-family:Sora,sans-serif;font-size:16px;font-weight:800;margin:0 0 12px;color:{BOX_SUGGESTION_TITLE};">💡 Recommendations</h4>{doc_rows}</div>', unsafe_allow_html=True)

            st.write('')
            saved_extra = selected_report.get('extra', {})
            if not saved_extra.get('doctor_name'):
                saved_extra['doctor_name']  = selected_report.get('doctor_name', doctors.get(doctor_email,{}).get('name',''))
                saved_extra['doctor_email'] = doctor_email
            pdf_data = generate_pdf(patient_data, result, confidence, name, email, pred_time, extra=saved_extra)
            _render_whatsapp_share(phone_key=f'doctor_{selected_idx}', pdf_bytes=pdf_data, patient_name=name, result=result, confidence=confidence, pred_time=pred_time, patient_data=patient_data, selected_idx=selected_idx)


def admin_page():
    st.markdown(f'''<style>.stApp{{background:{'linear-gradient(135deg,#1A0808 0%,#2D0D0D 45%,#1A0A1A 100%)' if DARK else 'linear-gradient(135deg,#A5B4FC 0%,#C4B5FD 40%,#DDD6FE 100%)'}!important;}}</style>''', unsafe_allow_html=True)
    page_header('🛡️', 'Admin Panel', 'Manage doctors, users, reports, and audit logs')
    pending = {email: d for email, d in doctors.items() if not d.get('approved', False)}
    high = [r for r in reports if 'High' in r.get('result', '')]
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('🧑 Patients', len(users)); c2.metric('👨‍⚕️ Doctors', len(doctors))
        c3.metric('⏳ Pending', len(pending)); c4.metric('⚠️ High Risk', len(high))
    st.write('')
    st.subheader('⏳ Doctor Approval Requests')
    if not pending: st.success('✅ No pending doctor approvals.')
    else:
        for email, d in pending.items():
            with st.container(border=True):
                st.write(f"**👤 Name:** {d.get('name')} &nbsp;|&nbsp; **📧 Email:** {email}")
                st.write(f"🔬 {d.get('specialization')} &nbsp;·&nbsp; 🏥 {d.get('hospital')} &nbsp;·&nbsp; 📋 {d.get('license_no')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f'✅ Approve {email}', key=f'approve_{email}', type='primary', use_container_width=True):
                        doctors[email]['approved'] = True; save_json(DOCTORS_FILE, doctors)
                        add_audit('Doctor Approved', st.session_state.current_user_email, email); st.rerun()
                with col2:
                    if st.button(f'❌ Reject {email}', key=f'reject_{email}', type='secondary', use_container_width=True):
                        doctors.pop(email); save_json(DOCTORS_FILE, doctors)
                        add_audit('Doctor Rejected', st.session_state.current_user_email, email); st.rerun()
    st.write(''); st.subheader('🧑 Registered Patients')
    st.dataframe(pd.DataFrame([{'Name': v.get('name'), 'Email': k, 'Age': v.get('age'), 'Gender': v.get('gender')} for k, v in users.items()]), use_container_width=True)
    st.write(''); st.subheader('👨‍⚕️ Registered Doctors')
    st.dataframe(pd.DataFrame([{'Name': v.get('name'), 'Email': k, 'Approved': v.get('approved'), 'Specialization': v.get('specialization')} for k, v in doctors.items()]), use_container_width=True)
    st.write(''); st.subheader('📋 Audit Log')
    logs = load_json(AUDIT_FILE, [])
    if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else: st.info('📭 No audit logs yet.')


def profile_page():
    back_page = 'prediction' if st.session_state.user_type in ('patient', 'doctor') else 'admin'
    if st.button('← Back', key='profile_back', type='secondary'): st.session_state.page = back_page; st.rerun()
    page_header('👤', 'My Profile', 'Update your personal details and photo')
    email = st.session_state.current_user_email; utype = st.session_state.user_type
    with st.container(border=True):
        if utype == 'patient':
            user = users[email]
            name = st.text_input(' Name', value=user.get('name', ''))
            phone = st.text_input(' Phone', value=user.get('phone', ''))
            age = st.number_input(' Age', 1, 100, int(user.get('age', 25)))
            gender = st.selectbox(' Gender', ['Female', 'Male', 'Other'], index=['Female', 'Male', 'Other'].index(user.get('gender', 'Female')) if user.get('gender') in ['Female', 'Male', 'Other'] else 0)
            address = st.text_area(' Address', value=user.get('address', ''))
            uploaded_photo = st.file_uploader(' Change Profile Photo', type=['png', 'jpg', 'jpeg'], key='edit_patient_photo')
            if st.button(' Save Profile', type='primary', use_container_width=True):
                update_data = {'name': name, 'phone': phone, 'age': age, 'gender': gender, 'address': address}
                if uploaded_photo: update_data['profile_pic'] = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                users[email].update(update_data); save_json(USERS_FILE, users)
                st.session_state.current_user_name = name
                add_audit('Profile Updated', email, 'Patient profile updated'); st.success('✅ Profile updated!'); st.rerun()
        elif utype == 'doctor':
            doctor = doctors[email]
            name = st.text_input(' Name', value=doctor.get('name', ''))
            phone = st.text_input(' Phone', value=doctor.get('phone', ''))
            specialization = st.text_input('🔬 Specialization', value=doctor.get('specialization', ''))
            hospital = st.text_input(' Hospital', value=doctor.get('hospital', ''))
            license_no = st.text_input(' License No.', value=doctor.get('license_no', ''))
            uploaded_photo = st.file_uploader(' Change Profile Photo', type=['png', 'jpg', 'jpeg'], key='edit_doctor_photo')
            if st.button(' Save Profile', type='primary', use_container_width=True):
                update_data = {'name': name, 'phone': phone, 'specialization': specialization, 'hospital': hospital, 'license_no': license_no}
                if uploaded_photo: update_data['profile_pic'] = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                doctors[email].update(update_data); save_json(DOCTORS_FILE, doctors)
                st.session_state.current_user_name = name
                add_audit('Profile Updated', email, 'Doctor profile updated'); st.success('✅ Profile updated!'); st.rerun()
        else: st.info('ℹ️ Admin profile editing is not available.')


# ===== ROUTER =====
# Intercept ?forgot_password=1 BEFORE the `started` check.
# The href link causes a full reload which resets `started` to False;
# without this, the router hits landing_page() and stops before auth_page().
if st.query_params.get('forgot_password') == '1':
    st.query_params.clear()
    st.session_state.started   = True
    st.session_state.page      = 'auth'
    st.session_state.auth_mode = 'forgot_password'
    st.session_state.fp_step   = 1
    st.rerun()

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

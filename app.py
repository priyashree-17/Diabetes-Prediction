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

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt

# UPDATE 1: Change initial_sidebar_state to 'collapsed' to create a drawer style
st.set_page_config(page_title='GlucoTrack', page_icon='🩺', layout='wide', initial_sidebar_state='collapsed')

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
    BG = '#070B14'
    BG2 = '#0D1525'
    CARD = '#111827'
    CARD2 = '#1A2540'
    TEXT = '#F0F6FF'
    MUTED = '#8BA4C8'
    BORDER = '#1E3358'
    INPUT = '#0F1E35'
    GRAD1 = '#0EA5E9'
    GRAD2 = '#6366F1'
    GRAD3 = '#14B8A6'
    BLUE = '#0EA5E9'
    BLUE_DARK = '#0284C7'
    TEAL = '#14B8A6'
    INDIGO = '#6366F1'
    SIDEBAR = '#0B1120'
    PLOT_TEMPLATE = 'plotly_dark'
    RESULT_HIGH_BG = '#2D0A14'
    RESULT_HIGH_BORDER = '#F43F5E'
    RESULT_HIGH_TEXT = '#FDA4AF'
    RESULT_LOW_BG = '#031A1A'
    RESULT_LOW_BORDER = '#14B8A6'
    RESULT_LOW_TEXT = '#5EEAD4'
    BOX_SUGGESTION_BG = '#0F1E35'
    BOX_SUGGESTION_TITLE = '#F0F6FF'
    BOX_SUGGESTION_TEXT = '#5EEAD4'
    HERO_OVERLAY = 'rgba(7,11,20,0.85)'
else:
    BG = '#F0F7FF'
    BG2 = '#E8F2FF'
    CARD = '#FFFFFF'
    CARD2 = '#F8FBFF'
    TEXT = '#0A1628'
    MUTED = '#4A6589'
    BORDER = '#C8DCF0'
    INPUT = '#FFFFFF'
    GRAD1 = '#0EA5E9'
    GRAD2 = '#6366F1'
    GRAD3 = '#0D9488'
    BLUE = '#0369A1'
    BLUE_DARK = '#075985'
    TEAL = '#0D9488'
    INDIGO = '#4F46E5'
    SIDEBAR = '#FFFFFF'
    PLOT_TEMPLATE = 'plotly_white'
    RESULT_HIGH_BG = '#FFF1F2'
    RESULT_HIGH_BORDER = '#FB7185'
    RESULT_HIGH_TEXT = '#BE123C'
    RESULT_LOW_BG = '#F0FDFA'
    RESULT_LOW_BORDER = '#5EEAD4'
    RESULT_LOW_TEXT = '#0F766E'
    BOX_SUGGESTION_BG = '#ECFDF5'
    BOX_SUGGESTION_TITLE = '#0A1628'
    BOX_SUGGESTION_TEXT = '#0F766E'
    HERO_OVERLAY = 'rgba(240,247,255,0.92)'

GRAD_PRIMARY = f'linear-gradient(135deg, {GRAD1} 0%, {GRAD2} 100%)'
GRAD_CARD = f'linear-gradient(135deg, {GRAD1}18 0%, {GRAD2}18 100%)' if not DARK else f'linear-gradient(135deg, {GRAD1}22 0%, {GRAD2}22 100%)'
GRAD_HERO = f'linear-gradient(135deg, #0369A1 0%, #4F46E5 50%, #0D9488 100%)'

# UPDATE 2: Removed the hacky CSS that was breaking Streamlit and causing text to show
css = f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800;900&family=DM+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif !important; }}
.stApp {{ background: {BG} !important; }}
.block-container {{ padding-top: 1.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; max-width: 100% !important; }}
h1,h2,h3,h4,h5,h6 {{ font-family: 'Sora', sans-serif !important; color: {TEXT} !important; }}
p, label, span {{ font-family: 'DM Sans', sans-serif !important; color: {TEXT} !important; }}

/* Header cleanup */
[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; box-shadow: none !important; border: none !important; }}
header[data-testid="stHeader"] [data-testid="stAppDeployButton"] {{ display: none !important; }}
header[data-testid="stHeader"] #MainMenu {{ display: none !important; }}
header[data-testid="stHeader"] [data-testid="stConnectionStatus"] {{ display: none !important; }}

/* Nav links */
.nav-link {{ text-decoration: none !important; color: {TEXT} !important; font-weight: 600 !important; font-size: 15px !important; transition: all 0.2s ease !important; font-family: 'DM Sans', sans-serif !important; }}
.nav-link:hover {{ color: {GRAD1} !important; }}

/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: {INPUT} !important; color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important; border-radius: 14px !important;
    min-height: 52px !important; font-size: 15px !important; padding-left: 16px !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: border-color 0.2s ease !important;
}}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
    border-color: {GRAD1} !important;
    box-shadow: 0 0 0 3px {GRAD1}22 !important;
}}
.stSelectbox div[data-baseweb="select"]>div {{
    background: {INPUT} !important; color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important; border-radius: 14px !important; min-height: 52px !important;
}}

/* Card containers */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 22px !important;
    padding: 28px !important;
    box-shadow: 0 4px 24px rgba(14,165,233,0.06), 0 1px 4px rgba(0,0,0,0.04) !important;
}}

/* Primary buttons */
.stButton>button[kind="primary"], .stDownloadButton>button, .stFormSubmitButton>button {{
    background: {GRAD_PRIMARY} !important;
    color: white !important; border: none !important; border-radius: 14px !important;
    font-weight: 700 !important; font-size: 15px !important; min-height: 52px !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 8px 24px rgba(14,165,233,0.30) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.2px !important;
}}
.stButton>button[kind="primary"]:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 32px rgba(14,165,233,0.38) !important;
    filter: brightness(1.05) !important;
}}
.stButton>button[kind="secondary"] {{
    background: transparent !important; color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important; border-radius: 14px !important;
    font-weight: 600 !important; font-size: 15px !important; min-height: 52px !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.2s ease !important;
}}
.stButton>button[kind="secondary"]:hover {{
    background: {BORDER}44 !important; transform: translateY(-1px) !important;
}}
button * {{ color: white !important; }}
.stButton>button[kind="secondary"] * {{ color: {TEXT} !important; }}

/* Sidebar */
section[data-testid="stSidebar"] {{ background: {SIDEBAR} !important; border-right: 1px solid {BORDER}; }}
section[data-testid="stSidebar"]>div {{ background: transparent !important; padding-top: 0 !important; }}
section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
.sb-header {{ height: 80px; display: flex; align-items: center; gap: 12px; padding: 0 18px; border-bottom: 1px solid {BORDER}; }}
.sb-logo-box {{
    width: 42px; height: 42px;
    background: {GRAD_PRIMARY};
    color: white !important; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 20px;
    box-shadow: 0 4px 12px rgba(14,165,233,0.35);
}}
.sb-brand {{ font-size: 20px; font-weight: 800; color: {TEXT} !important; font-family: 'Sora', sans-serif !important; }}
.sb-profile {{ display: flex; align-items: center; gap: 14px; padding: 20px 18px; border-bottom: 1px solid {BORDER}; }}
.sb-avatar {{
    width: 48px; height: 48px; border-radius: 14px;
    background: {GRAD_PRIMARY};
    color: white !important; display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 17px; font-family: 'Sora', sans-serif !important;
}}
.sb-name {{ font-size: 15px; font-weight: 700; color: {TEXT} !important; margin-bottom: 3px; font-family: 'Sora', sans-serif !important; }}
.sb-role {{ font-size: 13px; color: {MUTED} !important; font-weight: 500; }}
div[data-testid="stRadio"] {{ padding: 18px 7px 0 !important; }}
div[data-testid="stRadio"] label {{
    border-radius: 12px !important; padding: 13px 14px !important; margin: 3px 0 !important;
    font-size: 15px !important; font-weight: 600 !important; background: transparent !important;
    transition: all 0.15s ease !important;
}}
div[data-testid="stRadio"] label:hover {{ background: {GRAD1}12 !important; }}
div[data-testid="stRadio"] label[data-baseweb="radio"]>div:first-child {{ display: none !important; }}

/* HERO */
.hero-section {{
    position: relative;
    min-height: 92vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 60px 20px 40px;
    overflow: hidden;
}}
.hero-bg {{
    position: absolute; inset: 0; z-index: 0;
    background: {GRAD_HERO};
    opacity: {'0.12' if not DARK else '0.18'};
    border-radius: 0 0 60px 60px;
}}
.hero-glow {{
    position: absolute; width: 700px; height: 700px;
    border-radius: 50%;
    background: radial-gradient(circle, {GRAD1}30 0%, transparent 70%);
    top: -200px; left: 50%; transform: translateX(-50%);
    pointer-events: none; z-index: 0;
}}
.hero-glow2 {{
    position: absolute; width: 500px; height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle, {GRAD2}20 0%, transparent 70%);
    bottom: -100px; right: -100px;
    pointer-events: none; z-index: 0;
}}
.hero-badge {{
    position: relative; z-index: 1;
    display: inline-flex; align-items: center; gap: 8px;
    background: {GRAD_PRIMARY};
    color: white !important;
    border-radius: 999px; padding: 8px 20px;
    font-weight: 700; font-size: 12px; letter-spacing: 2px;
    font-family: 'DM Sans', sans-serif;
    text-transform: uppercase;
    box-shadow: 0 4px 20px rgba(14,165,233,0.35);
    margin-bottom: 28px;
    animation: fadeInDown 0.6s ease both;
}}
.hero-title {{
    position: relative; z-index: 1;
    font-family: 'Sora', sans-serif;
    font-size: clamp(52px, 8vw, 96px);
    font-weight: 900;
    line-height: 0.95;
    letter-spacing: -3px;
    color: {TEXT} !important;
    margin: 0 0 24px;
    animation: fadeInUp 0.7s ease 0.1s both;
}}
.hero-gradient-text {{
    background: {GRAD_PRIMARY};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: block;
}}
.hero-sub {{
    position: relative; z-index: 1;
    font-size: clamp(17px, 2.2vw, 22px);
    line-height: 1.6;
    max-width: 680px;
    margin: 0 auto 44px;
    color: {MUTED} !important;
    font-weight: 400;
    animation: fadeInUp 0.7s ease 0.2s both;
}}

/* Stats bar */
.stats-wrap {{
    max-width: 900px; margin: 44px auto 80px;
    display: grid; grid-template-columns: repeat(3, 1fr);
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 24px; overflow: hidden;
    box-shadow: 0 8px 32px rgba(14,165,233,0.08);
}}
.stat {{ padding: 40px 20px; text-align: center; border-right: 1px solid {BORDER}; }}
.stat:last-child {{ border-right: none; }}
.stat-num {{
    font-family: 'Sora', sans-serif;
    font-size: 42px; font-weight: 900;
    background: {GRAD_PRIMARY};
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.stat-label {{ font-size: 16px; margin-top: 6px; color: {MUTED} !important; font-weight: 500; }}

/* Feature cards */
.section {{ padding: 0 20px 80px; }}
.section-title {{
    text-align: center; font-family: 'Sora', sans-serif;
    font-size: clamp(28px, 4vw, 42px); font-weight: 900;
    margin-bottom: 14px; color: {TEXT} !important;
}}
.section-sub {{ text-align: center; font-size: 19px; margin-bottom: 52px; color: {MUTED} !important; }}
.feature-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; max-width: 1200px; margin: 0 auto; }}
.feature-card {{
    border-radius: 24px; padding: 36px 32px; min-height: 380px;
    border: 1px solid {BORDER};
    position: relative; overflow: hidden;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}}
.feature-card:hover {{ transform: translateY(-6px); box-shadow: 0 20px 48px rgba(14,165,233,0.14); }}
.feature-card::before {{
    content: ''; position: absolute; inset: 0;
    opacity: 0.06; pointer-events: none;
    border-radius: inherit;
}}
.feature-blue {{ background: {'#0E1A2E' if DARK else '#EFF8FF'} !important; }}
.feature-blue::before {{ background: linear-gradient(135deg, {GRAD1}, transparent); }}
.feature-green {{ background: {'#081A18' if DARK else '#F0FDFA'} !important; }}
.feature-green::before {{ background: linear-gradient(135deg, {TEAL}, transparent); }}
.feature-purple {{ background: {'#120E2E' if DARK else '#F5F3FF'} !important; }}
.feature-purple::before {{ background: linear-gradient(135deg, {INDIGO}, transparent); }}
.pill {{
    display: inline-flex; border-radius: 999px; padding: 6px 16px;
    font-size: 11px; font-weight: 800; letter-spacing: 1.5px;
    margin-bottom: 28px; border: none;
    text-transform: uppercase; font-family: 'DM Sans', sans-serif;
}}
.pill-blue {{ background: {GRAD1}22 !important; color: {GRAD1} !important; }}
.pill-green {{ background: {TEAL}22 !important; color: {TEAL} !important; }}
.pill-purple {{ background: {INDIGO}22 !important; color: {INDIGO} !important; }}
.icon-box {{
    width: 56px; height: 56px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; margin-bottom: 20px;
}}
.icon-blue {{ background: {GRAD1}18 !important; }}
.icon-green {{ background: {TEAL}18 !important; }}
.icon-purple {{ background: {INDIGO}18 !important; }}
.feature-title {{ font-family: 'Sora', sans-serif; font-size: 20px; font-weight: 800; margin-bottom: 14px; color: {TEXT} !important; }}
.feature-text {{ font-size: 16px; line-height: 1.6; color: {MUTED} !important; }}

/* Steps */
.steps-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; max-width: 1200px; margin: 0 auto; }}
.step-card {{
    border: 1px solid {BORDER}; border-radius: 20px;
    padding: 32px 22px; text-align: center;
    background: {CARD} !important;
    position: relative; overflow: hidden;
    transition: transform 0.2s ease;
}}
.step-card:hover {{ transform: translateY(-4px); }}
.step-num {{
    font-family: 'Sora', sans-serif; font-size: 40px; font-weight: 900;
    background: {GRAD_PRIMARY};
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 12px;
}}
.step-title {{ font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 800; margin-bottom: 10px; color: {TEXT} !important; }}
.step-text {{ font-size: 15px; line-height: 1.55; color: {MUTED} !important; }}

/* CTA */
.bottom-cta {{
    max-width: 860px; margin: 0 auto 80px;
    text-align: center;
    border-radius: 32px; padding: 60px 60px;
    background: {GRAD_PRIMARY};
    position: relative; overflow: hidden;
    box-shadow: 0 20px 60px rgba(14,165,233,0.35);
}}
.bottom-cta::before {{
    content: ''; position: absolute;
    width: 400px; height: 400px; border-radius: 50%;
    background: rgba(255,255,255,0.08);
    top: -150px; right: -100px; pointer-events: none;
}}

/* Auth */
.auth-title {{ text-align: center; padding: 28px 0 18px; }}
.auth-title h1 {{ font-family: 'Sora', sans-serif; font-size: 30px; margin: 24px 0 6px; color: {TEXT} !important; font-weight: 800; }}
.auth-title p {{ font-size: 16px; color: {MUTED} !important; }}
.auth-logo-row {{ display: flex; justify-content: center; align-items: center; gap: 12px; font-family: 'Sora', sans-serif; font-size: 28px; font-weight: 900; color: {TEXT} !important; }}
.logo-square {{
    width: 40px; height: 40px; border-radius: 10px;
    background: {GRAD_PRIMARY};
    color: white !important; display: flex; align-items: center; justify-content: center;
    font-weight: 900; box-shadow: 0 4px 14px rgba(14,165,233,0.35);
}}

/* Page header */
.page-head {{ display: flex; align-items: center; gap: 16px; padding: 20px 28px 14px; }}
.page-icon {{
    width: 50px; height: 50px;
    background: {GRAD_PRIMARY};
    color: white !important; border-radius: 14px;
    display: flex; align-items: center; justify-content: center; font-size: 22px;
    box-shadow: 0 4px 16px rgba(14,165,233,0.30);
}}
.page-title {{ font-family: 'Sora', sans-serif; font-size: 27px; font-weight: 800; color: {TEXT} !important; }}
.page-sub {{ font-size: 15px; margin-top: 3px; color: {MUTED} !important; }}

/* Card headings */
.card-heading {{ display: flex; align-items: center; gap: 10px; font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 800; margin-bottom: 20px; color: {TEXT} !important; }}
.badge-num {{
    width: 28px; height: 28px;
    background: {GRAD_PRIMARY};
    color: white !important; border-radius: 999px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 13px;
}}

/* Results */
.result-high {{
    background: {RESULT_HIGH_BG}; border: 1.5px solid {RESULT_HIGH_BORDER};
    color: {RESULT_HIGH_TEXT} !important; padding: 28px; border-radius: 20px;
    text-align: center; font-weight: 800; font-size: 22px;
    font-family: 'Sora', sans-serif;
}}
.result-low {{
    background: {RESULT_LOW_BG}; border: 1.5px solid {RESULT_LOW_BORDER};
    color: {RESULT_LOW_TEXT} !important; padding: 28px; border-radius: 20px;
    text-align: center; font-weight: 800; font-size: 22px;
    font-family: 'Sora', sans-serif;
}}

/* Param cards */
.param-card {{
    background: {CARD2} !important; border: 1px solid {BORDER} !important;
    border-radius: 16px; padding: 18px 14px; text-align: center;
    transition: transform 0.2s ease;
}}
.param-card:hover {{ transform: translateY(-3px); }}
.param-label {{ color: {MUTED} !important; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }}
.param-value {{
    font-family: 'Sora', sans-serif; color: {TEXT} !important;
    font-size: 22px; font-weight: 800;
    background: {GRAD_PRIMARY};
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}

/* WhatsApp */
.wa-btn-wrap {{
    background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
    border-radius: 14px; padding: 14px 18px; cursor: pointer;
    text-align: center; font-weight: 700; font-size: 15px;
    color: white !important; text-decoration: none;
    display: flex; align-items: center; justify-content: center; gap: 10px;
    box-shadow: 0 8px 24px rgba(37,211,102,0.30);
    transition: all 0.2s ease;
    font-family: 'DM Sans', sans-serif;
}}
.wa-btn-wrap:hover {{ transform: translateY(-2px); box-shadow: 0 12px 32px rgba(37,211,102,0.38); filter: brightness(1.04); }}

/* Footer */
.footer {{
    border-top: 1px solid {BORDER}; padding: 26px 22px;
    display: flex; justify-content: space-between;
    color: {MUTED} !important; font-size: 14px;
}}
.footer-logo {{ font-family: 'Sora', sans-serif; font-weight: 800; color: {TEXT} !important; }}

/* Gradient divider */
.grad-divider {{
    height: 2px;
    background: {GRAD_PRIMARY};
    border-radius: 999px;
    margin: 0 auto 0;
    opacity: 0.6;
}}

/* Animations */
@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 20px rgba(14,165,233,0.3); }}
    50% {{ box-shadow: 0 0 40px rgba(14,165,233,0.55); }}
}}

/* Visibility fixes */
.stMarkdown, .stMarkdown *, .page-title, .card-heading, .section-title, .auth-title h1, div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"], .stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] * {{ color: {TEXT} !important; }}
.page-sub, .section-sub, .hero-sub, .step-text, .stat-label, .auth-title p, .param-label {{ color: {MUTED} !important; }}
.stDataFrame, .stDataFrame *, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {{ color: {TEXT} !important; font-weight: 600 !important; }}

@media(max-width:900px) {{
    .feature-grid, .steps-grid, .stats-wrap {{ grid-template-columns: 1fr; }}
    .hero-title {{ font-size: 52px; letter-spacing: -2px; }}
}}
</style>
'''
st.markdown(css, unsafe_allow_html=True)


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
        st.session_state.logged_in = True; st.session_state.user_type = 'doctor'; st.session_state.current_user_name = doctor.get('name', 'Doctor'); st.session_state.current_user_email = email; st.session_state.page = 'prediction'; add_audit('Login', email, 'Doctor logged in'); return True, ''
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
        return ['📋 Monitor blood glucose levels daily and keep a log.', '🥗 Reduce sugar and refined carbohydrate intake significantly.', '🏥 Consult a healthcare professional for proper evaluation and treatment.']
    if patient_data['BMI'] >= 30:
        return ['🥦 Follow a balanced calorie-controlled diet with whole foods.', '🏃 Exercise for at least 30 minutes daily — walking, swimming, or cycling.', '⚖️ Track your BMI and body weight weekly.']
    if patient_data['BloodPressure'] > 90:
        return ['🧂 Reduce sodium and processed food intake to lower BP.', '💊 Monitor blood pressure regularly with a home device.', '🧘 Practice yoga, walking, or meditation to manage stress.']
    return ['🥗 Maintain a balanced, nutritious diet rich in vegetables and whole grains.', '🏃 Exercise regularly — aim for 150 minutes of moderate activity per week.', '💧 Drink adequate water and get 7–9 hours of quality sleep nightly.']


def nice_label(key):
    label_map = {
        'Pregnancies': 'Pregnancies',
        'Glucose': 'Glucose (mg/dL)',
        'BloodPressure': 'Blood Pressure (mmHg)',
        'SkinThickness': 'Skin Thickness (mm)',
        'Insulin': 'Insulin (μU/mL)',
        'BMI': 'BMI',
        'DiabetesPedigreeFunction': 'Diabetes Pedigree Function',
        'Age': 'Age (years)'
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
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    bars = ax.bar(labels, values, color=colors, width=0.58, edgecolor='none')
    ax.set_title('Key Clinical Parameter Overview', fontsize=13, fontweight='bold', pad=14, color='#0A1628')
    ax.set_ylabel('Recorded value', fontsize=9, color='#4A6589')
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#C8DCF0')
    ax.tick_params(axis='x', labelsize=8, colors='#334155')
    ax.tick_params(axis='y', labelsize=8, colors='#64748B', length=0)
    ax.grid(axis='y', alpha=0.18, color='#94A3B8')
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.025, str(value), ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#0A1628')
    plt.tight_layout()
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    img.seek(0)
    return img


def create_risk_gauge_image(confidence, is_high):
    fig, ax = plt.subplots(figsize=(4.8, 2.45), dpi=190, subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.set_theta_offset(3.14159)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    theta = [i * 3.14159 / 180 for i in range(0, 181)]
    ax.plot(theta, [0.72]*len(theta), color='#E2E8F0', linewidth=22, solid_capstyle='round')
    val = max(0, min(float(confidence), 100))
    theta_val = [i * 3.14159 / 180 for i in range(0, int(180*val/100)+1)]
    color = '#F43F5E' if is_high else '#0D9488'
    ax.plot(theta_val, [0.72]*len(theta_val), color=color, linewidth=22, solid_capstyle='round')
    ax.text(3.14159/2, 0.30, f'{val:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold', color='#0A1628')
    ax.text(3.14159/2, 0.10, 'Model confidence', ha='center', va='center', fontsize=9, color='#64748B')
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    img.seek(0)
    return img



def generate_pdf(patient_data, result, confidence, name, email, pred_time):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    navy = (0.04, 0.09, 0.16)
    royal = (0.05, 0.64, 0.91)
    teal = (0.05, 0.58, 0.53)
    indigo = (0.39, 0.40, 0.95)
    slate = (0.06, 0.09, 0.16)
    muted = (0.29, 0.40, 0.55)
    soft = (0.94, 0.97, 1.00)
    line = (0.78, 0.86, 0.94)
    high = 'High' in result

    def rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

    def setc(c): pdf.setFillColorRGB(*c)
    def stroke(c): pdf.setStrokeColorRGB(*c)

    def rr(x, y, w, h, fill, border=None, r=14, sw=0.8):
        if border is None: border = line
        setc(fill); stroke(border); pdf.setLineWidth(sw)
        pdf.roundRect(x, y, w, h, r, fill=True, stroke=True)

    def label_value(x, y, label, value):
        pdf.setFont('Helvetica', 8); setc(muted); pdf.drawString(x, y + 14, label)
        pdf.setFont('Helvetica-Bold', 11); setc(slate); pdf.drawRightString(x + 205, y + 14, str(value))

    setc((1, 1, 1)); pdf.rect(0, 0, width, height, fill=True, stroke=False)
    setc(navy); pdf.rect(0, height - 128, width, 128, fill=True, stroke=False)
    setc(royal); pdf.roundRect(38, height - 90, 50, 50, 12, fill=True, stroke=False)
    setc((1,1,1)); pdf.setFont('Helvetica-Bold', 19); pdf.drawCentredString(63, height - 70, '🩺')
    pdf.setFont('Helvetica-Bold', 23); pdf.drawString(108, height - 52, 'GlucoTrack Clinical Report')
    pdf.setFont('Helvetica', 10); setc((0.6, 0.75, 0.92))
    pdf.drawString(108, height - 72, 'Diabetes Risk Assessment  |  Health Analytics  |  Action Plan')
    pdf.setFont('Helvetica', 9); pdf.drawString(108, height - 91, f'Generated: {pred_time}')

    chip_fill = rgb('#FEE2E2') if high else rgb('#D1FAE5')
    chip_text = rgb('#B91C1C') if high else rgb('#047857')
    rr(width - 185, height - 88, 140, 32, chip_fill, chip_fill, r=16, sw=0)
    pdf.setFont('Helvetica-Bold', 10); setc(chip_text)
    pdf.drawCentredString(width - 115, height - 67, '⚠ HIGH RISK' if high else '✓ LOW RISK')

    y = height - 168
    rr(38, y - 78, 248, 78, soft, line, r=16)
    pdf.setFont('Helvetica-Bold', 12); setc(slate); pdf.drawString(56, y - 24, 'Patient Information')
    pdf.setFont('Helvetica', 9.5); setc(muted)
    pdf.drawString(56, y - 44, f'Name: {name}'); pdf.drawString(56, y - 61, f'Email: {email}')

    risk_bg = rgb('#FEF2F2') if high else rgb('#ECFDF5')
    risk_border = rgb('#FCA5A5') if high else rgb('#6EE7B7')
    risk_text = rgb('#B91C1C') if high else rgb('#047857')
    rr(306, y - 78, width - 344, 78, risk_bg, risk_border, r=16, sw=1.2)
    pdf.setFont('Helvetica-Bold', 15); setc(risk_text); pdf.drawString(326, y - 30, result)
    pdf.setFont('Helvetica', 9.5); setc(muted)
    pdf.drawString(326, y - 50, 'Assessment based on clinical parameters')
    pdf.setFont('Helvetica-Bold', 13); setc(risk_text)
    pdf.drawRightString(width - 54, y - 34, f'{confidence}%')
    pdf.setFont('Helvetica', 8.5); setc(muted); pdf.drawRightString(width - 54, y - 50, 'confidence')

    y -= 112
    pdf.setFont('Helvetica-Bold', 12); setc(slate); pdf.drawString(38, y, 'Quick Health Summary')
    y -= 48
    summary = [('Glucose', f"{patient_data['Glucose']} mg/dL", '#0EA5E9'), ('BMI', f"{patient_data['BMI']}", '#0D9488'), ('Blood Pressure', f"{patient_data['BloodPressure']} mmHg", '#F97316'), ('Age', f"{patient_data['Age']} years", '#6366F1')]
    card_w = (width - 96) / 4
    for i, (title, value, color_hex) in enumerate(summary):
        x = 38 + i * (card_w + 8)
        rr(x, y - 60, card_w, 60, (1,1,1), line, r=13)
        setc(rgb(color_hex)); pdf.roundRect(x + 12, y - 24, 8, 24, 4, fill=True, stroke=False)
        pdf.setFont('Helvetica', 8); setc(muted); pdf.drawString(x + 26, y - 19, title)
        pdf.setFont('Helvetica-Bold', 14); setc(slate); pdf.drawString(x + 26, y - 42, value)

    y -= 92
    pdf.setFont('Helvetica-Bold', 12); setc(slate); pdf.drawString(38, y, 'Clinical Measurements')
    y -= 20
    items = list(patient_data.items()); col_w = (width - 96) / 2; row_h = 29
    for idx, (key, value) in enumerate(items):
        col = idx % 2; row = idx // 2; x = 38 + col * (col_w + 20); yy = y - row * row_h
        rr(x, yy - 23, col_w, 23, (1,1,1), line, r=7, sw=0.5)
        label_value(x + 10, yy - 27, nice_label(key), value)

    y -= 142
    pdf.setFont('Helvetica-Bold', 12); setc(slate); pdf.drawString(38, y, 'Health Analytics')
    rr(38, y - 188, 328, 173, (1,1,1), line, r=16)
    rr(380, y - 188, width - 418, 173, (1,1,1), line, r=16)
    chart_img = create_pdf_chart_image(patient_data)
    pdf.drawImage(ImageReader(chart_img), 48, y - 178, width=308, height=143, preserveAspectRatio=True, mask='auto')
    gauge_img = create_risk_gauge_image(confidence, high)
    pdf.drawImage(ImageReader(gauge_img), 395, y - 175, width=163, height=128, preserveAspectRatio=True, mask='auto')
    pdf.setFont('Helvetica-Bold', 9); setc(slate); pdf.drawCentredString(466, y - 168, 'Risk Confidence Gauge')

    y -= 222
    rr(38, y - 102, width - 76, 102, rgb('#F0FDFA'), rgb('#99F6E4'), r=16)
    pdf.setFont('Helvetica-Bold', 12); setc(slate); pdf.drawString(56, y - 24, '💡 Recommended Health Action Plan')
    pdf.setFont('Helvetica', 9.5); setc((0.10, 0.18, 0.28)); yy = y - 46
    for i, s in enumerate(get_suggestions(patient_data), start=1):
        setc(teal); pdf.circle(62, yy + 3, 6, fill=True, stroke=False)
        setc((1,1,1)); pdf.setFont('Helvetica-Bold', 7); pdf.drawCentredString(62, yy + 1, str(i))
        s_clean = ''.join(c for c in s if ord(c) < 65536 and not (0x1F000 <= ord(c) <= 0x1FFFF))
        setc((0.10, 0.18, 0.28)); pdf.setFont('Helvetica', 9.5); pdf.drawString(76, yy, s_clean.strip()); yy -= 20

    stroke(line); pdf.line(38, 46, width - 38, 46)
    pdf.setFont('Helvetica-Oblique', 7.5); setc((0.44, 0.50, 0.58))
    pdf.drawCentredString(width/2, 32, 'Disclaimer: This report is for educational and screening purposes only — not a medical diagnosis.')
    pdf.drawCentredString(width/2, 20, 'Please consult a qualified healthcare professional before making any medical decisions.')
    pdf.save()
    return buffer.getvalue()


def public_header():
    col_logo, col_nav, col_spacer, col_theme, col_signin = st.columns([2.5, 4.0, 2.0, 1.2, 1.2])
    with col_logo:
        st.markdown(f'''
        <div style="display:flex;align-items:center;gap:12px;font-family:'Sora',sans-serif;font-size:22px;font-weight:900;color:{TEXT};margin-top:10px;">
            <div style="width:38px;height:38px;border-radius:10px;background:{GRAD_PRIMARY};color:white;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;box-shadow:0 4px 14px rgba(14,165,233,0.35);">🩺</div>
            GlucoTrack
        </div>
        ''', unsafe_allow_html=True)
    with col_nav:
        st.markdown(f'''
        <div style="display:flex;gap:28px;margin-top:14px;">
            <a href="#features" class="nav-link" target="_self">✨ Features</a>
            <a href="#how-it-works" class="nav-link" target="_self">🔄 How It Works</a>
        </div>
        ''', unsafe_allow_html=True)
    with col_theme:
        theme_label = '☀️ Light' if st.session_state.dark_mode else '🌙 Dark'
        if st.button(theme_label, key='pub_theme_toggle', type='secondary', use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode; st.rerun()
    with col_signin:
        if st.button('Sign In →', key='nav_signin', type='primary', use_container_width=True):
            st.session_state.started = True; st.session_state.page = 'auth'; st.session_state.auth_mode = 'signin'; st.rerun()
    st.markdown(f'<div class="grad-divider" style="margin-bottom:0;"></div>', unsafe_allow_html=True)


def dashboard_sidebar():
    if not st.session_state.started or not st.session_state.logged_in: return
    name = st.session_state.current_user_name; email = st.session_state.current_user_email
    role = {'patient': '🧑 Patient', 'doctor': '👨⚕️ Doctor', 'admin': '🛡️ Admin'}.get(st.session_state.user_type, 'User')
    init = initials(name)
    profile_pic = None
    if st.session_state.user_type == 'patient' and email in users:
        profile_pic = users[email].get('profile_pic')
    elif st.session_state.user_type == 'doctor' and email in doctors:
        profile_pic = doctors[email].get('profile_pic')
    if profile_pic:
        avatar_html = f'<img src="data:image/png;base64,{profile_pic}" style="width:48px;height:48px;border-radius:14px;object-fit:cover;display:block;">'
    else:
        avatar_html = f'<div class="sb-avatar">{init}</div>'
    st.sidebar.markdown(f'<div class="sb-header"><div class="sb-logo-box">🩺</div><div class="sb-brand">GlucoTrack</div></div><div class="sb-profile">{avatar_html}<div><div class="sb-name">{name if name else "Loading..."}</div><div class="sb-role">{role}</div></div></div>', unsafe_allow_html=True)
    if st.sidebar.button('✏️ Edit Profile', use_container_width=True): st.session_state.page = 'profile'; st.rerun()
    if st.sidebar.button('☀️ Light Mode' if st.session_state.dark_mode else '🌙 Dark Mode', use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode; st.rerun()

    if st.session_state.user_type == 'patient':
        options = ['prediction', 'dashboard']
        labels = ['🩺 Predict Risk', '📊 Health Dashboard']
    elif st.session_state.user_type == 'doctor':
        options = ['prediction', 'doctor', 'dashboard']
        labels = ['🩺 Predict Risk', '👨⚕️ Patient Data', '📊 Health Dashboard']
    else:
        options = ['admin', 'prediction', 'dashboard']
        labels = ['🛡️ Admin Panel', '🩺 Predict Risk', '📊 Dashboard']

    if st.session_state.page not in options and st.session_state.page != 'profile':
        st.session_state.page = options[0]
    if st.session_state.page != 'profile':
        idx = options.index(st.session_state.page) if st.session_state.page in options else 0
        selected_label = st.sidebar.radio('', labels, index=idx, label_visibility='collapsed')
        selected_page = options[labels.index(selected_label)]
        if selected_page != st.session_state.page: st.session_state.page = selected_page; st.rerun()
    st.sidebar.markdown('<div style="height:180px;"></div>', unsafe_allow_html=True)
    if st.sidebar.button('↪ Sign Out', use_container_width=True):
        add_audit('Logout', st.session_state.current_user_email, 'User logged out')
        for key in ['logged_in', 'user_type', 'current_user_name', 'current_user_email', 'prediction_done', 'patient_data', 'prediction_result', 'confidence', 'prediction_time', 'pdf_bytes']:
            st.session_state[key] = defaults[key]
        st.session_state.page = 'auth'; st.session_state.auth_mode = 'signin'; st.rerun()


# UPDATE 3: Removed the hacky Javascript block from landing_page that was breaking the sidebar
def landing_page():
    public_header()

    # Hero section with Get Started button INSIDE the hero card

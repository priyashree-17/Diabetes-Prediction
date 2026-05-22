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

css = f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800;900&family=DM+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif !important; }}
.stApp {{ background: {BG} !important; }}
.block-container {{ padding-top: 1.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; max-width: 100% !important; }}
h1,h2,h3,h4,h5,h6 {{ font-family: 'Sora', sans-serif !important; color: {TEXT} !important; }}
p, label, span {{ font-family: 'DM Sans', sans-serif !important; color: {TEXT} !important; }}

/* ── Hide keyboard_double_arrow collapse button ── */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarNavCollapseButton"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"],
.st-emotion-cache-pkbazv,
.st-emotion-cache-1cypcdb,
.st-emotion-cache-dvne4q,
.st-emotion-cache-1gwvy71 {{
    display: none !important;
    height: 0 !important;
    overflow: hidden !important;
}}
section[data-testid="stSidebar"] > div > div {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}

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

# Inject JS directly into page via st.markdown to hide keyboard_double_arrow sidebar button
st.markdown("""
<script>
(function() {
    var HIDE = 'display:none!important;height:0!important;width:0!important;overflow:hidden!important;padding:0!important;margin:0!important;opacity:0!important;position:absolute!important;pointer-events:none!important;';
    function hideKbd() {
        // Target 1: the sidebar collapse button by its SVG icon test id
        ['keyboard_double_arrow_left', 'keyboard_double_arrow_right'].forEach(function(tid) {
            document.querySelectorAll('svg[data-testid="' + tid + '"]').forEach(function(svg) {
                var el = svg;
                for (var i = 0; i < 5; i++) {
                    if (!el) break;
                    el.style.cssText = HIDE;
                    if (el.tagName === 'BUTTON' || el.tagName === 'DIV') break;
                    el = el.parentElement;
                }
            });
        });
        // Target 2: any text node inside sidebar starting with "keyboard_"
        var sb = document.querySelector('[data-testid="stSidebar"]');
        if (!sb) return;
        var tw = document.createTreeWalker(sb, NodeFilter.SHOW_TEXT);
        var n;
        while (n = tw.nextNode()) {
            if (/^keyboard_/.test(n.textContent.trim())) {
                var el = n.parentElement;
                for (var i = 0; i < 5 && el && el !== sb; i++) {
                    el.style.cssText = HIDE;
                    el = el.parentElement;
                }
            }
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            hideKbd();
            new MutationObserver(hideKbd).observe(document.body, {childList:true, subtree:true});
        });
    } else {
        hideKbd();
        new MutationObserver(hideKbd).observe(document.body, {childList:true, subtree:true});
    }
})();
</script>
""", unsafe_allow_html=True)


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
    # Draw stethoscope icon using vector shapes (ReportLab cannot render emoji)
    cx, cy = 63, height - 65  # center of icon box
    setc((1, 1, 1))
    stroke((1, 1, 1))
    pdf.setLineWidth(2.2)
    # Chest piece — filled circle
    pdf.circle(cx, cy - 7, 7, fill=True, stroke=False)
    # Chest piece inner circle
    setc(royal)
    pdf.circle(cx, cy - 7, 3.5, fill=True, stroke=False)
    setc((1, 1, 1))
    # Tube — arc going up-left then curving right to earpiece fork
    from reportlab.graphics.shapes import Path
    from reportlab.lib.colors import Color, white
    pdf.setStrokeColorRGB(1, 1, 1)
    pdf.setLineWidth(2.4)
    pdf.setLineCap(1)
    # Left tube arm
    pdf.bezier(cx - 7, cy - 1,   cx - 14, cy + 4,   cx - 14, cy + 12,  cx - 9, cy + 16)
    # Right tube arm
    pdf.bezier(cx + 7, cy - 1,   cx + 14, cy + 4,   cx + 14, cy + 12,  cx + 9, cy + 16)
    # Top connector bar
    pdf.line(cx - 9, cy + 16, cx + 9, cy + 16)
    # Left earpiece dot
    pdf.setFillColorRGB(1, 1, 1)
    pdf.circle(cx - 9, cy + 18, 2.2, fill=True, stroke=False)
    # Right earpiece dot
    pdf.circle(cx + 9, cy + 18, 2.2, fill=True, stroke=False)
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


# FIX 2: Doctor sidebar now includes Predict Risk + Doctor Portal + Dashboard
def dashboard_sidebar():
    if not st.session_state.started or not st.session_state.logged_in: return
    # Re-run keyboard hide on every sidebar render (Streamlit re-renders on interaction)
    st.markdown("""
    <script>
    (function() {
        var H='display:none!important;height:0!important;width:0!important;overflow:hidden!important;padding:0!important;margin:0!important;opacity:0!important;position:absolute!important;';
        function hide() {
            ['keyboard_double_arrow_left','keyboard_double_arrow_right'].forEach(function(t){
                document.querySelectorAll('svg[data-testid="'+t+'"]').forEach(function(s){
                    for(var e=s,i=0;e&&i<6;e=e.parentElement,i++){e.style.cssText=H;if(e.tagName==='BUTTON')break;}
                });
            });
            var sb=document.querySelector('[data-testid="stSidebar"]');
            if(!sb)return;
            var tw=document.createTreeWalker(sb,NodeFilter.SHOW_TEXT);
            var n;
            while(n=tw.nextNode()){
                if(/^keyboard_/.test(n.textContent.trim())){
                    for(var e=n.parentElement,i=0;e&&e!==sb&&i<5;e=e.parentElement,i++)e.style.cssText=H;
                }
            }
        }
        hide();
        new MutationObserver(hide).observe(document.body,{childList:true,subtree:true});
    })();
    </script>
    """, unsafe_allow_html=True)
    name = st.session_state.current_user_name; email = st.session_state.current_user_email
    role = {'patient': '🧑 Patient', 'doctor': '👨‍⚕️ Doctor', 'admin': '🛡️ Admin'}.get(st.session_state.user_type, 'User')
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

    # FIX 2: Doctors now get Predict Risk + Patient Data + Dashboard
    if st.session_state.user_type == 'patient':
        options = ['prediction', 'dashboard']
        labels = ['🩺 Predict Risk', '📊 Health Dashboard']
    elif st.session_state.user_type == 'doctor':
        options = ['prediction', 'doctor', 'dashboard']
        labels = ['🩺 Predict Risk', '👨‍⚕️ Patient Data', '📊 Health Dashboard']
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


def landing_page():
    public_header()

    # Hero section with Get Started button INSIDE the hero card
    st.markdown(f'''
    <section class="hero-section">
        <div class="hero-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-glow2"></div>
        <div class="hero-badge">🧬 AI-POWERED HEALTH PLATFORM</div>
        <h1 class="hero-title">
            Know Your<br>
            <span class="hero-gradient-text">Diabetes Risk</span>
        </h1>
        <p class="hero-sub">
            Get a science-backed diabetes risk assessment in under 2 minutes.<br>
            Powered by Machine Learning. Built for your health.
        </p>
        <div style="position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;gap:14px;margin-top:20px;">
            <a href="?hero_clicked=1" style="
                display:inline-flex;align-items:center;justify-content:center;gap:10px;
                background:{GRAD_PRIMARY};
                color:white !important;text-decoration:none;border-radius:16px;
                padding:16px 52px;
                font-family:'DM Sans',sans-serif;
                font-weight:700;font-size:17px;cursor:pointer;
                box-shadow:0 8px 28px rgba(14,165,233,0.38);
                min-width:270px;transition:all 0.2s ease;
            ">🚀 Get Started Free</a>
        </div>
    </section>
    ''', unsafe_allow_html=True)

    # Check if hero HTML button was clicked (sets query param)
    params = st.query_params
    if params.get('hero_clicked') == '1':
        st.query_params.clear()
        st.session_state.started = True; st.session_state.page = 'auth'; st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()

    # Stats
    st.markdown(f'''
    <div class="stats-wrap" style="margin-top:52px;">
        <div class="stat">
            <div class="stat-num">95%+</div>
            <div class="stat-label">🎯 Model Accuracy</div>
        </div>
        <div class="stat">
            <div class="stat-num">8</div>
            <div class="stat-label">🔬 Health Parameters Analyzed</div>
        </div>
        <div class="stat">
            <div class="stat-num">100%</div>
            <div class="stat-label">💸 Completely Free to Use</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Features Section
    st.markdown(f'''
    <section id="features" class="section" style="padding-top:20px;">
        <h2 class="section-title">What GlucoTrack Does</h2>
        <p class="section-sub">Three powerful features to monitor, predict, and improve your health</p>
        <div class="feature-grid">
            <div class="feature-card feature-blue">
                <div class="pill pill-blue">🧠 MACHINE LEARNING</div>
                <div class="icon-box icon-blue">🔬</div>
                <div class="feature-title">AI-Powered Risk Prediction</div>
                <div class="feature-text">Our trained ML model analyzes 8 clinical parameters — Glucose, BMI, Insulin, Blood Pressure, Age, Pregnancies, Skin Thickness, and DPF — to compute your diabetes risk with a confidence score.</div>
            </div>
            <div class="feature-card feature-green">
                <div class="pill pill-green">📊 ANALYTICS</div>
                <div class="icon-box icon-green">📈</div>
                <div class="feature-title">Interactive Health Dashboard</div>
                <div class="feature-text">Visualize your health data through dynamic charts, glucose gauges, and BMI indicators inside a clean, beautiful dashboard. Track your progress over time.</div>
            </div>
            <div class="feature-card feature-purple">
                <div class="pill pill-purple">💡 PERSONALIZED</div>
                <div class="icon-box icon-purple">🩺</div>
                <div class="feature-title">Smart Health Recommendations</div>
                <div class="feature-text">Get targeted, personalized health recommendations based on your specific clinical values — diet tips, exercise plans, and lifestyle changes tailored just for you.</div>
            </div>
        </div>
    </section>
    ''', unsafe_allow_html=True)

    # How It Works
    st.markdown(f'''
    <section id="how-it-works" class="section">
        <h2 class="section-title">How It Works</h2>
        <p class="section-sub">Get your diabetes risk assessment in 4 simple steps</p>
        <div class="steps-grid">
            <div class="step-card">
                <div class="step-num">01</div>
                <div class="step-title">🔐 Create Account</div>
                <div class="step-text">Sign up free with your name and email address in under a minute</div>
            </div>
            <div class="step-card">
                <div class="step-num">02</div>
                <div class="step-title">🩺 Enter Health Data</div>
                <div class="step-text">Fill in your 8 clinical health values from your latest lab report</div>
            </div>
            <div class="step-card">
                <div class="step-num">03</div>
                <div class="step-title">🤖 Get AI Prediction</div>
                <div class="step-text">Our ML model instantly calculates your personalized diabetes risk</div>
            </div>
            <div class="step-card">
                <div class="step-num">04</div>
                <div class="step-title">📄 View & Share Report</div>
                <div class="step-text">Download a PDF report or share it directly via WhatsApp with your doctor</div>
            </div>
        </div>
    </section>
    ''', unsafe_allow_html=True)

    # Bottom CTA
    st.markdown(f'''
    <section class="section" style="padding-bottom:24px;">
        <div class="bottom-cta">
            <div style="font-size:48px;margin-bottom:16px;">❤️‍🩹</div>
            <h2 style="font-family:'Sora',sans-serif;font-size:36px;font-weight:900;margin:0 0 16px;color:white !important;">Take Control of Your Health Today</h2>
            <p style="font-size:19px;line-height:1.6;margin-bottom:36px;color:rgba(255,255,255,0.88) !important;">Join thousands using GlucoTrack to monitor their diabetes risk. Free, fast, and takes less than 2 minutes.</p>
        </div>
    </section>
    ''', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.8, 1.5, 1.8])
    with c2:
        if st.button('🚀 Create Free Account →', key='bottom_signup_btn', type='primary', use_container_width=True):
            st.session_state.started = True; st.session_state.page = 'auth'; st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()

    st.markdown(f'''
    <div style="text-align:center;margin:16px 0 0;color:{MUTED};font-size:14px;font-family:'DM Sans',sans-serif;">
        ✅ Free forever &nbsp;·&nbsp; 🔒 Private &amp; secure &nbsp;·&nbsp; ⚡ Results in seconds
    </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'''
    <div class="footer">
        <div class="footer-logo">🩺 GlucoTrack</div>
        <div>For educational purposes only. Always consult a medical professional.</div>
        <div>© 2025 GlucoTrack</div>
    </div>
    ''', unsafe_allow_html=True)


def auth_page():
    public_header()
    if st.button('← Back to Home', key='auth_back_home', type='secondary'):
        st.session_state.started = False; st.session_state.page = 'home'; st.rerun()

    if st.session_state.auth_mode == 'signin':
        st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Welcome back 👋</h1><p>Sign in to continue to your health dashboard</p></div>', unsafe_allow_html=True)
        c1, col_card, c3 = st.columns([1, 1.8, 1])
        with col_card:
            with st.container(border=True):
                # Demo credentials info box — always visible
                st.markdown(f'''
                <div style="background:{'#0F1E35' if DARK else '#EFF8FF'};border:1px solid {'#1E3358' if DARK else '#BAE0FD'};
                            border-radius:14px;padding:14px 18px;margin-bottom:16px;font-family:DM Sans,Arial;">
                    <div style="font-weight:700;font-size:13px;color:{'#60A5FA' if DARK else '#0369A1'};margin-bottom:8px;">
                        🔑 Demo Credentials
                    </div>
                    <div style="font-size:13px;color:{'#8BA4C8' if DARK else '#4A6589'};line-height:1.8;">
                        🧑 <b>Patient:</b> user@gmail.com &nbsp;/&nbsp; user@123<br>
                        🛡️ <b>Admin:</b> admin@glucotrack.com &nbsp;/&nbsp; admin@123<br>
                        👨‍⚕️ <b>Doctor:</b> doctor@glucotrack.com &nbsp;/&nbsp; Doc@1234
                    </div>
                </div>
                ''', unsafe_allow_html=True)

                email = st.text_input('📧 Email address', placeholder='you@example.com', key='signin_email')
                password = st.text_input('🔒 Password', type='password', placeholder='Your password', key='signin_password')
                is_admin = st.checkbox('Are you an admin or doctor?', key='is_admin_login')
                st.write('')
                if st.button('Sign In →', type='primary', use_container_width=True, key='signin_btn'):
                    ok, msg = login_user(email, password)
                    if ok: st.rerun()
                    else:
                        st.error(f'❌ {msg}')
                        st.markdown(f'''
                        <div style="font-size:12px;color:{'#8BA4C8' if DARK else '#64748B'};margin-top:4px;padding:0 4px;">
                            💡 If you registered with a custom password, use that. 
                            Or delete <code>users.json</code> to reset to demo credentials.
                        </div>
                        ''', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;margin:18px 0;color:{MUTED};">— or —</div>', unsafe_allow_html=True)
                if st.button('✨ Create a free account →', type='secondary', use_container_width=True, key='to_signup'):
                    st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 1; st.rerun()
                st.markdown(f'<p style="text-align:center;color:{MUTED};margin-top:20px;">🔒 Your health data is private and never shared.</p>', unsafe_allow_html=True)
    else:
        if st.session_state.signup_step == 1:
            st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Create your account 🎉</h1><p>Step 1 of 2 — Personal Details</p><div style="height:6px;background:{GRAD_PRIMARY};border-radius:8px;max-width:560px;margin:28px auto 0;width:50%;"></div></div>', unsafe_allow_html=True)
            c1, col_card, c3 = st.columns([1, 1.8, 1])
            with col_card:
                with st.container(border=True):
                    full_name = st.text_input('👤 Full Name *', placeholder='John Doe', key='reg_name')
                    email = st.text_input('📧 Email Address *', placeholder='you@example.com', key='reg_email')
                    phone = st.text_input('📞 Phone Number *', placeholder='+91 98765 43210', key='reg_phone')
                    c_a, c_b = st.columns(2)
                    with c_a: age = st.number_input('🎂 Age *', 1, 100, 25, key='reg_age')
                    with c_b: gender = st.selectbox('⚧ Gender', ['Select', 'Female', 'Male', 'Other'], key='reg_gender')
                    address = st.text_area('🏠 Address', placeholder='Your address (optional)', key='reg_address')
                    if st.button('Continue →', type='primary', use_container_width=True, key='reg_continue'):
                        email_clean = email.strip().lower()
                        if not full_name or not email_clean or not phone: st.error('⚠️ Please fill all required fields.')
                        elif gender == 'Select': st.error('⚠️ Please select your gender.')
                        elif email_clean in users or email_clean in doctors or email_clean in admins: st.error('❌ Email already registered. Please sign in.')
                        else:
                            st.session_state.signup_name = full_name.strip(); st.session_state.signup_email = email_clean; st.session_state.signup_phone = phone.strip(); st.session_state.signup_age = age; st.session_state.signup_gender = gender; st.session_state.signup_address = address.strip(); st.session_state.signup_step = 2; st.rerun()
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
                        st.markdown(f'<div style="margin:-4px 0 18px;"><div style="height:5px;border-radius:5px;background:#E2E8F0;overflow:hidden;"><div style="height:100%;width:{width_pct}%;background:{color};border-radius:5px;transition:width 0.3s ease;"></div></div><div style="font-size:13px;color:{color};font-weight:700;margin-top:6px;">{label} · {hint_text}</div></div>', unsafe_allow_html=True)
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
    public_header()
    if st.button('← Back to Password Setup', key='create_profile_back', type='secondary'):
        st.session_state.page = 'auth'; st.session_state.auth_mode = 'signup'; st.session_state.signup_step = 2; st.rerun()
    st.markdown(f'<div class="auth-title"><div class="auth-logo-row"><div class="logo-square">🩺</div><div>GlucoTrack</div></div><h1>Choose Your Profile 👤</h1><p>Are you a patient or a healthcare professional?</p></div>', unsafe_allow_html=True)
    c1, col_card, c3 = st.columns([1, 1.8, 1])
    with col_card:
        with st.container(border=True):
            role = st.radio('I am a', ['🧑 Patient', '👨‍⚕️ Doctor'], horizontal=True)
            name = st.text_input('👤 Full Name', value=st.session_state.signup_name)
            email = st.text_input('📧 Email', value=st.session_state.signup_email, disabled=True)
            if '🧑' in role:
                phone = st.text_input('📞 Phone', value=st.session_state.signup_phone)
                age = st.number_input('🎂 Age', 1, 100, int(st.session_state.signup_age))
                gender = st.selectbox('⚧ Gender', ['Female', 'Male', 'Other'], index=['Female', 'Male', 'Other'].index(st.session_state.signup_gender) if st.session_state.signup_gender in ['Female', 'Male', 'Other'] else 0)
                address = st.text_area('🏠 Address', value=st.session_state.signup_address)
                uploaded_photo = st.file_uploader('📸 Upload Profile Photo (Optional)', type=['png', 'jpg', 'jpeg'], key='patient_photo')
                if st.button('✅ Create Patient Profile', type='primary', use_container_width=True):
                    base64_photo = None
                    if uploaded_photo:
                        base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                    users[st.session_state.signup_email] = {'password': st.session_state.signup_password, 'name': name, 'phone': phone, 'age': age, 'gender': gender, 'address': address, 'medical_history': '', 'user_type': 'patient', 'profile_created': True, 'profile_pic': base64_photo}
                    save_json(USERS_FILE, users)
                    add_audit('Account Created', st.session_state.signup_email, 'Patient profile created')
                    ok, msg = login_user(st.session_state.signup_email, st.session_state.signup_password)
                    if ok: st.rerun()
                    else: st.error(msg)
            else:
                phone = st.text_input('📞 Phone', value=st.session_state.signup_phone)
                specialization = st.text_input('🔬 Specialization', placeholder='Endocrinology')
                hospital = st.text_input('🏥 Hospital / Clinic')
                license_no = st.text_input('📋 Medical License No.')
                uploaded_photo = st.file_uploader('📸 Upload Profile Photo (Optional)', type=['png', 'jpg', 'jpeg'], key='doctor_photo')
                if st.button('✅ Create Doctor Profile', type='primary', use_container_width=True):
                    base64_photo = None
                    if uploaded_photo:
                        base64_photo = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                    doctors[st.session_state.signup_email] = {'password': st.session_state.signup_password, 'name': name, 'phone': phone, 'specialization': specialization, 'hospital': hospital, 'license_no': license_no, 'approved': False, 'user_type': 'doctor', 'profile_created': True, 'profile_pic': base64_photo}
                    save_json(DOCTORS_FILE, doctors)
                    add_audit('Doctor Signup', st.session_state.signup_email, 'Waiting for approval')
                    st.success('✅ Doctor profile created! Please wait for admin approval before signing in.')
                    st.session_state.page = 'auth'; st.session_state.auth_mode = 'signin'; st.rerun()


def prediction_page():
    st.markdown('<div class="page-head"><div class="page-icon">🩺</div><div><div class="page-title">Diabetes Risk Prediction</div><div class="page-sub">Enter your clinical parameters for an AI-powered assessment</div></div></div>', unsafe_allow_html=True)

    components.html(f'''
    <div style="background:linear-gradient(135deg,{GRAD1}18,{GRAD2}12);border:1px solid {GRAD1}44;border-radius:18px;padding:18px 24px;margin-bottom:18px;font-family:'DM Sans',Arial;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:20px;">🔬</span>
            <span style="font-family:'Sora',Arial;font-weight:800;font-size:16px;color:{TEXT};">About This Assessment</span>
        </div>
        <p style="color:{MUTED};font-size:14px;margin:0;line-height:1.6;">
            Fill in your latest clinical values below. Our ML model analyzes these 8 parameters to calculate your diabetes risk level.
            All values should come from a recent lab test or medical report for best accuracy.
        </p>
    </div>
    ''', height=120)

    with st.container(border=True):
        st.markdown('<div class="card-heading"><div class="badge-num">1</div>Clinical Health Parameters</div>', unsafe_allow_html=True)
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown(f'<p style="color:{MUTED};font-size:13px;margin-bottom:12px;">🔵 Metabolic Indicators</p>', unsafe_allow_html=True)
            preg = st.number_input('🤰 Pregnancies', 0, 20, 1, help='Number of times pregnant')
            glucose = st.number_input('🩸 Glucose (mg/dL)', 50, 250, 120, help='Plasma glucose concentration (2hr OGTT). Normal: <140, Prediabetes: 140–199, Diabetes: ≥200')
            insulin = st.number_input('💉 Insulin (μU/mL)', 0, 400, 100, help='2-Hour serum insulin. Normal: 16–166 μU/mL')
            dpf = st.number_input('🧬 Diabetes Pedigree', 0.0, 3.0, 0.5, help='Diabetes pedigree function — family history score')
        with c_right:
            st.markdown(f'<p style="color:{MUTED};font-size:13px;margin-bottom:12px;">🟢 Physical Indicators</p>', unsafe_allow_html=True)
            bp = st.number_input('💓 Blood Pressure (mmHg)', 30, 140, 70, help='Diastolic blood pressure. Normal: 60–80 mmHg')
            skin = st.number_input('📏 Skin Thickness (mm)', 0, 100, 20, help='Triceps skin fold thickness')
            bmi = st.number_input('⚖️ BMI', 10.0, 70.0, 25.0, help='Body Mass Index. Normal: 18.5–24.9, Overweight: 25–29.9, Obese: ≥30')
            # For doctor, use default age 35 since they may be entering for a patient
            if st.session_state.user_type == 'patient':
                default_age = int(users.get(st.session_state.current_user_email, {}).get('age', 30))
            else:
                default_age = 35
            age = st.number_input('🎂 Age (years)', 1, 100, default_age)

    components.html(f'''
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px;font-family:'DM Sans',Arial;">
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
            <div style="font-size:18px;margin-bottom:4px;">🩸</div>
            <div style="font-size:11px;color:{MUTED};font-weight:600;">GLUCOSE</div>
            <div style="font-size:12px;color:{TEXT};font-weight:700;">Normal &lt;140</div>
        </div>
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
            <div style="font-size:18px;margin-bottom:4px;">⚖️</div>
            <div style="font-size:11px;color:{MUTED};font-weight:600;">BMI</div>
            <div style="font-size:12px;color:{TEXT};font-weight:700;">Normal 18.5–24.9</div>
        </div>
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
            <div style="font-size:18px;margin-bottom:4px;">💓</div>
            <div style="font-size:11px;color:{MUTED};font-weight:600;">BLOOD PRESSURE</div>
            <div style="font-size:12px;color:{TEXT};font-weight:700;">Normal 60–80</div>
        </div>
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:12px;text-align:center;">
            <div style="font-size:18px;margin-bottom:4px;">💉</div>
            <div style="font-size:11px;color:{MUTED};font-weight:600;">INSULIN</div>
            <div style="font-size:12px;color:{TEXT};font-weight:700;">Normal 16–166</div>
        </div>
    </div>
    ''', height=100)

    st.write('')
    if st.button('🔍 Predict My Diabetes Risk →', type='primary', use_container_width=True):
        patient_data = {'Pregnancies': preg, 'Glucose': glucose, 'BloodPressure': bp, 'SkinThickness': skin, 'Insulin': insulin, 'BMI': bmi, 'DiabetesPedigreeFunction': dpf, 'Age': age}
        result, confidence = model_predict(patient_data)
        pred_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        name = st.session_state.current_user_name; email = st.session_state.current_user_email
        pdf = generate_pdf(patient_data, result, confidence, name, email, pred_time)
        st.session_state.patient_data = patient_data; st.session_state.prediction_result = result; st.session_state.confidence = confidence; st.session_state.prediction_time = pred_time; st.session_state.pdf_bytes = pdf; st.session_state.prediction_done = True
        reports.append({'name': name, 'email': email, 'result': result, 'confidence': confidence, 'time': pred_time, 'data': patient_data})
        save_json(REPORTS_FILE, reports)
        add_audit('Prediction', email, result)
        st.session_state.page = 'dashboard'; st.rerun()


# FIX 4: WhatsApp share widget — now also used standalone for doctors
def _render_whatsapp_share(phone_key, pdf_bytes, patient_name, result, confidence, pred_time, patient_data, selected_idx=None):
    """Share PDF via browser native Web Share API — no API keys required."""
    import base64 as _b64

    DARK_LOCAL = st.session_state.dark_mode
    bg_col     = '#031A0F' if DARK_LOCAL else '#F0FDF4'
    border_col = '#166534' if DARK_LOCAL else '#BBF7D0'
    text_col   = '#F0F6FF' if DARK_LOCAL else '#0A1628'
    muted_col  = '#8BA4C8' if DARK_LOCAL else '#4A6589'

    # Header card
    st.markdown(f"""
    <div style="background:{bg_col};border:1.5px solid {border_col};border-radius:18px;
                padding:20px 24px;margin-top:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <span style="font-size:22px;">📱</span>
            <span style="font-family:'Sora',Arial;font-weight:800;font-size:16px;color:{text_col};">
                Share PDF Report via WhatsApp
            </span>
        </div>
        <p style="color:{muted_col};font-size:13px;margin:4px 0 0 32px;">
            Opens your device share sheet — select WhatsApp to send the PDF file directly.
            Works on mobile &amp; supported desktop browsers.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # Build caption
    caption = (
        f"🩺 GlucoTrack Diabetes Risk Report\n"
        f"👤 Patient: {patient_name}\n"
        f"📊 Result: {result}\n"
        f"🎯 Confidence: {confidence}%\n"
        f"📅 Date: {pred_time}\n"
        f"🩸 Glucose: {patient_data.get('Glucose','N/A')} mg/dL\n"
        f"⚖️ BMI: {patient_data.get('BMI','N/A')}\n"
        f"💓 BP: {patient_data.get('BloodPressure','N/A')} mmHg\n"
        f"Powered by GlucoTrack AI Health Platform"
    )
    safe_caption = caption.replace("`", "'").replace("\\", "\\\\")
    file_name    = f"GlucoTrack_{patient_name.replace(' ', '_')}_Report.pdf"
    pdf_b64      = _b64.b64encode(pdf_bytes).decode("utf-8")

    col_share, col_dl = st.columns([3, 2])

    with col_share:
        # Web Share API button — shares the actual PDF file
        components.html(f"""
        <div style="margin:0;">
          <button id="sharePdfBtn_{phone_key}" style="
              width:100%;
              background:linear-gradient(135deg,#16A34A 0%,#22C55E 100%);
              color:white; border:none; padding:14px 20px;
              border-radius:14px; cursor:pointer; font-weight:700;
              font-size:15px; font-family:'DM Sans',Arial,sans-serif;
              box-shadow:0 8px 20px rgba(34,197,94,0.30);
              display:flex; align-items:center; justify-content:center; gap:8px;
              transition:all 0.2s ease;">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
                 fill="white" viewBox="0 0 16 16">
              <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.93
                       c0 1.39.365 2.743 1.06 3.962L0 16l4.13-1.082A7.86 7.86 0 0 0 7.99 12
                       c4.365 0 7.934-3.558 7.939-7.93a7.86 7.86 0 0 0-2.328-5.744
                       M7.993 11.89c-1.392 0-2.702-.38-3.829-1.08l-.275-.164-2.429.637
                       .649-2.368-.18-.287a5.95 5.95 0 0 1-.98-3.216c.004-3.279 2.685-5.96
                       5.966-5.96 1.587.001 3.079.616 4.2 1.738a5.96 5.96 0 0 1 1.729 4.2
                       c-.004 3.28-2.685 5.96-5.966 5.96M11.53 8.87c-.191-.096-1.136-.56
                       -1.31-.624-.173-.064-.3-.096-.426.096-.127.192-.49.61-.6.732
                       -.11.123-.219.138-.41.042-.191-.096-.807-.297-1.537-.95
                       -.568-.506-.95-1.133-1.062-1.324-.112-.19-.012-.294.084-.389
                       .087-.085.191-.223.287-.335.095-.112.127-.19.19-.32.064-.13
                       .032-.243-.016-.339-.048-.096-.426-1.026-.583-1.407-.152-.37
                       -.308-.32-.426-.326-.11-.006-.237-.008-.363-.008-.127 0-.332.048
                       -.506.237-.174.19-.66 1.63-.66 3.97 0 2.34 1.7 4.595 1.94 4.914
                       .24.318 3.352 5.12 8.12 7.18 1.133.49 2.02.784 2.709 1.004
                       1.134.36 2.167.309 2.984.187.912-.136 2.793-.113 3.197-1.197
                       .404-1.084.404-2.013.283-2.203-.12-.19-.32-.304-.51-.399"/>
            </svg>
            &nbsp;Share PDF on WhatsApp
          </button>
          <p id="shareStatus_{phone_key}" style="
              font-family:Arial,sans-serif; font-size:12px;
              color:#64748B; margin:8px 0 0; min-height:16px;"></p>
        </div>
        <script>
        (function() {{
          var btn    = document.getElementById('sharePdfBtn_{phone_key}');
          var status = document.getElementById('shareStatus_{phone_key}');
          btn.onmouseenter = function() {{ btn.style.transform='translateY(-2px)'; btn.style.boxShadow='0 12px 28px rgba(34,197,94,0.40)'; }};
          btn.onmouseleave = function() {{ btn.style.transform='translateY(0)';    btn.style.boxShadow='0 8px 20px rgba(34,197,94,0.30)';  }};
          btn.onclick = async function() {{
            try {{
              var b64 = "{pdf_b64}";
              var binary = atob(b64);
              var bytes  = new Uint8Array(binary.length);
              for (var i = 0; i < binary.length; i++) {{
                bytes[i] = binary.charCodeAt(i);
              }}
              var file = new File([bytes], "{file_name}", {{ type: "application/pdf" }});
              if (navigator.canShare && navigator.canShare({{ files: [file] }})) {{
                await navigator.share({{
                  title: "GlucoTrack Diabetes Report",
                  text:  `{safe_caption}`,
                  files: [file]
                }});
                status.style.color = "#16A34A";
                status.innerText = "✅ Share panel opened — select WhatsApp to send the PDF.";
              }} else {{
                status.style.color = "#F97316";
                status.innerText = "⚠️ Your browser doesn\'t support file sharing. Please download the PDF and send it manually via WhatsApp.";
              }}
            }} catch(err) {{
              if (err.name !== "AbortError") {{
                status.style.color = "#EF4444";
                status.innerText = "❌ Sharing cancelled or not supported. Download the PDF and attach it in WhatsApp.";
              }}
            }}
          }};
        }})();
        </script>
        """, height=110)

    with col_dl:
        st.download_button(
            "📥 Download PDF",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            use_container_width=True,
            key=f"wa_dl_{phone_key}"
        )

    st.caption("ℹ️ Works best on mobile Chrome/Safari. On desktop, the file will be downloaded — attach it in WhatsApp Web manually.")


def dashboard_page():
    st.markdown('<div class="page-head"><div class="page-icon">📊</div><div><div class="page-title">Health Dashboard</div><div class="page-sub">Your prediction result, analytics, and personalized recommendations</div></div></div>', unsafe_allow_html=True)
    if not st.session_state.prediction_done:
        st.warning('⚠️ No prediction found. Please complete a prediction first.')
        if st.button('🩺 Go to Prediction', type='primary'): st.session_state.page = 'prediction'; st.rerun()
        return
    result = st.session_state.prediction_result; confidence = st.session_state.confidence; patient_data = st.session_state.patient_data

    st.markdown(f'<div class="{"result-high" if "High" in result else "result-low"}">{"⚠️" if "High" in result else "✅"} {result}<br><span style="font-size:16px;font-weight:600;opacity:0.85;">Model Confidence: {confidence}%</span></div>', unsafe_allow_html=True)
    st.write('')

    st.subheader('🧾 Submitted Health Parameters')
    params = list(patient_data.items()); cols = st.columns(4)
    for i, (k, v) in enumerate(params):
        with cols[i % 4]: st.markdown(f'<div class="param-card"><div class="param-label">{nice_label(k)}</div><div class="param-value">{v}</div></div>', unsafe_allow_html=True)

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
        f'''<div style="display:flex;align-items:flex-start;gap:14px;padding:14px 0;
                    border-bottom:1px solid {BORDER if not DARK else "#1E3358"};">
            <div style="min-width:32px;height:32px;border-radius:50%;
                        background:linear-gradient(135deg,{GRAD1},{GRAD2});
                        color:white;display:flex;align-items:center;justify-content:center;
                        font-weight:800;font-size:13px;flex-shrink:0;">{i}</div>
            <div style="font-size:15px;line-height:1.65;color:{BOX_SUGGESTION_TEXT};
                        font-weight:600;padding-top:4px;">{s}</div>
        </div>'''
        for i, s in enumerate(suggestions, 1)
    ])
    st.markdown(f'''
    <div style="background:{BOX_SUGGESTION_BG};padding:24px 28px;border-radius:20px;
                border:1px solid {BORDER};margin-top:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <span style="font-size:22px;">💡</span>
            <h3 style="font-family:Sora,sans-serif;font-size:18px;font-weight:800;
                       margin:0;color:{BOX_SUGGESTION_TITLE};">Personalized Health Suggestions</h3>
        </div>
        <p style="color:{MUTED};font-size:13px;margin:0 0 12px 32px;">
            Based on your clinical values
        </p>
        {suggestion_rows}
    </div>
    ''', unsafe_allow_html=True)

    st.write('')
    st.subheader('📤 Send Report via WhatsApp')
    _render_whatsapp_share(
        phone_key='patient_dash',
        pdf_bytes=st.session_state.pdf_bytes,
        patient_name=st.session_state.current_user_name,
        result=result,
        confidence=confidence,
        pred_time=st.session_state.prediction_time,
        patient_data=patient_data
    )

    st.write('')
    if st.button('🔄 New Prediction', type='secondary', use_container_width=True): reset_prediction_state(); st.session_state.page = 'prediction'; st.rerun()


def doctor_page():
    st.markdown('<div class="page-head"><div class="page-icon">👨‍⚕️</div><div><div class="page-title">Doctor Portal</div><div class="page-sub">Comprehensive Patient Directory & Clinical Health Analytics</div></div></div>', unsafe_allow_html=True)
    high_cases = [r for r in reports if 'High' in r.get('result', '')]
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric('📋 Total Assessments', len(reports))
        c2.metric('⚠️ High Risk Patients', len(high_cases))
        c3.metric('🧑 Registered Patients', len(users))

    st.write('')
    tab_dir, tab_detail = st.tabs(['📋 Patient Reports Directory', '🔍 Detailed Patient Analysis'])

    with tab_dir:
        st.subheader('All Patient Reports')
        if not reports: st.info('📭 No patient reports available yet.')
        else:
            report_data = []
            for idx, r in enumerate(reports):
                data_dict = r.get('data', {})
                report_data.append({'ID': idx, 'Patient Name': r.get('name'), 'Email': r.get('email'), 'Risk Level': r.get('result'), 'Confidence': f"{r.get('confidence')}%", 'Assessment Time': r.get('time'), 'Glucose': data_dict.get('Glucose', 'N/A'), 'BMI': data_dict.get('BMI', 'N/A'), 'BP': data_dict.get('BloodPressure', 'N/A'), 'Age': data_dict.get('Age', 'N/A')})
            df_reports = pd.DataFrame(report_data)
            st.dataframe(df_reports.drop(columns=['ID']), use_container_width=True)

    with tab_detail:
        if not reports: st.info('📭 No patient reports available.')
        else:
            report_options = [f"{r.get('name')} ({r.get('time')}) — {r.get('result')}" for r in reports]
            selected_idx = st.selectbox('🔍 Select Patient Report:', range(len(reports)), format_func=lambda x: report_options[x])
            selected_report = reports[selected_idx]
            patient_data = selected_report.get('data', {})
            result = selected_report.get('result'); confidence = selected_report.get('confidence'); pred_time = selected_report.get('time'); name = selected_report.get('name'); email = selected_report.get('email')
            patient_info = users.get(email, {}); phone = patient_info.get('phone', 'Not Provided'); age = patient_info.get('age', patient_data.get('Age', 'N/A')); gender = patient_info.get('gender', 'Not Provided')

            st.markdown(f'''
            <div style="background:{CARD};border:1px solid {BORDER};padding:24px;border-radius:20px;margin-bottom:20px;">
                <h3 style="margin-top:0;font-family:Sora,sans-serif;color:{TEXT};">👤 Patient Profile: {name}</h3>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;font-size:14px;">
                    <div><b>📧 Email:</b><br>{email}</div>
                    <div><b>📞 Phone:</b><br>{phone}</div>
                    <div><b>🎂 Age:</b><br>{age}</div>
                    <div><b>⚧ Gender:</b><br>{gender}</div>
                </div>
                <div class="{"result-high" if "High" in result else "result-low"}" style="padding:14px;">
                    {"⚠️" if "High" in result else "✅"} <b>Assessment:</b> {result} &nbsp;·&nbsp; {confidence}% Confidence
                </div>
            </div>
            ''', unsafe_allow_html=True)

            st.subheader('📋 Clinical Health Parameters')
            param_labels = {'Pregnancies': '🤰 Pregnancies', 'Glucose': '🩸 Glucose (mg/dL)', 'BloodPressure': '💓 Blood Pressure (mmHg)', 'SkinThickness': '📏 Skin Thickness (mm)', 'Insulin': '💉 Insulin (μU/mL)', 'BMI': '⚖️ BMI (kg/m²)', 'DiabetesPedigreeFunction': '🧬 Diabetes Pedigree', 'Age': '🎂 Age (years)'}
            cols = st.columns(4)
            for i, (key, label) in enumerate(param_labels.items()):
                val = patient_data.get(key, 'N/A')
                with cols[i % 4]: st.markdown(f'<div class="param-card"><div class="param-label">{label}</div><div class="param-value">{val}</div></div>', unsafe_allow_html=True)

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
                    f'''<div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;
                                border-bottom:1px solid {BORDER};">
                        <div style="min-width:26px;height:26px;border-radius:50%;
                                    background:linear-gradient(135deg,{GRAD1},{GRAD2});
                                    color:white;display:flex;align-items:center;justify-content:center;
                                    font-weight:800;font-size:12px;flex-shrink:0;">{idx2}</div>
                        <div style="font-size:14px;line-height:1.6;color:{BOX_SUGGESTION_TEXT};
                                    font-weight:600;padding-top:2px;">{sug}</div>
                    </div>'''
                    for idx2, sug in enumerate(suggestions, 1)
                ])
                st.markdown(f'''
                <div style="background:{BOX_SUGGESTION_BG};padding:18px 20px;border-radius:16px;
                            border:1px solid {BORDER};margin-top:4px;">
                    <h4 style="font-family:Sora,sans-serif;font-size:16px;font-weight:800;
                               margin:0 0 12px;color:{BOX_SUGGESTION_TITLE};">💡 Recommendations</h4>
                    {doc_rows}
                </div>
                ''', unsafe_allow_html=True)

            st.write('')
            st.subheader('📤 Export & Share')
            pdf_data = generate_pdf(patient_data, result, confidence, name, email, pred_time)
            st.subheader('📤 Send Report via WhatsApp')
            _render_whatsapp_share(phone_key=f'doctor_{selected_idx}', pdf_bytes=pdf_data, patient_name=name, result=result, confidence=confidence, pred_time=pred_time, patient_data=patient_data, selected_idx=selected_idx)


def admin_page():
    st.markdown('<div class="page-head"><div class="page-icon">🛡️</div><div><div class="page-title">Admin Panel</div><div class="page-sub">Manage doctors, users, reports, and audit logs</div></div></div>', unsafe_allow_html=True)
    pending = {email: d for email, d in doctors.items() if not d.get('approved', False)}
    high = [r for r in reports if 'High' in r.get('result', '')]

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('🧑 Patients', len(users)); c2.metric('👨‍⚕️ Doctors', len(doctors)); c3.metric('⏳ Pending', len(pending)); c4.metric('⚠️ High Risk', len(high))

    st.write('')
    st.subheader('⏳ Doctor Approval Requests')
    if not pending: st.success('✅ No pending doctor approvals.')
    else:
        for email, d in pending.items():
            with st.container(border=True):
                st.write(f"**👤 Name:** {d.get('name')} &nbsp;|&nbsp; **📧 Email:** {email}")
                st.write(f"🔬 Specialization: {d.get('specialization')} &nbsp;·&nbsp; 🏥 Hospital: {d.get('hospital')} &nbsp;·&nbsp; 📋 License: {d.get('license_no')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f'✅ Approve {email}', key=f'approve_{email}', type='primary', use_container_width=True):
                        doctors[email]['approved'] = True; save_json(DOCTORS_FILE, doctors); add_audit('Doctor Approved', st.session_state.current_user_email, email); st.rerun()
                with col2:
                    if st.button(f'❌ Reject {email}', key=f'reject_{email}', type='secondary', use_container_width=True):
                        doctors.pop(email); save_json(DOCTORS_FILE, doctors); add_audit('Doctor Rejected', st.session_state.current_user_email, email); st.rerun()

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
    st.markdown('<div class="page-head"><div class="page-icon">👤</div><div><div class="page-title">My Profile</div><div class="page-sub">Update your personal details and photo</div></div></div>', unsafe_allow_html=True)
    email = st.session_state.current_user_email; utype = st.session_state.user_type

    with st.container(border=True):
        if utype == 'patient':
            user = users[email]
            name = st.text_input('👤 Name', value=user.get('name', ''))
            phone = st.text_input('📞 Phone', value=user.get('phone', ''))
            age = st.number_input('🎂 Age', 1, 100, int(user.get('age', 25)))
            gender = st.selectbox('⚧ Gender', ['Female', 'Male', 'Other'], index=['Female', 'Male', 'Other'].index(user.get('gender', 'Female')) if user.get('gender') in ['Female', 'Male', 'Other'] else 0)
            address = st.text_area('🏠 Address', value=user.get('address', ''))
            uploaded_photo = st.file_uploader('📸 Change Profile Photo', type=['png', 'jpg', 'jpeg'], key='edit_patient_photo')
            if st.button('💾 Save Profile', type='primary', use_container_width=True):
                update_data = {'name': name, 'phone': phone, 'age': age, 'gender': gender, 'address': address}
                if uploaded_photo:
                    update_data['profile_pic'] = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                users[email].update(update_data); save_json(USERS_FILE, users); st.session_state.current_user_name = name
                add_audit('Profile Updated', email, 'Patient profile updated'); st.success('✅ Profile updated!'); st.rerun()
        elif utype == 'doctor':
            doctor = doctors[email]
            name = st.text_input('👤 Name', value=doctor.get('name', ''))
            phone = st.text_input('📞 Phone', value=doctor.get('phone', ''))
            specialization = st.text_input('🔬 Specialization', value=doctor.get('specialization', ''))
            hospital = st.text_input('🏥 Hospital', value=doctor.get('hospital', ''))
            license_no = st.text_input('📋 License No.', value=doctor.get('license_no', ''))
            uploaded_photo = st.file_uploader('📸 Change Profile Photo', type=['png', 'jpg', 'jpeg'], key='edit_doctor_photo')
            if st.button('💾 Save Profile', type='primary', use_container_width=True):
                update_data = {'name': name, 'phone': phone, 'specialization': specialization, 'hospital': hospital, 'license_no': license_no}
                if uploaded_photo:
                    update_data['profile_pic'] = base64.b64encode(uploaded_photo.getvalue()).decode('utf-8')
                doctors[email].update(update_data); save_json(DOCTORS_FILE, doctors); st.session_state.current_user_name = name
                add_audit('Profile Updated', email, 'Doctor profile updated'); st.success('✅ Profile updated!'); st.rerun()
        else: st.info('ℹ️ Admin profile editing is not available.')


# ===== ROUTER =====
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

import streamlit as st
import pandas as pd
import pickle
from datetime import datetime
from io import BytesIO

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
    "users": {"user@gmail.com": "1234"},
    "admins": {"admin@glucotrack.com": "admin@123"},
    "prediction_done": False,
    "patient_data": None,
    "prediction_result": None,
    "confidence": None,
    "pdf_bytes": None
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
else:
    bg = "#F6FBFC"
    card = "#FFFFFF"
    text = "#1E293B"
    accent = "#0284C7"
    input_text = "#1E293B"
    sidebar_bg = "linear-gradient(180deg, #8ECAE6, #219EBC)"
    plot_template = "plotly_white"

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
    background: {sidebar_bg};
}}

section[data-testid="stSidebar"] > div {{
    background: transparent;
}}

section[data-testid="stSidebar"] * {{
    color: white !important;
}}

div[data-testid="stRadio"] label {{
    background: rgba(255,255,255,0.14);
    padding: 12px 16px;
    border-radius: 14px;
    margin-bottom: 8px;
    font-weight: 600;
}}

div[data-testid="stRadio"] label:hover {{
    background: rgba(255,255,255,0.25);
}}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stMarkdown,
label,
p,
h1,
h2,
h3,
h4,
h5,
h6,
span {{
    color: {input_text} !important;
}}

div[data-baseweb="input"] > div {{
    background-color: {card} !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
}}

input {{
    background-color: {card} !important;
    color: {input_text} !important;
}}

.stNumberInput input {{
    background-color: {card} !important;
    color: {input_text} !important;
}}

textarea {{
    background-color: {card} !important;
    color: {input_text} !important;
}}

div[data-baseweb="select"] > div {{
    background-color: {card} !important;
    color: {input_text} !important;
    border-radius: 12px !important;
}}

div[data-baseweb="select"] * {{
    color: {input_text} !important;
}}

.hero {{
    background: linear-gradient(135deg, #8ECAE6, #FFAFCC);
    padding: 50px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0px 8px 30px rgba(0,0,0,0.18);
}}

.hero-title {{
    font-size: 54px;
    font-weight: 900;
    color: #073B4C !important;
}}

.hero-sub {{
    font-size: 20px;
    color: #073B4C !important;
}}

.result-high {{
    background: #FFE4E6;
    color: #BE123C !important;
    padding: 28px;
    border-radius: 20px;
    font-size: 26px;
    font-weight: 800;
    text-align: center;
}}

.result-low {{
    background: #DCFCE7;
    color: #166534 !important;
    padding: 28px;
    border-radius: 20px;
    font-size: 26px;
    font-weight: 800;
    text-align: center;
}}

.stButton>button,
.stDownloadButton>button {{
    background-color: {accent};
    color: white !important;
    border-radius: 12px;
    padding: 10px 26px;
    border: none;
    font-weight: 700;
}}

.stButton>button:hover,
.stDownloadButton>button:hover {{
    background-color: #0369A1;
    color: white !important;
}}
</style>
""", unsafe_allow_html=True)

# ==============================
# HOME PAGE
# ==============================
def home_page():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">🩺 GlucoTrack</div>
        <p class="hero-sub">
        A smart diabetes risk prediction and patient health analytics system.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    col1, col2, col3 = st.columns(3)
    col1.info("📊 ML-based diabetes risk prediction")
    col2.success("📈 Patient health analytics")
    col3.warning("💡 Personalized health suggestions")

    st.write("")

    if st.button("🚀 Get Started"):
        st.session_state.started = True
        st.rerun()


if not st.session_state.started:
    home_page()
    st.stop()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.markdown("## 🩺 GLUCOTRACK")
st.sidebar.caption("Smart Health Dashboard")
st.sidebar.markdown("---")

if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as: {st.session_state.role}")

menu_options = ["User Login", "Sign Up", "Admin Login"]

if st.session_state.logged_in:
    menu_options = ["Prediction"]
    if st.session_state.role == "Admin":
        menu_options.insert(0, "Admin Dashboard")

st.session_state.page = st.sidebar.radio(
    "",
    menu_options,
    label_visibility="collapsed"
)

if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.prediction_done = False
        st.session_state.patient_data = None
        st.session_state.prediction_result = None
        st.session_state.confidence = None
        st.session_state.pdf_bytes = None
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
        if email in st.session_state.users and st.session_state.users[email] == password:
            st.session_state.logged_in = True
            st.session_state.role = "User"
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
                st.session_state.users[email] = new_pass
                st.success("Account created successfully. Please login using your email ID.")


def admin_login():
    st.title("🛡️ Admin Login")

    email = st.text_input("Admin Email ID")
    password = st.text_input("Admin Password", type="password")

    if st.button("Admin Login"):
        if email in st.session_state.admins and st.session_state.admins[email] == password:
            st.session_state.logged_in = True
            st.session_state.role = "Admin"
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

    st.subheader("Registered User Emails")

    st.dataframe(
        pd.DataFrame({"Email ID": list(st.session_state.users.keys())}),
        use_container_width=True
    )

# ==============================
# HEALTH SUGGESTIONS
# ==============================
def get_suggestions(patient_data):
    glucose = patient_data["Glucose"]
    bmi = patient_data["BMI"]
    bp = patient_data["BloodPressure"]

    if glucose >= 126:
        return [
            "Monitor blood glucose levels regularly",
            "Reduce sugar and refined carbohydrate intake",
            "Consult a healthcare professional for diabetes management"
        ]

    elif bmi >= 30:
        return [
            "Follow a calorie-controlled healthy diet",
            "Exercise for at least 30 minutes daily",
            "Track weight and BMI regularly"
        ]

    elif bp > 90:
        return [
            "Reduce sodium and processed food intake",
            "Monitor blood pressure regularly",
            "Maintain daily physical activity"
        ]

    else:
        return [
            "Maintain a balanced nutritious diet",
            "Exercise regularly to stay active",
            "Drink enough water and get adequate sleep"
        ]

# ==============================
# PDF REPORT
# ==============================
def generate_pdf_report(patient_data, result, confidence):
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 60

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "GlucoTrack Diabetes Risk Report")

    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Generated On: {datetime.now().strftime('%d-%m-%Y %H:%M')}")

    y -= 45
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Patient Health Details")

    y -= 25
    pdf.setFont("Helvetica", 11)

    for key, value in patient_data.items():
        pdf.drawString(60, y, f"{key}: {value}")
        y -= 22

    y -= 10
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Prediction Result")

    y -= 28
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, y, result)

    y -= 20
    pdf.drawString(60, y, f"Prediction Confidence: {confidence}%")

    y -= 45
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Health Recommendations")

    y -= 25
    pdf.setFont("Helvetica", 10)

    suggestions = get_suggestions(patient_data)

    for suggestion in suggestions:
        pdf.drawString(60, y, f"- {suggestion[:90]}")
        y -= 18

    y -= 25
    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, y, "Note: This report is generated using a machine learning model.")

    y -= 15
    pdf.drawString(50, y, "It should not replace professional medical advice.")

    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes

# ==============================
# PATIENT ANALYTICS
# ==============================
def show_patient_analytics(patient_data):
    st.subheader("📊 Patient Health Analytics")

    metrics = ["Glucose", "BMI", "Insulin", "BloodPressure", "Age"]
    values = [patient_data[m] for m in metrics]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=metrics,
        y=values,
        marker_color=["#FF6B9A", "#4D96FF", "#F4A261", "#52B788", "#9D79BC"],
        text=values,
        textposition="outside"
    ))

    fig.update_layout(
        title="Patient Health Parameter Overview",
        xaxis_title="Health Parameter",
        yaxis_title="Value",
        template=plot_template,
        height=420
    )

    st.plotly_chart(fig, use_container_width=True)

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=patient_data["Glucose"],
        title={"text": "Glucose Level"},
        gauge={
            "axis": {"range": [0, 250]},
            "bar": {"color": "#FF6B9A"},
            "steps": [
                {"range": [0, 99], "color": "#DCFCE7"},
                {"range": [100, 125], "color": "#FEF9C3"},
                {"range": [126, 250], "color": "#FFE4E6"}
            ]
        }
    ))

    gauge.update_layout(
        height=350,
        template=plot_template
    )

    st.plotly_chart(gauge, use_container_width=True)

# ==============================
# HEALTH RECOMMENDATIONS CARD
# ==============================
def show_health_suggestions(patient_data):
    suggestions = get_suggestions(patient_data)

    if dark_mode:
        card_bg = "linear-gradient(135deg, #081C3A, #0D5B63)"
        title_color = "#FFFFFF"
        point_color = "#22C55E"
    else:
        card_bg = "linear-gradient(135deg, #D9F0FF, #C7E9FF)"
        title_color = "#0F172A"
        point_color = "#059669"

    points = ""
    for suggestion in suggestions:
        points += f"<li>{suggestion}</li>"

    html_code = f"""
    <div style="
        background: {card_bg};
        padding: 28px 34px;
        border-radius: 22px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        font-family: Arial, sans-serif;
    ">
        <h2 style="
            color: {title_color};
            font-size: 30px;
            font-weight: 800;
            margin-bottom: 18px;
        ">
            💡 Health Recommendations
        </h2>

        <ul style="
            color: {point_color};
            font-size: 17px;
            font-weight: 600;
            line-height: 1.45;
            margin: 0;
            padding-left: 28px;
        ">
            {points}
        </ul>
    </div>
    """

    components.html(html_code, height=230)

# ==============================
# PREDICTION PAGE
# ==============================
def prediction_page():
    st.title("🩺 Diabetes Prediction")
    st.write("Enter patient health details below:")

    col1, col2 = st.columns(2)

    with col1:
        preg = st.number_input("Pregnancies", 0, 20, 1)
        glucose = st.number_input("Glucose", 50, 250, 120)
        bp = st.number_input("Blood Pressure", 30, 140, 70)
        skin = st.number_input("Skin Thickness", 0, 100, 20)

    with col2:
        insulin = st.number_input("Insulin", 0, 400, 100)
        bmi = st.number_input("BMI", 10.0, 70.0, 25.0)
        dpf = st.number_input("Diabetes Pedigree Function", 0.0, 3.0, 0.5)
        age = st.number_input("Age", 1, 100, 30)

    if st.button("Predict Diabetes Risk"):
        patient_data = {
            "Pregnancies": preg,
            "Glucose": glucose,
            "BloodPressure": bp,
            "SkinThickness": skin,
            "Insulin": insulin,
            "BMI": bmi,
            "DiabetesPedigreeFunction": dpf,
            "Age": age
        }

        input_raw = pd.DataFrame([patient_data])

        input_raw["Glucose_BMI"] = input_raw["Glucose"] * input_raw["BMI"]
        input_raw["Insulin_Glucose"] = input_raw["Insulin"] * input_raw["Glucose"]
        input_raw["Age_BMI"] = input_raw["Age"] * input_raw["BMI"]
        input_raw["BMI_Squared"] = input_raw["BMI"] ** 2

        input_encoded = pd.get_dummies(input_raw)
        input_df = input_encoded.reindex(columns=columns, fill_value=0)

        prediction = model.predict(input_df)

        if hasattr(model, "predict_proba"):
            probability = model.predict_proba(input_df)[0]

            if prediction[0] == 1:
                result = "High Risk of Diabetes"
                confidence = round(probability[1] * 100, 2)
            else:
                result = "Low Risk of Diabetes"
                confidence = round(probability[0] * 100, 2)
        else:
            result = "High Risk of Diabetes" if prediction[0] == 1 else "Low Risk of Diabetes"
            confidence = "N/A"

        st.session_state.prediction_done = True
        st.session_state.patient_data = patient_data
        st.session_state.prediction_result = result
        st.session_state.confidence = confidence
        st.session_state.pdf_bytes = generate_pdf_report(patient_data, result, confidence)

    if st.session_state.prediction_done:
        result = st.session_state.prediction_result
        patient_data = st.session_state.patient_data
        confidence = st.session_state.confidence

        if result == "High Risk of Diabetes":
            st.markdown(f"""
            <div class='result-high'>
                ⚠️ High Risk of Diabetes<br>
                Prediction Confidence: {confidence}%
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='result-low'>
                ✅ Low Risk of Diabetes<br>
                Prediction Confidence: {confidence}%
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        show_patient_analytics(patient_data)
        show_health_suggestions(patient_data)

        st.download_button(
            label="📄 Download Patient Report",
            data=st.session_state.pdf_bytes,
            file_name="glucotrack_patient_report.pdf",
            mime="application/pdf"
        )

# ==============================
# ROUTING
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

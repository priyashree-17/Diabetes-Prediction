import streamlit as st
import pandas as pd
import pickle

# ==============================
# LOAD MODEL & COLUMNS
# ==============================
model = pickle.load(open("diabetes_model.pkl", "rb"))
columns = pickle.load(open("columns.pkl", "rb"))

# ==============================
# UI
# ==============================
st.title("🩺 Diabetes Prediction App")
st.write("Enter patient details below:")

# Inputs
preg = st.number_input("Pregnancies", 0, 20, 1)
glucose = st.number_input("Glucose", 50, 200, 120)
bp = st.number_input("Blood Pressure", 30, 120, 70)
skin = st.number_input("Skin Thickness", 0, 100, 20)
insulin = st.number_input("Insulin", 0, 300, 100)
bmi = st.number_input("BMI", 10.0, 60.0, 25.0)
dpf = st.number_input("Diabetes Pedigree Function", 0.0, 3.0, 0.5)
age = st.number_input("Age", 1, 100, 30)

# ==============================
# PREDICTION
# ==============================
if st.button("Predict"):

    # --------------------------
    # Create input dataframe
    # --------------------------
    input_raw = pd.DataFrame({
        'Pregnancies': [preg],
        'Glucose': [glucose],
        'BloodPressure': [bp],
        'SkinThickness': [skin],
        'Insulin': [insulin],
        'BMI': [bmi],
        'DiabetesPedigreeFunction': [dpf],
        'Age': [age]
    })

    # --------------------------
    # Feature Engineering
    # --------------------------
    input_raw['Glucose_BMI'] = input_raw['Glucose'] * input_raw['BMI']
    input_raw['Insulin_Glucose'] = input_raw['Insulin'] * input_raw['Glucose']
    input_raw['Age_BMI'] = input_raw['Age'] * input_raw['BMI']
    input_raw['BMI_Squared'] = input_raw['BMI'] ** 2

    # --------------------------
    # Encoding
    # --------------------------
    input_encoded = pd.get_dummies(input_raw)

    # --------------------------
    # Match training columns
    # --------------------------
    input_df = input_encoded.reindex(columns=columns, fill_value=0)

    # --------------------------
    # Prediction
    # --------------------------
    prediction = model.predict(input_df)

    # --------------------------
    # Output
    # --------------------------
    if prediction[0] == 1:
        st.error("⚠️ High Risk of Diabetes")
    else:
        st.success("✅ Low Risk of Diabetes")
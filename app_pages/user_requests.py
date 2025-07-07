import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# --- Google Sheets Setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "FidSync Submissions"
TAB_NAME = "Form Responses 1"

# 👤 Admin email for preview access
ADMIN_EMAIL = "crods611@gmail.com"

def log_to_google_sheets(name, email, request_type, message, uploaded_file=None, timestamp=None):
    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        if not timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        file_name = uploaded_file.name if uploaded_file else ""
        row = [timestamp, name, email, request_type, message, file_name]
        worksheet.append_row(row, value_input_option="USER_ENTERED")

        return True
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

def is_admin_user():
    return st.session_state.get("email") == ADMIN_EMAIL

def get_all_submissions():
    creds_dict = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    gc = gspread.authorize(credentials)
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(TAB_NAME)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

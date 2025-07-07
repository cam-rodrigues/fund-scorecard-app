import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# === Google Sheets Setup ===
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_NAME = "FidSync Submissions"
TAB_NAME = "Form Responses 1"
COLUMNS = ["Timestamp", "Name", "Email", "Type", "Message", "File"]

# Set your Google login for admin view
ADMIN_EMAIL = "crods611@gmail.com"

def log_to_google_sheets(name, email, message, timestamp, request_type="Other", file_url=None):
    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        row = [timestamp, name, email, request_type, message, file_url or ""]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"⚠️ Failed to log to Google Sheets: {e}")
        return False

def render_admin_preview():
    if st.session_state.get("email") == ADMIN_EMAIL:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        st.markdown("### Admin Preview (Private)")
        st.dataframe(df)

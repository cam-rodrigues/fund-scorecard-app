import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# === Google Sheets Setup ===
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "FidSync Submissions"
TAB_NAME = "Form Responses 1"
COLUMNS = ["Timestamp", "Name", "Email", "Type", "Message", "File"]

# Admin login email to unlock preview
ADMIN_EMAIL = "crods611@gmail.com"

def log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp):
    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        file_name = uploaded_file.name if uploaded_file else ""
        row = [timestamp, name, email, request_type, message, file_name]

        # Write row
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        st.error(f"⚠️ Failed to log to Google Sheets: {e}")
        return False


def render_admin_preview():
    if st.session_state.get("email") != ADMIN_EMAIL:
        return

    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        data = worksheet.get_all_records()
        st.subheader("📊 All Submissions")
        st.dataframe(pd.DataFrame(data))

    except Exception as e:
        st.error(f"⚠️ Failed to load submissions: {e}")

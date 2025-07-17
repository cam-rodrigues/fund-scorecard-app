# utils/google_sheets.py

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

def log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        client = gspread.authorize(creds)
        sheet = client.open("FidSync Requests").sheet1

        file_name = uploaded_file.name if uploaded_file else ""

        sheet.append_row([timestamp, name, email, request_type, message, file_name])
        return True

    except Exception as e:
        print(f"Logging failed: {e}")
        return False

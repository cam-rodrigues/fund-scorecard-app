import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

def log_to_google_sheets(data):
    try:
        credentials = Credentials.from_service_account_info(st.secrets["gspread"])
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("your-google-sheet-id")
        worksheet = sh.sheet1
        worksheet.append_row(data)
        return True
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

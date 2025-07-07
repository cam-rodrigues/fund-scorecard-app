import gspread
from datetime import datetime
import streamlit as st

def log_to_google_sheets(name, email, request_type, message, file_url=None):
    try:
        creds = st.secrets["gspread"]
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_key("1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY")
        worksheet = sh.sheet1  # First sheet

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now, name, email, request_type, message, file_url or ""]
        worksheet.append_row(row)

        return True
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

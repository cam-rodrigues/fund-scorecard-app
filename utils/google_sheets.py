import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def log_to_google_sheets(name, email, message, file_link, timestamp):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials_dict = st.secrets["gspread"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)

        client = gspread.authorize(creds)
        sheet = client.open_by_key("1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY")
        worksheet = sheet.sheet1

        worksheet.append_row([name, email, message, file_link, timestamp])

    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")

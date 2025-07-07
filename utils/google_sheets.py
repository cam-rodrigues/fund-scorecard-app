import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def log_to_google_sheets(name, email, message, filename, file_url):
    try:
        # Authenticate with credentials stored in .streamlit/secrets.toml
        credentials = Credentials.from_service_account_info(st.secrets["gspread"])
        client = gspread.authorize(credentials)

        # Open the sheet using its ID from your shared link
        sheet = client.open_by_key("1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY")
        worksheet = sheet.sheet1  # Use the first sheet/tab

        # Append the submitted data as a new row
        worksheet.append_row([name, email, message, filename, file_url])

        return True
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

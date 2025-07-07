import gspread
import streamlit as st
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

def log_to_google_sheets(name, email, message, timestamp, filename="User Requests"):
    try:
        # Use credentials from secrets.toml
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(credentials)

        # Open your sheet
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY/edit#gid=0")
        worksheet = sheet.sheet1

        # Add new row
        worksheet.append_row([name, email, message, timestamp])
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")

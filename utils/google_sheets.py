import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define the required Google Sheets scope
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

# Set the name of the Google Sheet and target tab
SHEET_NAME = "FidSync Submissions"
TAB_NAME = "Form Responses 1"

# Define the column headers and order
COLUMNS = ["Timestamp", "Name", "Email", "Type", "Message", "File"]

def log_to_google_sheets(name, email, message, timestamp, request_type="Other", file_url=""):
    try:
        # Load credentials from Streamlit secrets
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)

        # Connect to the sheet
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        # Check and write headers if not present
        existing_headers = worksheet.row_values(1)
        if existing_headers != COLUMNS:
            worksheet.resize(rows=1)
            worksheet.update("A1:F1", [COLUMNS])

        # Prepare row in correct column order
        row = [
            timestamp,
            name,
            email,
            request_type,
            message,
            file_url if file_url else ""
        ]

        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

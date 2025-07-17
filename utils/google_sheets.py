# utils/google_sheets.py

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import tempfile

def log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp):
    try:
        # Define scope and creds
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        client = gspread.authorize(creds)

        # Open the spreadsheet by title or key
        sheet = client.open("FidSync Requests").sheet1  # or use .worksheet("Sheet1")

        # Handle file upload: optionally log file name or save temporarily
        file_name = uploaded_file.name if uploaded_file else ""

        # Append row to the sheet
        sheet.append_row([timestamp, name, email, request_type, message, file_name])

        return True

    except Exception as e:
        print(f"Logging to Google Sheets failed: {e}")
        return False

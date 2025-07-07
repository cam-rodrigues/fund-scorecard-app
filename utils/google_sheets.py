import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# === Google Sheets Setup ===
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "FidSync Submissions"
TAB_NAME = "Form Responses 1"
COLUMNS = ["Timestamp", "Name", "Email", "Type", "Message", "File"]

# Set your Google login for admin view
ADMIN_EMAIL = "crods611@gmail.com"

def log_to_google_sheets(name, email, request_type, message, timestamp, uploaded_file=None):
    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        # Extract file name safely
        file_name = uploaded_file.name if uploaded_file else ""

        # Build row with guaranteed order
        row = [
            timestamp or "",
            name or "",
            email or "",
            request_type or "",
            message or "",
            file_name
        ]

        st.write("Logging this row to Google Sheets:", row)  # for debugging
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        st.error(f"⚠️ Failed to log to Google Sheets: {e}")
        return False


def render_admin_preview():
    """If the logged-in user is the admin, show the latest Google Sheets table."""
    if st.session_state.get("email") == ADMIN_EMAIL:
        try:
            creds_dict = st.secrets["gspread"]
            credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
            gc = gspread.authorize(credentials)
            sh = gc.open(SHEET_NAME)
            worksheet = sh.worksheet(TAB_NAME)
            data = worksheet.get_all_records()

            st.markdown("### ✅ Admin Preview: Latest Submissions")
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.warning(f"⚠️ Could not load admin preview: {e}")

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# === Google Sheets Setup ===
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "FidSync Submissions"
TAB_NAME = "Form Responses 1"
COLUMNS = ["Timestamp", "Name", "Email", "Type", "Message", "File"]

# 👤 Set your Google login for admin view
ADMIN_EMAIL = "crods611@gmail.com"

def log_to_google_sheets(name, email, message, timestamp, request_type="Other", file_url=""):
    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        # Write headers if missing
        existing_headers = worksheet.row_values(1)
        if existing_headers != COLUMNS:
            worksheet.resize(rows=1)
            worksheet.update("A1:F1", [COLUMNS])

        # Ensure row is in correct order
        row = [timestamp, name, email, request_type, message, file_url if file_url else ""]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

def render_admin_preview():
    try:
        user_email = st.experimental_user.email if hasattr(st, "experimental_user") and st.experimental_user else ""
        if user_email.lower() != ADMIN_EMAIL.lower():
            return  # Don't show anything for non-admins

        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)
        data = worksheet.get_all_records()

        if not data:
            st.info("No requests found.")
            return

        df = pd.DataFrame(data)

        st.markdown("### 👀 Admin Preview: All User Requests")
        request_types = df["Type"].unique()
        for r_type in request_types:
            with st.expander(f"📂 {r_type}"):
                st.dataframe(df[df["Type"] == r_type].sort_values("Timestamp", ascending=False), use_container_width=True)

    except Exception as e:
        st.warning(f"⚠️ Admin preview error: {e}")

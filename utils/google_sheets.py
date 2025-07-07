# --- utils/google_sheets.py ---

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

ADMIN_EMAIL = "your.email@example.com"  # <- Change this

# Connect to the Google Sheet
@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gspread"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY")
    return sheet.worksheet("Form Responses 1")

def log_to_google_sheets(name, email, message, timestamp, request_type):
    try:
        sheet = get_sheet()
        sheet.append_row([timestamp, name, email, request_type, message])
        return True
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

def render_admin_preview():
    user = st.user.get("email", "")  # For Streamlit Community Cloud
    if user != ADMIN_EMAIL:
        return

    st.markdown("---")
    st.markdown("### 🔒 Admin Preview")
    try:
        sheet = get_sheet()
        data = sheet.get_all_records()
        if not data:
            st.info("No submissions yet.")
            return

        df = pd.DataFrame(data)

        # Optional: Group by type
        with st.expander("Group by Request Type"):
            grouped = df.groupby("Request Type").size()
            st.write(grouped)

        # Optional: Sort by time
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.sort_values("Timestamp", ascending=False)

        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load admin preview: {e}")

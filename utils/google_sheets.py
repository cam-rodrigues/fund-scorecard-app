import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    set_frozen, format_cell_range, CellFormat,
    Color, TextFormat, set_column_width
)
import datetime

# Define the scope for Sheets + Drive access
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate using the service account info from Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["gspread"], scopes=SCOPE
)
gc = gspread.authorize(creds)

# Spreadsheet and sheet setup
SPREADSHEET_ID = "1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY"
SHEET_NAME = "Sheet1"

# Admin email (set to your Google account email)
ADMIN_EMAIL = "crods611@gmail.com"

def log_to_google_sheets(name, email, message, timestamp, request_type="Other", file_link=""):
    try:
        sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

        # Append the new row
        sheet.append_row([timestamp, name, email, request_type, message, file_link])

        # Apply formatting only once (if not yet formatted)
        if sheet.acell("A1").value != "Timestamp":
            sheet.update("A1", [["Timestamp", "Name", "Email", "Type", "Message", "File"]])
            header_format = CellFormat(
                backgroundColor=Color(0.88, 0.88, 0.88),
                textFormat=TextFormat(bold=True),
            )
            format_cell_range(sheet, "A1:F1", header_format)
            set_frozen(sheet, rows=1)

        # Alternate row shading
        for i in range(2, sheet.row_count + 1):
            row_color = Color(1, 1, 1) if i % 2 == 0 else Color(0.97, 0.97, 0.97)
            format_cell_range(sheet, f"A{i}:F{i}", CellFormat(backgroundColor=row_color))

        # Auto column width
        for col in range(1, 7):
            set_column_width(sheet, col, 200)

        return True

    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

def render_admin_preview():
    user_email = st.experimental_user.email if hasattr(st.experimental_user, 'email') else None

    if user_email == ADMIN_EMAIL:
        st.markdown("---")
        st.markdown("### 🔒 Admin Preview")

        try:
            sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
            rows = sheet.get_all_records()

            # Sort by timestamp descending
            rows.sort(key=lambda x: x.get("Timestamp", ""), reverse=True)

            grouped = {}
            for row in rows:
                req_type = row.get("Type", "Other")
                grouped.setdefault(req_type, []).append(row)

            for group, entries in grouped.items():
                with st.expander(f"{group} ({len(entries)} requests)", expanded=False):
                    for entry in entries:
                        st.markdown(f"**{entry['Name']}** ({entry['Email']})  ")
                        st.markdown(f"*{entry['Timestamp']}*  ")
                        st.markdown(f"{entry['Message']}  ")
                        if entry.get("File"):
                            st.markdown(f"📎 {entry['File']}")
                        st.markdown("---")

        except Exception as e:
            st.error(f"Could not load admin preview: {e}")

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import (
    set_frozen, format_cell_range, CellFormat,
    Color, TextFormat, set_column_width
)

# Define the scope for Sheets + Drive access
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_ID = "1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY"

def log_to_google_sheets(name, email, message, timestamp):
    try:
        creds = ServiceAccountCredentials.from_service_account_info(st.secrets["gspread"], scopes=SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1

        # Add header if it's missing
        if not sheet.get_all_values():
            sheet.append_row(["Name", "Email", "Message", "Submitted At"])

        # Append new row
        sheet.append_row([name, email, message, timestamp])

        # --- Formatting ---
        fmt = CellFormat(
            backgroundColor=Color(0.95, 0.95, 0.95),
            textFormat=TextFormat(bold=True),
        )
        format_cell_range(sheet, "A1:D1", fmt)  # bold header

        # Freeze first row
        set_frozen(sheet, rows=1)

        # Set alternating row colors (light gray)
        alt_fmt = CellFormat(backgroundColor=Color(0.98, 0.98, 0.98))
        all_rows = len(sheet.get_all_values())
        for r in range(2, all_rows + 1):
            if r % 2 == 0:
                format_cell_range(sheet, f"A{r}:D{r}", alt_fmt)

        # Resize columns
        set_column_width(sheet, 'A', 150)
        set_column_width(sheet, 'B', 250)
        set_column_width(sheet, 'C', 400)
        set_column_width(sheet, 'D', 200)

        return True
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")
        return False

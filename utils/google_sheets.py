def log_to_google_sheets(name, email, request_type, message, timestamp, uploaded_file=None):
    try:
        creds_dict = st.secrets["gspread"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.worksheet(TAB_NAME)

        file_name = uploaded_file.name if uploaded_file else ""

        row = [
            timestamp or "",
            name or "",
            email or "",
            request_type or "",
            message or "",
            file_name
        ]

        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        st.error(f"⚠️ Failed to log to Google Sheets: {e}")
        return False

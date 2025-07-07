import streamlit as st
from datetime import datetime
from utils.google_sheets import log_to_google_sheets, render_admin_preview

def run():
    st.title("📬 Submit a Request")
    with st.form("user_request_form"):
        req_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "Other"])
        message = st.text_area("Your Message", height=150)
        uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

        submitted = st.form_submit_button("Submit Request")
        if submitted:
            name = st.session_state.get("name", "Anonymous")
            email = st.session_state.get("email", "anonymous@example.com")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            success = log_to_google_sheets(name, email, req_type, message, uploaded_file, timestamp)

            if success:
                st.success("✅ Your request has been saved.")
                st.write("Logging this row to Google Sheets:")
                st.json([timestamp, name, email, req_type, message, uploaded_file.name if uploaded_file else ""])
            else:
                st.error("❌ Something went wrong while saving your request.")

    render_admin_preview()

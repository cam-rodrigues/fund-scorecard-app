import streamlit as st
from datetime import datetime
from utils.google_sheets import log_to_google_sheets, render_admin_preview

def run():
    st.title("Submit a Request")

    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    request_type = st.selectbox("Type of Request", ["Bug Report", "Feature Request", "Other"])
    message = st.text_area("Your Message")
    uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

    if st.button("Submit Request"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success("✅ Your request has been saved.")

        success = log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp)

        if success:
            st.success("✅ Also logged to Google Sheets!")
        else:
            st.error("❌ Logging failed.")

    render_admin_preview()

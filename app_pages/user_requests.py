import streamlit as st
from datetime import datetime
from utils.google_sheets import log_to_google_sheets, render_admin_preview


def run():
    st.title("📬 Submit a Request")

    st.markdown("""
        Use the form below to request features, report bugs, or send feedback. If you're an admin, you'll also see incoming requests.
    """)

    with st.form("user_request_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name")
        with col2:
            email = st.text_input("Your Email")

        request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "Other"])
        message = st.text_area("Your Message", height=150)
        uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

        submitted = st.form_submit_button("Submit Request")

        if submitted:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            success = log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp)

            if success:
                st.success("✅ Your request has been saved.")
                st.write("Logging this row to Google Sheets:")
                st.json([timestamp, name, email, request_type, message, uploaded_file.name if uploaded_file else ""])
            else:
                st.error("❌ Something went wrong while saving your request.")

    st.markdown("---")
    render_admin_preview()

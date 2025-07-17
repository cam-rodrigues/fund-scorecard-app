import streamlit as st
from datetime import datetime
from utils/google_sheets.py import log_to_google_sheets

def run():
    st.title("Submit a Request")

    st.markdown("""
        Use the form below to request features, report bugs, or ask questions.
    """)

    with st.form("user_request_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name")
        with col2:
            email = st.text_input("Your Email")

        request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "General Question", "Other"])
        message = st.text_area("Your Message", height=150)
        uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

        submitted = st.form_submit_button("Submit Request")

    if submitted:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp)

        if success:
            st.success("✅ Your request has been saved.")

            st.markdown("#### Submission Details:")
            st.markdown(f"- **Timestamp:** {timestamp}")
            st.markdown(f"- **Name:** {name}")
            st.markdown(f"- **Email:** {email}")
            st.markdown(f"- **Type:** {request_type}")
            st.markdown(f"- **Message:** {message if message else '*None*'}")
            st.markdown(f"- **File:** {uploaded_file.name if uploaded_file else '*None*'}")

        else:
            st.error("❌ There was an error logging your request. Please try again or contact support.")

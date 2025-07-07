import streamlit as st
import datetime
import os
from utils.google_sheets import log_to_google_sheets, render_admin_preview

def run():
    st.markdown("## 📝 User Feedback & Feature Requests")

    st.markdown("""
    Have a suggestion, found a bug, or want to request a new feature?

    Fill out the form below to help improve **FidSync**.
    """)

    st.divider()

    st.markdown("### Submit a Request")

    name = st.text_input("Your Name")
    email = st.text_input("Email Address", placeholder="your.email@example.com")
    request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "UI Improvement", "Other"])
    message = st.text_area("Your Message", height=150)
    uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

    if st.button("Submit Request"):
        if not name or not email or not message:
            st.error("⚠️ Please fill in all required fields.")
        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save request to local folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            requests_dir = os.path.abspath(os.path.join(base_dir, "..", "requests"))
            os.makedirs(requests_dir, exist_ok=True)

            request_path = os.path.join(requests_dir, f"request_{timestamp.replace(':', '_').replace(' ', '_')}.txt")
            with open(request_path, "w") as f:
                f.write(f"Name: {name}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Request Type: {request_type}\n")
                f.write(f"Message:\n{message}\n")
                f.write(f"Submitted At: {timestamp}\n")

            if uploaded_file:
                file_ext = os.path.splitext(uploaded_file.name)[-1]
                file_path = os.path.join(requests_dir, f"attachment_{timestamp.replace(':', '_').replace(' ', '_')}{file_ext}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())

            st.success("✅ Your request has been saved.")

            log_success = log_to_google_sheets(name, email, request_type, message, timestamp)
            if log_success:
                st.success("✅ Also logged to Google Sheets!")
            else:
                st.error("⚠️ Failed to log to Google Sheets. Please try again later.")

    st.divider()
    render_admin_preview()

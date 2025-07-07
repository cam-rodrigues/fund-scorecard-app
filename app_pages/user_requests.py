import streamlit as st
from utils.google_sheets import log_to_google_sheets, render_admin_preview

st.set_page_config(page_title="User Requests", layout="wide")

st.title("📨 Submit a Feature Request, Bug Report, or Question")
st.markdown(
    "Let us know how we can improve FidSync. Submissions are logged to our team’s Google Sheet."
)

with st.form("request_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "Other"])
    message = st.text_area("Your Message", height=150)
    uploaded_file = st.file_uploader(
        "Optional Screenshot or Supporting File",
        type=["png", "jpg", "jpeg", "pdf", "txt"],
    )

    submitted = st.form_submit_button("Submit Request")

if submitted:
    if not name or not email or not message:
        st.warning("Please fill out your name, email, and message.")
    else:
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        success = log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp)

        if success:
            st.success("✅ Your request has been saved.")
        else:
            st.error("❌ Failed to log to Google Sheets. Please try again later.")

# Optional Admin view (shows full request table if logged in as admin)
render_admin_preview()

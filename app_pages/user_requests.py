import streamlit as st
from utils.google_sheets import log_to_google_sheets, is_admin_user
from datetime import datetime

st.title("User Requests")

st.markdown("Use the form below to submit feature requests, bug reports, or general questions.")

# --- Input form ---
with st.form("user_request_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", max_chars=50)
    with col2:
        email = st.text_input("Your Email", max_chars=100)

    request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "Other"])
    message = st.text_area("Your Message", height=150)
    uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

    submit = st.form_submit_button("Submit Request")

# --- Submission logic ---
if submit:
    if not name or not email or not message:
        st.error("Please fill out all required fields: Name, Email, and Message.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = log_to_google_sheets(name, email, request_type, message, uploaded_file, timestamp)

        if success:
            st.success("✅ Your request has been saved.")
        else:
            st.error("❌ Failed to log your request. Please try again later.")

# --- Admin View ---
if is_admin_user():
    st.markdown("---")
    st.subheader("📊 Admin Submission Viewer (Live Preview)")
    try:
        from utils.google_sheets import get_all_submissions
        df = get_all_submissions()
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load admin preview: {e}")

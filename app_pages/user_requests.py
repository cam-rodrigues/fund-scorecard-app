import streamlit as st
from datetime import datetime
from utils.google_sheets import log_to_google_sheets, render_admin_preview

st.set_page_config(page_title="User Requests", layout="wide")

# === Visual Styling ===
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    label, textarea, input, select {
        font-size: 0.95rem;
    }
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 8px 12px;
        border: 1px solid #ccc;
    }
    .stFileUploader > div {
        background-color: #f1f5f9;
        border-radius: 10px;
        border: 1.5px dashed #ccc !important;
        padding: 1rem;
    }
    .stButton > button {
        background-color: #2b6cb0;
        color: white;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border: none;
        border-radius: 8px;
        transition: 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #1a4b84;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# === Page Header ===
st.title("📬 Submit a Request")
st.markdown("Use this form to request a feature, report a bug, or send feedback.")

# === Form Fields ===
name = st.text_input("Your Name")
email = st.text_input("Your Email")
request_type = st.selectbox("Type of Request", ["Bug Report", "Feature Request", "Other"])
message = st.text_area("Your Message", height=150)
uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

# === Submission ===
if st.button("Submit Request"):
    if not name or not email or not request_type:
        st.warning("Please complete all required fields.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = log_to_google_sheets(
            name=name,
            email=email,
            request_type=request_type,
            message=message,
            uploaded_file=uploaded_file,
            timestamp=timestamp
        )
        if success:
            st.success("✅ Your request has been saved.")
        else:
            st.error("❌ Failed to log to Google Sheets. Please try again later.")

# === Admin Table Preview (hidden unless email matches ADMIN_EMAIL) ===
render_admin_preview()

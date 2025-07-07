import streamlit as st
from datetime import datetime
from utils.google_sheets import log_to_google_sheets, render_admin_preview

# === Page Config ===
st.set_page_config(page_title="User Requests", layout="wide")

# === Optional Custom Font ===
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# === Custom Styling ===
st.markdown("""
<style>
    .stButton>button {
        background-color: #2B6CB0;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 0.5rem;
        transition: background 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1A4E8A;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>textarea {
        border-radius: 0.5rem;
        padding: 0.5rem;
    }
    .stFileUploader>div>div {
        border: 1px dashed #ccc !important;
        border-radius: 0.75rem;
        background-color: #F7FAFC;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# === Page Title ===
st.title("📬 Submit a Request")

# === Input Fields Layout ===
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
    with col2:
        request_type = st.selectbox("Type of Request", ["Bug Report", "Feature Request", "Other"])
        uploaded_file = st.file_uploader(
            "Optional Screenshot or Supporting File",
            type=["png", "jpg", "jpeg", "pdf", "txt"]
        )

message = st.text_area("Your Message", height=150)

# === Submission Button ===
if st.button("Submit Request"):
    if not name or not email or not request_type:
        st.warning("Please fill in all required fields.")
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

# === Hidden Admin Preview ===
render_admin_preview()

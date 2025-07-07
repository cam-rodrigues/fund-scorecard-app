import streamlit as st
import datetime
import os

def run():
    st.markdown("## User Feedback & Feature Requests")

    st.markdown("""
        Have a suggestion, found a bug, or want to request a new feature?

        Fill out the form below to help improve FidSync.
    """)

    st.markdown("### Submit a Request")

    # --- Form fields ---
    name = st.text_input("Your Name")
    email = st.text_input("Email Address", placeholder="your.email@example.com")
    request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "UI Improvement", "Other"])
    message = st.text_area("Your Message", height=150)
    uploaded_file = st.file_uploader("Optional Screenshot or Supporting File", type=["png", "jpg", "jpeg", "pdf", "txt"])

    # --- Submit button ---
    if st.button("Submit Request"):
        if not name or not email or not message:
            st.error("Please fill in all required fields.")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            requests_dir = os.path.abspath(os.path.join(base_dir, "..", "requests"))

            try:
                os.makedirs(requests_dir, exist_ok=True)
            except Exception as e:
                st.error(f"❌ Failed to create `requests/` folder: {e}")
                return

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            request_path = os.path.join(requests_dir, f"request_{timestamp}.txt")

            try:
                with open(request_path, "w") as f:
                    f.write(f"Name: {name}\n")
                    f.write(f"Email: {email}\n")
                    f.write(f"Request Type: {request_type}\n")
                    f.write(f"Message:\n{message}\n")
                    f.write(f"Submitted At: {timestamp}\n")
                st.success("✅ Your request has been submitted.")
            except Exception as e:
                st.error(f"❌ Failed to save request: {e}")

            if uploaded_file:
                try:
                    file_ext = os.path.splitext(uploaded_file.name)[-1]
                    file_save_path = os.path.join(requests_dir, f"attachment_{timestamp}{file_ext}")
                    with open(file_save_path, "wb") as f:
                        f.write(uploaded_file.read())
                    st.success(f"📎 Attachment saved as `{file_save_path}`")
                except Exception as e:
                    st.error(f"❌ Failed to save attachment: {e}")

    # ✅ Link to the shared sheet
    st.markdown("📄 [View all submissions in Google Sheets](https://docs.google.com/spreadsheets/d/1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY)")

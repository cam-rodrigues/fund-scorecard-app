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
            st.success("✅ Your request has been submitted. Thank you!")
            st.markdown("---")
            st.markdown("### Preview")
            st.markdown(f"**Name:** {name}")
            st.markdown(f"**Email:** {email}")
            st.markdown(f"**Request Type:** {request_type}")
            st.markdown(f"**Message:**\n{message}")
            st.markdown(f"**Submitted At:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if uploaded_file:
                file_ext = os.path.splitext(uploaded_file.name)[-1]
                st.markdown(f"**Uploaded File:** `{uploaded_file.name}`")
                
                if file_ext.lower() in [".png", ".jpg", ".jpeg"]:
                    st.image(uploaded_file, caption="Screenshot Preview", use_column_width=True)
                else:
                    st.info("File uploaded successfully.")


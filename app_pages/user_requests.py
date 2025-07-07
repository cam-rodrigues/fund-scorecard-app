import streamlit as st
import datetime

def run():
    st.markdown("## User Feedback & Feature Requests")

    st.markdown("""
        Have a suggestion or found a bug? Let us know what would make FidSync better.

        Fill out the form below to submit your request.
    """)

    # --- Form layout ---
    with st.form("request_form"):
        name = st.text_input("Your Name")

        email_name = st.text_input("Email (name only, e.g. cam.rodrigues)")
        email_domain = st.selectbox(
            "Email Domain",
            ["@procyon.net", "@gmail.com", "@outlook.com", "@yahoo.com", "@icloud.com"]
        )
        full_email = f"{email_name}{email_domain}"

        request_type = st.selectbox(
            "Type of Request",
            ["Feature Request", "Bug Report", "UI Improvement", "Other"]
        )

        message = st.text_area("Your Message", height=150)

        submitted = st.form_submit_button("Submit Request")

    # --- Submission handling ---
    if submitted:
        if not name or not email_name or not message:
            st.error("Please fill in all required fields.")
        else:
            st.success("✅ Your request has been submitted. Thank you!")
            st.markdown("---")
            st.markdown("### Preview")
            st.markdown(f"**Name:** {name}")
            st.markdown(f"**Email:** {full_email}")
            st.markdown(f"**Request Type:** {request_type}")
            st.markdown(f"**Message:**\n{message}")
            st.markdown(f"**Submitted At:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

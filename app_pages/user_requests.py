import streamlit as st
import datetime

def run():
    st.markdown("## User Feedback & Feature Requests")

    st.markdown("""
        Have a suggestion or found a bug? Let us know what would make FidSync better.
    """)

    st.markdown("### Submit a Request")

    # --- State variables ---
    if "confirmed_email" not in st.session_state:
        st.session_state.confirmed_email = ""

    # --- Email input with simulated dropdown ---
    raw_email = st.text_input("Email Address", placeholder="e.g. cam.rodrigues@")

    # Only show suggestions if @ is present but not completed
    email_domains = ["gmail.com", "procyon.net", "outlook.com", "yahoo.com", "icloud.com"]
    suggestion_shown = False

    if "@" in raw_email and "." not in raw_email.split("@")[-1]:
        name_part = raw_email.split("@")[0]
        st.markdown("#### Choose a domain:")
        col1, col2, col3 = st.columns(3)
        for i, domain in enumerate(email_domains):
            col = [col1, col2, col3][i % 3]
            if col.button(f"{name_part}@{domain}"):
                st.session_state.confirmed_email = f"{name_part}@{domain}"

        suggestion_shown = True

    elif "." in raw_email.split("@")[-1]:
        st.session_state.confirmed_email = raw_email

    # Final email
    final_email = st.session_state.confirmed_email

    # --- Other form fields ---
    name = st.text_input("Your Name")
    request_type = st.selectbox("Type of Request", ["Feature Request", "Bug Report", "UI Improvement", "Other"])
    message = st.text_area("Your Message", height=150)

    # --- Submit button ---
    if st.button("Submit Request"):
        if not name or not final_email or not message:
            st.error("Please fill in all required fields.")
        else:
            st.success("✅ Your request has been submitted. Thank you!")
            st.markdown("---")
            st.markdown("### Preview")
            st.markdown(f"**Name:** {name}")
            st.markdown(f"**Email:** {final_email}")
            st.markdown(f"**Request Type:** {request_type}")
            st.markdown(f"**Message:**\n{message}")
            st.markdown(f"**Submitted At:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

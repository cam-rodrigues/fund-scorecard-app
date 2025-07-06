import streamlit as st
import pandas as pd
import datetime
import os

def run():
    st.title("Submit a Request")
    st.markdown(
        "Use this form to ask for help, suggest improvements, or report any issues with FidSync."
    )

    with st.form("request_form", clear_on_submit=True):
        email = st.text_input("Your work email", placeholder="you@firm.com")
        request_text = st.text_area("What do you need FidSync to do?", height=200)
        submitted = st.form_submit_button("Send Request")

    if submitted:
        if not request_text.strip():
            st.warning("Please enter a request before submitting.")
        elif "@" not in email or "." not in email:
            st.warning("Please enter a valid email address.")
        else:
            request_entry = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "email": email.strip(),
                "request": request_text.strip()
            }

            # Save to CSV
            csv_path = "user_requests_log.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df = pd.concat([df, pd.DataFrame([request_entry])], ignore_index=True)
            else:
                df = pd.DataFrame([request_entry])

            df.to_csv(csv_path, index=False)

            st.success("✅ Your request was submitted. Thank you!")

import streamlit as st
from utils import request_store


def show():
    """Display the user request submission form."""
    st.title("Submit a Request")
    st.write(
        "Have an idea or need a new feature? Let us know how FidSync can help you."
    )

    with st.form("request_form"):
        request_text = st.text_area("Describe what you need the program to do", height=200)
        contact_email = st.text_input("Your email (optional)")
        submitted = st.form_submit_button("Send Request")

    if submitted:
        if request_text.strip():
            request_store.save_request(request_text, contact_email)
            st.success("Thank you for your feedback!")
        else:
            st.warning("Please enter a description before submitting.")


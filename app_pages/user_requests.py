import streamlit as st

def run():
    st.header("📬 Submit a Request")
    st.markdown("Use this form to request a new feature, tool, or report.")

    with st.form("request_form"):
        email = st.text_input("Your Email")
        request = st.text_area("Your Request")

        submitted = st.form_submit_button("Submit")

    if submitted:
        if not email or not request:
            st.warning("Please fill out both fields.")
        else:
            st.success("✅ Request submitted successfully!")
            # Here you'd log it, email it, or store it
            st.write("We'll follow up at:", email)

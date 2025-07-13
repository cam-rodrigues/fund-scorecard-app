import streamlit as st
from datetime import datetime


def run():
    st.set_page_config(page_title="Meeting Minutes Generator", layout="centered")
    st.title("🧾 Meeting Minutes Generator")

    st.markdown("Fill in key details below to generate a clean meeting summary.")
    st.markdown("---")

    meeting_title = st.text_input("Meeting Title", placeholder="e.g. Investment Strategy Review")
    meeting_date = st.date_input("Date of Meeting", value=datetime.today())
    attendees = st.text_area("Attendees (comma-separated)", placeholder="e.g. Alice, Bob, Sarah")
    topics = st.text_area("Topics Discussed", placeholder="Brief bullet points or paragraph")
    action_items = st.text_area("Action Items / Next Steps", placeholder="Who is doing what and by when")

    if st.button("Generate Summary"):
        summary = f"""
        Meeting Title: {meeting_title or 'N/A'}
        Date: {meeting_date.strftime('%B %d, %Y')}
        Attendees: {attendees or 'N/A'}

        Topics Discussed:
        {topics or 'N/A'}

        Action Items:
        {action_items or 'N/A'}
        """

        st.markdown("---")
        st.subheader("📋 Generated Minutes")
        st.text(summary.strip())

        st.download_button("Download as .txt", data=summary.strip(), file_name="meeting_minutes.txt")
        st.success("Ready to copy, download, or paste into an email!")

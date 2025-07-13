import streamlit as st
from datetime import datetime
import pyperclip

def run():
    st.set_page_config(page_title="Meeting Minutes Generator", layout="centered")
    st.title("Meeting Minutes Generator")

    st.markdown("Fill in the meeting details below to create a polished summary.")
    st.markdown("---")

    meeting_title = st.text_input("Meeting Title", placeholder="e.g. Investment Strategy Review")
    meeting_date = st.date_input("Date", value=datetime.today())
    meeting_time = st.time_input("Time (optional)")
    attendees = st.text_area("Attendees (comma-separated)", placeholder="e.g. Alice, Bob, Sarah")
    topics = st.text_area("Topics Discussed", placeholder="Bullet points or a summary paragraph")
    decisions = st.text_area("Decisions Made", placeholder="Any final decisions agreed upon")
    action_items = st.text_area("Action Items / Next Steps", placeholder="Who is doing what and by when")

    if st.button("Generate Minutes"):
        if not meeting_title and not attendees and not topics and not action_items:
            st.error("Please fill out at least a few fields to generate minutes.")
        else:
            time_str = meeting_time.strftime('%I:%M %p') if meeting_time else ""
            summary = f"""
Meeting Minutes
===============

**Meeting Title:** {meeting_title or 'N/A'}
**Date:** {meeting_date.strftime('%B %d, %Y')}{f" at {time_str}" if time_str else ''}
**Attendees:** {attendees or 'N/A'}

---

### Topics Discussed
{topics or 'N/A'}

### Decisions Made
{decisions or 'N/A'}

### Action Items / Next Steps
{action_items or 'N/A'}
"""

            st.markdown("---")
            st.subheader("Generated Minutes")
            st.text_area("Meeting Summary", value=summary.strip(), height=300)

            st.download_button("Download as .txt", data=summary.strip(), file_name="meeting_minutes.txt")
            st.code(summary.strip(), language='markdown')
            st.success("You can now download, copy, or paste your meeting minutes anywhere.")

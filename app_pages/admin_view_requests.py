import streamlit as st
import os
import datetime

def run():
    st.title("📂 Admin: View Submitted Requests")

    requests_dir = "requests"
    if not os.path.exists(requests_dir):
        st.warning("No requests have been submitted yet.")
        return

    request_files = sorted([f for f in os.listdir(requests_dir) if f.endswith(".txt")], reverse=True)

    if not request_files:
        st.info("No requests found.")
        return

    for req_file in request_files:
        req_path = os.path.join(requests_dir, req_file)
        with open(req_path, "r") as f:
            lines = f.read()

        timestamp = req_file.replace("request_", "").replace(".txt", "")
        st.markdown("---")
        st.subheader(f"📝 Submission: {timestamp}")
        st.text(lines)

        # Check for corresponding attachment
        attachment_prefix = f"attachment_{timestamp}"
        attachments = [f for f in os.listdir(requests_dir) if f.startswith(attachment_prefix)]

        if attachments:
            for attachment in attachments:
                ext = os.path.splitext(attachment)[-1].lower()
                filepath = os.path.join(requests_dir, attachment)
                st.markdown(f"**Attachment:** `{attachment}`")

                if ext in [".png", ".jpg", ".jpeg"]:
                    st.image(filepath, caption=attachment, use_column_width=True)
                elif ext == ".txt":
                    with open(filepath, "r") as f:
                        st.code(f.read(), language="text")
                elif ext == ".pdf":
                    st.markdown(f"[📄 Open PDF]({filepath})")

    st.markdown("---")
    st.caption("End of request list.")

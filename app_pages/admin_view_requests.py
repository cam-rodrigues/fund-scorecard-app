import streamlit as st
import os

def run():
    st.title("📂 Admin: View Submitted Requests")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    requests_dir = os.path.abspath(os.path.join(base_dir, "..", "requests"))
    os.makedirs(requests_dir, exist_ok=True)

    request_files = sorted([
        f for f in os.listdir(requests_dir)
        if f.startswith("request_") and f.endswith(".txt")
    ], reverse=True)

    if not request_files:
        st.info("📭 No submissions yet.")
        return

    for req_file in request_files:
        req_path = os.path.join(requests_dir, req_file)
        with open(req_path, "r") as f:
            lines = f.read()

        timestamp = req_file.replace("request_", "").replace(".txt", "")
        st.markdown("---")
        st.subheader(f"📝 Submission: {timestamp}")
        st.text(lines)

        attachment_prefix = f"attachment_{timestamp}"
        attachments = [
            f for f in os.listdir(requests_dir)
            if f.startswith(attachment_prefix)
        ]

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

    # ✅ Link to the shared sheet
    st.markdown("📄 [Open Submission Sheet](https://docs.google.com/spreadsheets/d/1NByeYVPB0oX8i2ct9cEt3cQat7Dyp-uZxBbw17QiQeY)")

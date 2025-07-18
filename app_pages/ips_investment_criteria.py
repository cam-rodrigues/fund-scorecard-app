import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 8: Fund Scorecard Structured Extraction", layout="wide")
    st.title("Step 8: Structured Investment Option + Metrics Extraction")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step8_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # --- Extract scorecard section page number (from TOC) ---
            toc_text = pdf.pages[1].extract_text()
            def find_page(section_title):
                for line in toc_text.split("\n"):
                    if section_title in line:
                        match = re.search(r"(\d+)$", line)
                        return int(match.group(1)) if match else None
                return None
            scorecard_page = find_page("Fund Scorecard")
            if not scorecard_page:
                st.error("❌ Could not find Fund Scorecard page.")
                return

            # --- Extract Investment Options + Metrics ---
            fund_blocks = []
            lines_buffer = []

            # Read all text from Fund Scorecard pages
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text:
                    continue
                lines_buffer.extend(text.split("\n"))

            # Clean up buffer
            cleaned_lines = []
            skip_keywords = [
                "Criteria Threshold",
                "Portfolio manager or management team",
                "must outperform its benchmark",
                "must be in the top 50%", "must be in the top 10%",
                "must be greater than 95%",
                "Created with mpi Stylus"
            ]

            for line in lines_buffer:
                if not any(kw in line for kw in skip_keywords):
                    cleaned_lines.append(line.strip())

            # Parse blocks based on "Manager Tenure" anchor
            i = 0
            while i < len(cleaned_lines):
                if "Manager Tenure" in cleaned_lines[i]:
                    if i == 0:
                        i += 1
                        continue
                    fund_name = cleaned_lines[i - 1].strip()
                    metrics_block = cleaned_lines[i:i + 14]
                    parsed_metrics = []

                    for m_line in metrics_block:
                        m = re.match(r"(.+?)\s+(Pass|Review)\s+(.*)", m_line)
                        if m:
                            metric_name = m.group(1).strip()
                            status = m.group(2).strip()
                            reason = m.group(3).strip()
                            parsed_metrics.append((metric_name, status, reason))

                    fund_blocks.append({
                        "name": fund_name,
                        "metrics": parsed_metrics
                    })

                    i += 14  # skip the block
                else:
                    i += 1

            # --- Display results ---
            st.subheader("Extracted Investment Options")
            for block in fund_blocks:
                st.markdown(f"### {block['name']}")
                for metric in block["metrics"]:
                    st.markdown(f"- **{metric[0]}** → {metric[1]} — {metric[2]}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")

import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 9: Fund Match Check", layout="wide")
    st.title("Step 9: Check Number of Investment Options")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step9_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # --- Extract Total Options from page 1 ---
            page1_text = pdf.pages[0].extract_text()
            total_match = re.search(r"Total Options:\s*(\d+)", page1_text or "")
            declared_total = int(total_match.group(1)) if total_match else None

            # --- Extract Fund Scorecard starting page from TOC ---
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

            # --- Extract Investment Options from scorecard section ---
            lines_buffer = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text:
                    continue
                lines_buffer.extend(text.split("\n"))

            # Step 8 cleanup: remove threshold/boilerplate definitions
            cleaned_lines = []
            skip_keywords = [
                "Criteria Threshold", "Portfolio manager", "must outperform", "must be in the top",
                "must be greater than", "Created with mpi Stylus"
            ]
            for line in lines_buffer:
                if not any(kw in line for kw in skip_keywords):
                    cleaned_lines.append(line.strip())

            # Step 8 logic: parse funds
            fund_blocks = []
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

                    i += 14
                else:
                    i += 1

            # --- Step 9: Compare counts ---
            extracted_count = len(fund_blocks)

            st.subheader("Double Check: Investment Option Count")
            st.markdown(f"- Declared in PDF (Page 1): **{declared_total if declared_total else 'Not found'}**")
            st.markdown(f"- Extracted from Scorecard: **{extracted_count}**")

            if declared_total is None:
                st.warning("⚠️ Could not find Total Options on Page 1.")
            elif declared_total == extracted_count:
                st.success("✅ Number of Investment Options matches.")
            else:
                st.error("❌ Mismatch: PDF says one number, but we extracted a different number.")

            # Optional display of the fund names
            st.subheader("Extracted Fund Names")
            for block in fund_blocks:
                st.markdown(f"- {block['name']}")

    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")

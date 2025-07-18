import streamlit as st
import pdfplumber
import re
from datetime import datetime

def run():
    st.set_page_config(page_title="Step 4: Table of Contents", layout="wide")
    st.title("Step 4: Table of Contents – Page Numbers")

    # Step 1 – Upload PDF
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step4_upload")

    if uploaded_file:
        st.success("✅ MPI PDF successfully uploaded.")

        try:
            with pdfplumber.open(uploaded_file) as pdf:
                # Page 1 – Context
                raw_text = pdf.pages[0].extract_text()
                cleaned_text = re.sub(
                    r"For Plan Sponsor use only.*?Created with mpi Stylus\.", "", raw_text, flags=re.DOTALL
                )

                # Extract Time Period (Q1–Q4)
                quarter_match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', cleaned_text)
                if quarter_match:
                    date_str = quarter_match.group(0)
                    month_day = date_str[:5]
                    year = "20" + date_str[-2:]
                    quarter_map = {"3/31": "Q1", "6/30": "Q2", "9/30": "Q3", "12/31": "Q4"}
                    quarter = quarter_map.get(month_day, "Unknown") + " " + year
                else:
                    quarter = "Not found"

                # Page 2 – Table of Contents
                toc_text = pdf.pages[1].extract_text()
                st.subheader("Raw Table of Contents (Page 2)")
                st.text(toc_text)

                # Find section pages
                def find_page_number(section_title, toc_text):
                    pattern = rf"{re.escape(section_title)}[\s\.]*?(\d+)"
                    match = re.search(pattern, toc_text)
                    return int(match.group(1)) if match else None

                perf_page = find_page_number("Fund Performance: Current vs. Proposed Comparison", toc_text)
                scorecard_page = find_page_number("Fund Scorecard", toc_text)

                # Display extracted results
                st.subheader("Extracted Sections")
                st.markdown(f"**Time Period:** {quarter}")
                st.markdown(f"**Fund Performance Section Page:** {perf_page if perf_page else 'Not found'}")
                st.markdown(f"**Fund Scorecard Section Page:** {scorecard_page if scorecard_page else 'Not found'}")

        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")

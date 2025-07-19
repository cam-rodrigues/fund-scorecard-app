import streamlit as st
import pdfplumber
import re
import pandas as pd
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Steps: Convert & Cleanup", layout="wide")
    st.title("Step 3: Convert & Clean Page 1 Data")

    # Step 1 – Upload PDF
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step3_upload")

    if uploaded_file:
        st.success("✅ MPI PDF successfully uploaded.")

        try:
            with pdfplumber.open(uploaded_file) as pdf:
                raw_text = pdf.pages[0].extract_text()
                
    # Step 3 – Remove boilerplate footer line
                cleaned_text = re.sub(
                    r"For Plan Sponsor use only.*?Created with mpi Stylus\.", "", raw_text, flags=re.DOTALL
                )

                st.subheader("Cleaned Text from Page 1")
                st.text(cleaned_text)

    # Step 2 – Extract Quarter-End Date
                quarter_match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', cleaned_text)
                if quarter_match:
                    date_str = quarter_match.group(0)
                    month_day = date_str[:5]
                    year = "20" + date_str[-2:]

                    quarter_map = {
                        "3/31": "Q1",
                        "6/30": "Q2",
                        "9/30": "Q3",
                        "12/31": "Q4"
                    }

                    quarter = quarter_map.get(date_str[:date_str.rfind("/")], "Unknown") + " " + date_str[-4:]
                else:
                    quarter = "Not found"

                # Extract Total Options
                total_match = re.search(r"Total Options:\s*(\d+)", cleaned_text)
                total_options = total_match.group(1) if total_match else "Not found"

                # Extract Prepared For
                prepared_for_match = re.search(r"Prepared For:\s*\n(.+)", cleaned_text)
                prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else "Not found"

                # Extract Prepared By
                prepared_by_match = re.search(r"Prepared By:\s*\n(.+)", cleaned_text)
                prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else "Not found"

                # Display results
                st.subheader("Extracted Page 1 Summary")
                st.markdown(f"**Time Period:** {quarter}")
                st.markdown(f"**Total Options:** {total_options}")
                st.markdown(f"**Prepared For:** {prepared_for}")
                st.markdown(f"**Prepared By:** {prepared_by}")

    # Step 4 - Table of Contents
    # Page 2 – Table of Contents
                toc_text = pdf.pages[1].extract_text()
                
    # Step 5/6 – Remove irrelevant TOC lines
                lines = toc_text.split("\n")
                ignore_keywords = [
                    "Calendar Year", "Risk Analysis", "Style Box", "Returns Correlation",
                    "Fund Factsheets", "Definitions & Disclosures", "Past performance",
                    "Total Options", "http://", quarter.replace(" ", "/"),
                    "shares may be worth more/less than original cost",
                    "Returns assume reinvestment of all distributions at NAV"
                ]

                cleaned_toc_lines = [
                    line for line in lines
                    if not any(kw in line for kw in ignore_keywords)
                ]

                # Step 5 – Extract relevant section page numbers
                def find_page(section_title, toc_lines):
                    for line in toc_lines:
                        if section_title in line:
                            match = re.search(r"(\d+)$", line)
                            return int(match.group(1)) if match else None
                    return None

                perf_page = find_page("Fund Performance: Current vs. Proposed Comparison", cleaned_toc_lines)
                scorecard_page = find_page("Fund Scorecard", cleaned_toc_lines)

                # Display cleaned TOC + section page number
                st.subheader("Cleaned Table of Contents")
                for line in cleaned_toc_lines:
                    st.markdown(f"- {line}")

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

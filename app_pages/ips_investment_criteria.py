import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 5: Clean TOC", layout="wide")
    st.title("Step 5: Clean and Parse Table of Contents")

    # Step 1 – Upload
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step5_upload")

    if uploaded_file:
        st.success("✅ MPI PDF uploaded.")

        try:
            with pdfplumber.open(uploaded_file) as pdf:
                # Step 2 – Page 1 Cleanup
                page1 = pdf.pages[0].extract_text()
                page1_clean = re.sub(
                    r"For Plan Sponsor use only.*?Created with mpi Stylus\.", "", page1 or "", flags=re.DOTALL
                )

                # Step 3 – Time Period
                date_match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', page1_clean)
                if date_match:
                    date_str = date_match.group(0)
                    quarter_map = {"3/31": "Q1", "6/30": "Q2", "9/30": "Q3", "12/31": "Q4"}
                    quarter = quarter_map[date_str[:5]] + " 20" + date_str[-2:]
                else:
                    quarter = "Not found"

                # Step 4 – Page 2 TOC
                toc_text = pdf.pages[1].extract_text()

                # Step 5 – Remove irrelevant TOC lines
                lines = toc_text.split("\n")
                ignore_keywords = [
                    "Calendar Year", "Risk Analysis", "Style Box", "Returns Correlation", "Fund Factsheets",
                    "Definitions & Disclosures", "Past performance", "Total Options", "http://", quarter.replace(" ", "/")
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

                # Display cleaned TOC + section page numbers
                st.subheader("Cleaned Table of Contents")
                for line in cleaned_toc_lines:
                    st.markdown(f"- {line}")

                st.subheader("Extracted Section Pages")
                st.markdown(f"**Time Period:** {quarter}")
                st.markdown(f"**Fund Performance Page:** {perf_page if perf_page else 'Not found'}")
                st.markdown(f"**Fund Scorecard Page:** {scorecard_page if scorecard_page else 'Not found'}")

        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")

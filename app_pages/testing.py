import streamlit as st
import pdfplumber
import re
import pandas as pd
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Steps: Convert & Cleanup", layout="wide")
    st.title("Steps")

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

#Step 7
        
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
                
            # --- Display results ---
            st.subheader("Extracted Investment Options")
            for block in fund_blocks:
                st.markdown(f"### {block['name']}")
                for metric in block["metrics"]:
                    st.markdown(f"- **{metric[0]}** → {metric[1]} — {metric[2]}")
                st.markdown("---")
            
        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")

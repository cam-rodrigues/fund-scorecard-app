import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 7: Fund Scorecard Extract", layout="wide")
    st.title("Step 7: Extract Fund Scorecard Section")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step7_upload")

    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # Extract page 1 date and compute quarter (copied from prior step)
            page1 = pdf.pages[0].extract_text()
            date_match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', page1 or "")
            if date_match:
                date_str = date_match.group(0)
                quarter_map = {"3/31": "Q1", "6/30": "Q2", "9/30": "Q3", "12/31": "Q4"}
                month_day = date_str.split("/")[0] + "/" + date_str.split("/")[1]
                quarter = quarter_map.get(month_day, "Unknown") + " " + date_str[-4:]
            else:
                quarter = "Not found"

            # Extract TOC and clean lines
            toc_text = pdf.pages[1].extract_text()
            ignore_keywords = [
                "Calendar Year", "Risk Analysis", "Style Box", "Returns Correlation",
                "Fund Factsheets", "Definitions & Disclosures", "Past performance",
                "Total Options", "http://", quarter.replace(" ", "/"),
                "shares may be worth more/less than original cost",
                "Returns assume reinvestment of all distributions at NAV"
            ]
            toc_lines = toc_text.split("\n")
            cleaned_toc_lines = [line for line in toc_lines if not any(kw in line for kw in ignore_keywords)]

            def find_page(section_title, toc_lines):
                for line in toc_lines:
                    if section_title in line:
                        match = re.search(r"(\d+)$", line)
                        return int(match.group(1)) if match else None
                return None

            scorecard_page = find_page("Fund Scorecard", cleaned_toc_lines)
            if not scorecard_page:
                st.error("❌ Could not find Fund Scorecard section.")
                return

            # Go to Fund Scorecard section
            st.markdown(f"**Scorecard Section starts on page:** {scorecard_page}")

            metric_blocks = []
            current_fund = None

            # Parse all pages starting from scorecard_page
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")
                for line in lines:
                    line = line.strip()

                    # Skip watchlist lines
                    if "Fund Meets Watchlist Criteria" in line or "Fund has been placed on watchlist" in line:
                        continue

                    # Fund name (bold subheadings)
                    if re.match(r'^[A-Z].{5,}$', line) and "Pass" not in line and "Review" not in line:
                        current_fund = {"name": line.strip(), "metrics": []}
                        metric_blocks.append(current_fund)
                        continue

                    # Metric line with Pass/Review
                    if current_fund and ("Pass" in line or "Review" in line):
                        m = re.match(r"(.+?)\s+(Pass|Review)\s+(.+)", line)
                        if m:
                            metric_name = m.group(1).strip()
                            status = m.group(2).strip()
                            reason = m.group(3).strip()
                            current_fund["metrics"].append((metric_name, status, reason))

            # Display Results
            st.subheader("Extracted Funds + Metrics")
            for fund in metric_blocks:
                st.markdown(f"**{fund['name']}**")
                for metric in fund["metrics"]:
                    st.markdown(f"- {metric[0]} → **{metric[1]}** — {metric[2]}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")

import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 11: Remove Watchlist Text", layout="wide")
    st.title("Step 11: Clean Investment Option Names – Watchlist Check")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step11_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # --- Extract Total Options from Page 1 ---
            page1_text = pdf.pages[0].extract_text()
            total_match = re.search(r"Total Options:\s*(\d+)", page1_text or "")
            declared_total = int(total_match.group(1)) if total_match else None

            # --- Extract Scorecard Page Number from TOC (Page 2) ---
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

            # --- Read Scorecard Section Lines ---
            lines_buffer = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text:
                    continue
                lines_buffer.extend(text.split("\n"))

            # --- Clean and filter unwanted definitions ---
            cleaned_lines = []
            skip_keywords = [
                "Criteria Threshold", "Portfolio manager", "must outperform", "must be in the top",
                "must be greater than", "Created with mpi Stylus"
            ]
            for line in lines_buffer:
                if not any(kw in line for kw in skip_keywords):
                    cleaned_lines.append(line.strip())

            # --- Extract Investment Options and Metrics (14 below each name) ---
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

            # --- Step 10: Remove Invalid Names (Not Actual Funds) ---
            invalid_name_terms = [
                "FUND FACTS 3 YEAR ROLLING STYLE",
                "FUND FACTS 3 YEAR ROLLING STYLE ASSET LOADINGS (Returns-based)"
            ]
            cleaned_funds = [
                f for f in fund_blocks
                if not any(term in f["name"].upper() for term in invalid_name_terms)
            ]

            # --- Step 11: Clean Watchlist Sentences from Fund Names ---
            def clean_watchlist_text(name):
                name = re.sub(r"Fund Meets Watchlist Criteria\.", "", name)
                name = re.sub(r"Fund has been placed on watchlist.*", "", name)
                return name.strip()

            final_funds = []
            for f in cleaned_funds:
                cleaned_name = clean_watchlist_text(f["name"])
                if cleaned_name:  # Only include if something remains
                    final_funds.append({
                        "name": cleaned_name,
                        "metrics": f["metrics"]
                    })

            # --- Display Results ---
            st.subheader("Double Check: Investment Option Count")
            st.markdown(f"- Declared in PDF (Page 1): **{declared_total if declared_total else 'Not found'}**")
            st.markdown(f"- Extracted After Cleanup: **{len(final_funds)}**")

            if declared_total is None:
                st.warning("⚠️ Could not find Total Options on Page 1.")
            elif declared_total == len(final_funds):
                st.success("✅ Number of Investment Options matches.")
            else:
                st.error("❌ Mismatch between declared and extracted Investment Options.")

            st.subheader("Cleaned Investment Options (Watchlist stripped)")
            for fund in final_funds:
                st.markdown(f"### {fund['name']}")
                for metric in fund["metrics"]:
                    st.markdown(f"- **{metric[0]}** → {metric[1]} — {metric[2]}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")

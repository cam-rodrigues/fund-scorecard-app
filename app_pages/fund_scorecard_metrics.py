import streamlit as st
import pdfplumber
import pandas as pd
import re

CONFIDENCE_THRESHOLD = 0.75  # below this is considered "low confidence"
DEBUG = True  # Set to False to hide low-confidence logs

def normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())

def simple_similarity(a, b):
    a, b = normalize_name(a), normalize_name(b)
    matches = sum((char in b) for char in a)
    return matches / max(len(a), len(b))

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Processing PDF..."):
            fund_meta = {}
            inception_data = {}
            criteria_data = []
            low_confidence_logs = []

            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)

                # === Phase 1: Build fund meta data (Name + Ticker) ===
                for i in range(min(15, total_pages)):
                    lines = pdf.pages[i].extract_text().split("\n")
                    for line in lines:
                        ticker_match = re.match(r"^(.*?)([A-Z]{4,6})$", line.strip())
                        if ticker_match:
                            fund_name = ticker_match.group(1).strip()
                            ticker = ticker_match.group(2).strip()
                            norm = normalize_name(fund_name)
                            fund_meta[norm] = {
                                "Fund Name": fund_name,
                                "Ticker": ticker
                            }

                # === Phase 2: Collect Inception Dates ===
                for i in range(total_pages):
                    lines = pdf.pages[i].extract_text().split("\n")
                    for j, line in enumerate(lines):
                        if "Inception Date:" in line:
                            match = re.search(r"(\\d{2}/\\d{2}/\\d{4})", line)
                            if not match:
                                continue
                            date = match.group(1)
                            nearby_lines = lines[max(0, j - 10): j + 10]
                            fund_line = next((l for l in nearby_lines if len(l.strip()) > 10 and "Fund" in l), None)
                            if fund_line:
                                fund_name_guess = re.sub(r"Fund.*", "", fund_line).strip()
                                norm = normalize_name(fund_name_guess)
                                inception_data[norm] = date

                # === Phase 3: Scorecard Extraction ===
                for i in range(total_pages):
                    text = pdf.pages[i].extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\\n(?=[^\\n]*?Fund (Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.strip().split("\\n")
                        if not lines:
                            continue

                        raw_line = lines[0].strip()
                        raw_line = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist.*)\\.*", "", raw_line)

                        ticker_match = re.search(r"\\b([A-Z]{4,6})\\b", raw_line)
                        ticker = ticker_match.group(1) if ticker_match else "N/A"
                        fund_name = raw_line.split(ticker)[0].strip() if ticker != "N/A" else raw_line
                        norm_name = normalize_name(fund_name)

                        match_key = None
                        confidence = 0.0

                        if norm_name in fund_meta:
                            match_key = norm_name
                            confidence = 1.0
                        else:
                            scores = [(k, simple_similarity(norm_name, k)) for k in fund_meta]
                            best_match = max(scores, key=lambda x: x[1], default=(None, 0))
                            if best_match[1] > 0.6:
                                match_key = best_match[0]
                                confidence = best_match[1]

                        if not match_key:
                            if DEBUG:
                                low_confidence_logs.append(f"❌ Skipped: '{fund_name}' — no match")
                            continue

                        meta = fund_meta[match_key]
                        meets_criteria = "placed on watchlist" not in block
                        criteria = []

                        for line in lines[1:]:
                            match = re.match(r"^(.*?)\\s+(Pass|Review)", line.strip())
                            if match:
                                metric = match.group(1).strip()
                                result = match.group(2).strip()
                                criteria.append((metric, result))

                        inception_date = inception_data.get(match_key, "N/A")

                        if criteria:
                            entry = {
                                "Fund Name": meta["Fund Name"],
                                "Ticker": meta["Ticker"],
                                "Inception Date": inception_date,
                                "Meets Criteria": "Yes" if meets_criteria else "No",
                                **{metric: result for metric, result in criteria}
                            }
                            criteria_data.append(entry)

                            if DEBUG and confidence < CONFIDENCE_THRESHOLD:
                                low_confidence_logs.append(
                                    f"⚠️ Low confidence ({confidence:.2f}) match: '{fund_name}' → '{meta['Fund Name']}'"
                                )

        # === Output ===
        if criteria_data:
            df = pd.DataFrame(criteria_data)
            st.success(f"✅ Extracted {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download as CSV", data=csv, file_name="fund_criteria_results.csv", mime="text/csv")

            if DEBUG and low_confidence_logs:
                with st.expander("⚠️ Low-Confidence Matches or Skips"):
                    for log in low_confidence_logs:
                        st.markdown(log)
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")

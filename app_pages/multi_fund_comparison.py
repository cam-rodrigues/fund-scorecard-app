# === multi_mpi_extractor.py ===

import streamlit as st
import pdfplumber
import pandas as pd
import numpy as np
import re

# === Extract Fund Performance from a single PDF ===
def extract_fund_performance(pdf_file):
    performance_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text or "Fund Performance: Current vs." not in text:
                continue
            lines = text.split("\n")
            fund_name = None
            for line in lines:
                if re.search(r"[A-Z]{4,6}X", line):
                    fund_name = line.strip()
                    continue
                if fund_name and re.search(r"[-+]?\d+\.\d+", line):
                    numbers = re.findall(r"[-+]?\d+\.\d+", line)
                    if len(numbers) >= 6:
                        performance_data.append({
                            "Fund": fund_name,
                            "QTD": float(numbers[0]),
                            "YTD": float(numbers[1]),
                            "1 Yr": float(numbers[2]),
                            "3 Yr": float(numbers[3]),
                            "5 Yr": float(numbers[4]),
                            "10 Yr": float(numbers[5]),
                        })
                        fund_name = None
    return pd.DataFrame(performance_data)

# === Streamlit App ===
def run():
    st.set_page_config(page_title="Multi-MPI Fund Extractor", layout="wide")
    st.title("📂 Multi-MPI Fund Comparison Tool")

    uploaded_pdfs = st.file_uploader("Upload one or more MPI-style PDFs", type="pdf", accept_multiple_files=True)
    if not uploaded_pdfs:
        st.info("Please upload at least one MPI PDF to begin.")
        st.stop()

    combined_df = pd.DataFrame()
    for uploaded_file in uploaded_pdfs:
        new_df = extract_fund_performance(uploaded_file)
        new_df["Source PDF"] = uploaded_file.name
        combined_df = pd.concat([combined_df, new_df], ignore_index=True)

    if combined_df.empty:
        st.error("No fund performance data was extracted from the uploaded PDFs.")
        st.stop()

    combined_df.drop_duplicates(inplace=True)
    st.success(f"{len(combined_df)} fund entries extracted from {len(uploaded_pdfs)} PDF(s).")

    st.markdown("### Extracted Fund Performance")
    st.dataframe(combined_df, use_container_width=True)

    csv = combined_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download as CSV", data=csv, file_name="funds_combined.csv", mime="text/csv")

# === Run the app ===
if __name__ == "__main__":
    run()

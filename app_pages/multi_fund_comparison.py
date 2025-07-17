# === multi_mpi_extractor.py ===

import streamlit as st
import pdfplumber
import pandas as pd
import numpy as np
import re
from utils.export.pptx_exporter import export_client_dashboard
from utils.export.pdf_exporter import export_client_dashboard_pdf

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
    st.title("Multi Fund Comparison Tool")

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
    st.download_button("Download as CSV", data=csv, file_name="funds_combined.csv", mime="text/csv")

    # === Export Client Dashboard ===
    st.markdown("---")
    st.subheader("📤 Export Client Dashboard")

    client_name = st.text_input("Client Name (for export)", value="Sample Client")

    # Convert DataFrame to fund_data format
    fund_data = []
    for _, row in combined_df.iterrows():
        fund_data.append({
            "fund_name": row["Fund"],
            "key_metrics": [
                f"QTD: {row['QTD']}%",
                f"YTD: {row['YTD']}%",
                f"1 Yr: {row['1 Yr']}%",
                f"3 Yr: {row['3 Yr']}%",
                f"5 Yr: {row['5 Yr']}%",
                f"10 Yr: {row['10 Yr']}%",
            ],
            "rationale": "Rationale not yet provided."  # You could let users input this later
        })

    if st.button("Export to PPTX"):
        export_client_dashboard(fund_data, client_name=client_name, output_path="Client_Dashboard.pptx")
        with open("Client_Dashboard.pptx", "rb") as f:
            st.download_button("Download PPTX", f, file_name="Client_Dashboard.pptx")

    if st.button("Export to PDF"):
        export_client_dashboard_pdf(fund_data, client_name=client_name, output_path="Client_Dashboard.pdf")
        with open("Client_Dashboard.pdf", "rb") as f:
            st.download_button("Download PDF", f, file_name="Client_Dashboard.pdf")

# === Run the app ===
if __name__ == "__main__":
    run()

    st.markdown("---")
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")

# === qtrly_comparison.py ===

import os
import pandas as pd
import pdfplumber
import re
import streamlit as st

# === Extract performance from each PDF ===
def extract_fund_performance_from_pdf(file):
    data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text or "Fund Performance: Current vs." not in text:
                continue
            lines = text.split("\n")
            fund_name = None
            for line in lines:
                if re.search(r"[A-Z]{4,6}X", line):
                    fund_name = line.strip()
                elif fund_name and re.search(r"[-+]?\d+\.\d+", line):
                    numbers = re.findall(r"[-+]?\d+\.\d+", line)
                    if len(numbers) >= 6:
                        data.append({
                            "Fund": fund_name,
                            "QTD": float(numbers[0]),
                            "YTD": float(numbers[1]),
                            "1 Yr": float(numbers[2]),
                            "3 Yr": float(numbers[3]),
                            "5 Yr": float(numbers[4]),
                            "10 Yr": float(numbers[5]),
                        })
                        fund_name = None
    return pd.DataFrame(data)

# === Streamlit App ===
def run():
    st.set_page_config("Quarterly Fund Comparison", layout="wide")
    st.title("Quarterly Fund Comparison Tool")

    uploaded_pdfs = st.file_uploader("Upload multiple MPI PDFs (different quarters)", type="pdf", accept_multiple_files=True)
    if not uploaded_pdfs:
        st.info("Please upload at least two MPI PDFs from different quarters.")
        st.stop()

    # Extract data from each uploaded file and label with upload timestamp (or filename)
    quarter_data = []
    for file in uploaded_pdfs:
        df = extract_fund_performance_from_pdf(file)
        label = os.path.splitext(file.name)[0]
        df["Quarter"] = label
        quarter_data.append(df)

    if not quarter_data:
        st.warning("No data could be extracted from the uploaded PDFs.")
        st.stop()

    all_data = pd.concat(quarter_data, ignore_index=True)
    fund_names = all_data["Fund"].unique()
    selected_funds = st.multiselect("Select funds to compare across quarters", fund_names, default=list(fund_names[:3]))

    if not selected_funds:
        st.warning("Please select at least one fund.")
        st.stop()

    comparison = all_data[all_data["Fund"].isin(selected_funds)]
    pivoted = comparison.pivot_table(index="Quarter", columns="Fund", values=["QTD", "YTD", "1 Yr", "3 Yr", "5 Yr", "10 Yr"])

    st.markdown("### Quarterly Performance Comparison")
    st.dataframe(pivoted.style.format("{:.2f}"), use_container_width=True)

    st.download_button(
        "Download Comparison as CSV",
        data=pivoted.to_csv().encode("utf-8"),
        file_name="quarterly_comparison.csv",
        mime="text/csv"
    )

run()

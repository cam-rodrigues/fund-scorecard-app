import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

# --- IPS Investment Criteria Mapping ---
IPS_METRICS = [
    "Manager Tenure ≥ 3 years",
    "3Y Perf > Benchmark OR 3Y R² > 95%",
    "3Y Perf > 50% of Peers",
    "3Y Sharpe > 50% of Peers",
    "3Y Sortino > 50% of Peers OR 3Y TE < 90% of Peers",
    "5Y Perf > Benchmark OR 5Y R² > 95%",
    "5Y Perf > 50% of Peers",
    "5Y Sharpe > 50% of Peers",
    "5Y Sortino > 50% of Peers OR 5Y TE < 90% of Peers",
    "Expense Ratio < 50% of Peers",
    "Style aligns with objectives",
]

COLUMN_HEADERS = [
    "Name Of Fund", "Category", "Ticker", "Time Period", "Plan Assets"
] + [str(i+1) for i in range(11)] + ["IPS Status"]

# --- Helper: Parse relevant tables from the MPI PDF ---
def extract_fund_tables(pdf):
    data = []
    quarter = datetime.today().strftime("Q{} %Y".format((datetime.today().month - 1)//3 + 1))

    for page in pdf.pages:
        text = page.extract_text()
        if text and "Fund Scorecard" in text:
            lines = text.split("\n")
            fund_name, ticker, category = None, None, None
            metrics = []

            for line in lines:
                if re.match(r"^.+\s+[A-Z]{4,6}X?$", line.strip()):
                    parts = line.rsplit(" ", 1)
                    fund_name, ticker = parts[0].strip(), parts[1].strip()
                    category_match = re.search(r"(Large|Mid|Small|International|Emerging|Fixed Income|Value|Growth|Blend)", fund_name, re.IGNORECASE)
                    if category_match:
                        cat = category_match.group(0)
                        try:
                            style = fund_name.split(cat)[-1].split()[0]
                            category = f"{cat} {style}"
                        except IndexError:
                            category = cat
                    else:
                        category = "Unknown"
                    metrics = []
                elif "Pass" in line or "Review" in line:
                    metrics.append("Pass" if "Pass" in line else "Review")

                    if len(metrics) == 11:
                        fail_count = metrics.count("Review")
                        if fail_count <= 4:
                            status = "Passed IPS Screen"
                        elif fail_count == 5:
                            status = "Informal Watch (IW)"
                        else:
                            status = "Formal Watch (FW)"

                        data.append([fund_name, category, ticker, quarter, "$"] + metrics + [status])

    return pd.DataFrame(data, columns=COLUMN_HEADERS)

# --- Streamlit App ---
def run():
    st.title("IPS Investment Criteria Table Generator")
    st.markdown("Upload an MPI PDF and extract IPS Investment Criteria into a structured table.")

    uploaded_file = st.file_uploader("Upload MPI.pdf", type=["pdf"])

    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            df = extract_fund_tables(pdf)
            st.dataframe(df, use_container_width=True)

            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button(
                "Download as Excel",
                buffer.getvalue(),
                "ips_investment_criteria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    run()

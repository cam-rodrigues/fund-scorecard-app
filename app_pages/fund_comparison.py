import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt

# === Utility: Extract trailing returns section ===
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
                # Identify fund ticker or name
                if re.search(r"[A-Z]{4,6}X", line):
                    fund_name = line.strip()
                    continue

                # Parse numeric lines
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
                        fund_name = None  # reset
    return pd.DataFrame(performance_data)

# === Streamlit App ===
def run():
    st.set_page_config(page_title="Fund Comparison", layout="wide")
    st.title("📊 Fund Performance Comparison Tool")

    uploaded_pdf = st.file_uploader("Upload MPI Fund PDF", type=["pdf"])
    if not uploaded_pdf:
        st.stop()

    with st.spinner("Extracting fund performance..."):
        df = extract_fund_performance(uploaded_pdf)

    if df.empty:
        st.error("No fund data found.")
        st.stop()

    selected_funds = st.multiselect("Select funds to compare", options=df["Fund"].unique())

    if selected_funds:
        subset = df[df["Fund"].isin(selected_funds)].set_index("Fund")
        st.subheader("Selected Fund Metrics")
        st.dataframe(subset.style.format("{:.2f}"))

        st.subheader("Visual Comparison")
        for col in subset.columns:
            st.write(f"**{col}**")
            fig, ax = plt.subplots()
            subset[col].plot(kind="bar", ax=ax)
            ax.set_ylabel(col)
            ax.set_title(f"Comparison: {col}")
            st.pyplot(fig)

if __name__ == "__main__":
    run()

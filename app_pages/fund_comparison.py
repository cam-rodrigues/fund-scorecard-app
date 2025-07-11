import streamlit as st
import pdfplumber
import pandas as pd
import re

# === Extract Performance Metrics from MPI PDF ===
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

# === Style Scorecard with Color ===
def style_scorecard(df):
    styled = df.style.format("{:.2f}")
    for col in df.columns:
        styled = styled.background_gradient(
            cmap="RdYlGn", axis=0, low=0.2, high=0.8, subset=[col]
        )
    return styled

# === Generate Top Summary ===
def generate_summary(df):
    avg_returns = df.mean(axis=1)
    top_fund = avg_returns.idxmax()
    worst_fund = avg_returns.idxmin()
    top_avg = avg_returns.max()
    worst_avg = avg_returns.min()

    wins = df.eq(df.max()).sum(axis=1)
    leader = wins.idxmax()

    return f"""**Summary**
- Top performing fund: **{top_fund}** (avg return: {top_avg:.2f}%)
- Lowest performer: **{worst_fund}** (avg return: {worst_avg:.2f}%)
- {leader} outperformed peers in the most categories."""

# === Streamlit App ===
def run():
    st.set_page_config(page_title="FidSync Beta - Fund Comparison", layout="wide")
    st.title("Fund Performance Comparison")

    uploaded_pdf = st.file_uploader("Upload MPI-style Fund Scorecard (PDF)", type=["pdf"])
    if not uploaded_pdf:
        st.stop()

    with st.spinner("Extracting fund performance data..."):
        df = extract_fund_performance(uploaded_pdf)

    if df.empty:
        st.error("No valid performance data found in this file.")
        st.stop()

    selected_funds = st.multiselect("Select funds to compare", df["Fund"].unique())
    if not selected_funds:
        st.warning("Please select at least one fund.")
        st.stop()

    subset = df[df["Fund"].isin(selected_funds)].set_index("Fund")

    # === Summary + Scorecard ===
    st.markdown("### Fund Comparison Summary")
    st.markdown(generate_summary(subset))

    st.markdown("### Fund Scorecard")
    st.dataframe(style_scorecard(subset), use_container_width=True)

    # === Optional Heatmap ===
    if st.checkbox("Show heatmap view instead of scorecard"):
        st.markdown("### Performance Heatmap")
        st.dataframe(subset.style.background_gradient(cmap="coolwarm").format("{:.2f}"))

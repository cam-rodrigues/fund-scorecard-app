import streamlit as st
import pdfplumber
import pandas as pd
import numpy as np
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

# === Add Benchmark & Volatility Columns ===
def enhance_with_benchmark(df):
    benchmark = {
        "Fund": "S&P 500 (Benchmark)",
        "QTD": 2.00,
        "YTD": 6.00,
        "1 Yr": 12.00,
        "3 Yr": 8.00,
        "5 Yr": 10.00,
        "10 Yr": 10.50
    }

    df = pd.concat([df, pd.DataFrame([benchmark])], ignore_index=True)

    # Add volatility and Sharpe estimates (mocked for now)
    np.random.seed(42)
    df["Volatility (%)"] = np.round(np.random.uniform(9, 18, len(df)), 2)
    df["Sharpe Ratio"] = np.round(np.random.uniform(0.4, 1.2, len(df)), 2)
    return df

# === Style Scorecard with Color ===
def style_scorecard(df):
    styled = df.style.format("{:.2f}")
    for col in df.columns[:-2]:  # exclude Volatility & Sharpe
        styled = styled.background_gradient(
            cmap="RdYlGn", axis=0, low=0.2, high=0.8, subset=[col]
        )
    return styled

# === Generate Summary with Benchmark Comparison ===
def generate_summary(df):
    if "S&P 500 (Benchmark)" not in df["Fund"].values:
        return ""

    df = df.set_index("Fund")
    benchmark = df.loc["S&P 500 (Benchmark)"]
    comparisons = df.drop("S&P 500 (Benchmark)")
    beat_counts = (comparisons[benchmark.index] > benchmark).sum(axis=1)
    best_fund = beat_counts.idxmax()
    avg_returns = comparisons.mean(axis=1)

    top_fund = avg_returns.idxmax()
    worst_fund = avg_returns.idxmin()

    return f"""**Summary**
- Fund that outperformed benchmark most: **{best_fund}** ({beat_counts[best_fund]} of 6 periods)
- Top average return: **{top_fund}** ({avg_returns[top_fund]:.2f}%)
- Lowest overall performer: **{worst_fund}** ({avg_returns[worst_fund]:.2f}%)
"""

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
        st.error("No valid performance data found.")
        st.stop()

    selected_funds = st.multiselect("Select funds to compare", df["Fund"].unique())
    if not selected_funds:
        st.warning("Please select at least one fund.")
        st.stop()

    filtered = df[df["Fund"].isin(selected_funds)]
    full_df = enhance_with_benchmark(filtered).set_index("Fund")

    # === Summary + Scorecard ===
    st.markdown("### Performance Summary")
    st.markdown(generate_summary(full_df))

    st.markdown("### Fund Scorecard (Including Benchmark and Risk Metrics)")
    st.dataframe(style_scorecard(full_df), use_container_width=True)

    if st.checkbox("Show heatmap instead of scorecard"):
        st.markdown("### Performance Heatmap")
        st.dataframe(full_df.style.background_gradient(cmap="coolwarm").format("{:.2f}"))

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

# === Add Benchmark + Risk Columns ===
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

    # Add mocked Volatility and Sharpe Ratio
    np.random.seed(42)
    df["Volatility (%)"] = np.round(np.random.uniform(9, 18, len(df)), 2)
    df["Sharpe Ratio"] = np.round(np.random.uniform(0.4, 1.2, len(df)), 2)
    return df

# === Color-Coded Scorecard ===
def style_scorecard(df):
    styled = df.style.format("{:.2f}")
    for col in df.columns[:-2]:  # exclude Volatility & Sharpe
        styled = styled.background_gradient(
            cmap="RdYlGn", axis=0, low=0.2, high=0.8, subset=[col]
        )
    return styled

# === Summary Generator ===
def generate_summary(df):
    df = df.copy()

    # Ensure 'Fund' is a column
    if df.index.name == "Fund":
        df.reset_index(inplace=True)

    if "S&P 500 (Benchmark)" not in df["Fund"].values:
        return ""

    benchmark = df[df["Fund"] == "S&P 500 (Benchmark)"].iloc[0]
    others = df[df["Fund"] != "S&P 500 (Benchmark)"]

    trailing_cols = ["QTD", "YTD", "1 Yr", "3 Yr", "5 Yr", "10 Yr"]
    beat_counts = (others[trailing_cols] > benchmark[trailing_cols]).sum(axis=1)

    best_fund = beat_counts.idxmax()
    top_fund = others[trailing_cols].mean(axis=1).idxmax()
    worst_fund = others[trailing_cols].mean(axis=1).idxmin()

    return f"""**Summary**
- Fund that outperformed benchmark most: **{others.iloc[best_fund]['Fund']}** ({beat_counts.iloc[best_fund]} of 6 periods)
- Highest avg return: **{others.iloc[top_fund]['Fund']}**
- Lowest overall performer: **{others.iloc[worst_fund]['Fund']}**
"""

# === Streamlit App ===
def run():
    st.set_page_config(page_title="FidSync Beta - Fund Comparison", layout="wide")
    st.title("Fund Performance Comparison")

    uploaded_pdf = st.file_uploader("Upload MPI-style Fund Scorecard (PDF)", type=["pdf"])
    if not uploaded_pdf:
        st.stop()

    with st.spinner("Extracting fund data..."):
        df = extract_fund_performance(uploaded_pdf)

    if df.empty:
        st.error("No valid fund data found.")
        st.stop()

    selected = st.multiselect("Select funds to compare", df["Fund"].unique())
    if not selected:
        st.warning("Please select at least one fund.")
        st.stop()

    # Filter and enhance
    filtered = df[df["Fund"].isin(selected)]
    enhanced = enhance_with_benchmark(filtered)

    # Show summary + data
    st.markdown("### Performance Summary")
    st.markdown(generate_summary(enhanced))

    st.markdown("### Scorecard with Benchmark and Risk")
    st.dataframe(style_scorecard(enhanced.set_index("Fund")), use_container_width=True)

    if st.checkbox("Show heatmap instead"):
        st.markdown("### Heatmap View")
        st.dataframe(
            enhanced.set_index("Fund").style.background_gradient(cmap="coolwarm").format("{:.2f}")
        )

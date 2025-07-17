import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches
from io import BytesIO
from utils.export.pptx_exporter import create_fidsync_template_slide

# --- Build ticker lookup ---
def build_ticker_lookup(pdf):
    lookup = {}
    for page in pdf.pages:
        lines = page.extract_text().split("\n") if page.extract_text() else []

        for i in range(len(lines) - 1):
            name_line = lines[i].strip()
            ticker_line = lines[i + 1].strip()
            if re.match(r"^[A-Z]{4,6}X?$", ticker_line) and len(name_line.split()) >= 3:
                if not re.match(r"^[A-Z]{4,6}X?$", name_line):
                    lookup[" ".join(name_line.split())] = ticker_line

        for line in lines:
            parts = line.strip().rsplit(" ", 1)
            if len(parts) == 2 and re.match(r"^[A-Z]{4,6}X?$", parts[1]):
                if len(parts[0].split()) >= 3:
                    lookup[parts[0].strip()] = parts[1].strip()
    return lookup

# --- Fund name from block ---
def get_fund_name(block, lookup):
    block_lower = block.lower()
    for name in lookup:
        if name.lower() in block_lower:
            return name

    lines = block.split("\n")
    candidates = [line.strip() for line in lines[:6] if sum(c.isupper() for c in line) > 5]

    for line in candidates:
        match = get_close_matches(line, lookup.keys(), n=1, cutoff=0.5)
        if match:
            return match[0]

    metric_start = next((i for i, line in enumerate(lines) if any(m in line for m in [
        "Manager Tenure", "Excess Performance", "Peer Return Rank",
        "Expense Ratio Rank", "Sharpe Ratio", "Tracking Error"
    ])), None)

    if metric_start and metric_start > 0:
        fallback = lines[metric_start - 1].strip()
        fallback = re.sub(r"(This|The)?\s?fund\s(has|meets).*", "", fallback, flags=re.I).strip()
        if fallback:
            return fallback
    return "UNKNOWN FUND"

# --- Parse metrics ---
def parse_metrics(block):
    metrics = {
        "Manager Tenure": {"status": None, "value": None},
        "Excess Performance (3Yr)": {"status": None, "value": None},
        "Excess Performance (5Yr)": {"status": None, "value": None},
        "Peer Return Rank (3Yr)": {"status": None, "value": None},
        "Peer Return Rank (5Yr)": {"status": None, "value": None},
        "Expense Ratio Rank": {"status": None, "value": None},
        "Sharpe Ratio Rank (3Yr)": {"status": None, "value": None},
        "Sharpe Ratio Rank (5Yr)": {"status": None, "value": None},
    }

    for line in block.split("\n"):
        for key in metrics:
            if key in line:
                if "Pass" in line:
                    metrics[key]["status"] = "Pass"
                elif "Review" in line:
                    metrics[key]["status"] = "Review"
                elif "Fail" in line:
                    metrics[key]["status"] = "Fail"

                match = re.search(r"[-+]?\d+\.?\d*%?", line)
                if match:
                    metrics[key]["value"] = match.group()
    return metrics

# --- Writeup builder ---
def generate_analysis(m):
    lines = []

    if m["Excess Performance (3Yr)"]["status"] == "Pass" or m["Excess Performance (5Yr)"]["status"] == "Pass":
        perf3 = m["Excess Performance (3Yr)"]["value"]
        perf5 = m["Excess Performance (5Yr)"]["value"]
        if perf3 and perf5:
            lines.append(f"The fund has outperformed its benchmark by {perf3} over the trailing 3 years and by {perf5} over 5 years, signaling consistent long-term performance.")
        elif perf3:
            lines.append(f"The fund has posted {perf3} excess return over 3 years, indicating near-term strength.")
        elif perf5:
            lines.append(f"The fund delivered {perf5} excess return over 5 years, showcasing its long-term capability.")

    if m["Peer Return Rank (5Yr)"]["status"] == "Pass":
        rank = m["Peer Return Rank (5Yr)"]["value"]
        lines.append(f"Its 5-year peer return rank of {rank} places it among the strongest in its category.")
    elif m["Peer Return Rank (3Yr)"]["status"] == "Pass":
        rank = m["Peer Return Rank (3Yr)"]["value"]
        lines.append(f"The fund also ranks competitively over the past 3 years, with a peer ranking of {rank}.")

    if m["Sharpe Ratio Rank (5Yr)"]["status"] == "Pass":
        lines.append("Risk-adjusted returns over the last 5 years have been strong, with a high Sharpe ratio relative to peers.")
    elif m["Sharpe Ratio Rank (3Yr)"]["status"] == "Pass":
        lines.append("The fund's 3-year Sharpe ratio suggests solid risk-adjusted outperformance.")

    if m["Expense Ratio Rank"]["status"] == "Pass":
        exp = m["Expense Ratio Rank"]["value"]
        lines.append(f"With an expense ratio rank of {exp}, the fund remains cost-efficient compared to peers.")

    if m["Manager Tenure"]["status"] == "Pass":
        val = m["Manager Tenure"]["value"]
        lines.append(f"The management team is experienced, having overseen the strategy for {val}.")

    if m["Excess Performance (3Yr)"]["status"] == "Review" or m["Excess Performance (5Yr)"]["status"] == "Review":
        lines.append("Recent performance relative to the benchmark has been mixed and may warrant further review.")

    if m["Sharpe Ratio Rank (3Yr)"]["status"] == "Review" or m["Sharpe Ratio Rank (5Yr)"]["status"] == "Review":
        lines.append("Risk-adjusted returns are currently under evaluation and do not stand out within the peer set.")

    if not lines:
        return "This fund's performance is mixed across key metrics and should be reviewed further before making a recommendation."

    lines.append("Overall, the fund shows positive attributes that may make it suitable for continued monitoring or inclusion based on plan objectives.")
    return " ".join(lines)

# --- Streamlit App ---
def run():
    st.set_page_config(page_title="Fund Writeup Generator", layout="wide")
    st.title("Fund Writeup Generator")

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if pdf_file:
        with pdfplumber.open(pdf_file) as pdf:
            ticker_lookup = build_ticker_lookup(pdf)
            fund_blocks = []
            fund_names = []

            for page in pdf.pages:
                txt = page.extract_text()
                if not txt:
                    continue

                blocks = re.split(
                    r"\n(?=[^\n]*?(Fund )?(Meets Watchlist Criteria|has been placed on watchlist))",
                    txt)

                for block in blocks:
                    if not block.strip():
                        continue
                    name = get_fund_name(block, ticker_lookup)
                    fund_names.append(name)
                    fund_blocks.append(block)

        if not fund_blocks:
            st.error("No fund entries found.")
            return

        selected = st.selectbox("Select a fund", fund_names)

        if selected:
            idx = fund_names.index(selected)
            block = fund_blocks[idx]
            metrics = parse_metrics(block)
            writeup = generate_analysis(metrics)

            # === Table ===
            st.subheader("Metric Summary Table")
            table = []
            for k, v in metrics.items():
                table.append({"Metric": k, "Status": v["status"] or "-", "Value": v["value"] or "-"})
            df = pd.DataFrame(table)

            def colorize(row):
                bg = "#ffffff"
                if row["Status"] == "Pass": bg = "#d6f5d6"
                elif row["Status"] == "Review": bg = "#fff5cc"
                elif row["Status"] == "Fail": bg = "#f7d6d6"
                return [f"background-color: {bg}"] * len(row)

            st.dataframe(df.style.apply(colorize, axis=1), use_container_width=True)

            # === Writeup ===
            st.subheader("Recommendation Summary")
            st.markdown(f"""
                <div style="background-color:#f6f9fc;padding:1rem;border-radius:0.5rem;border:1px solid #dbe2ea;">
                {writeup}
                </div>
            """, unsafe_allow_html=True)

            # === Export ===
            pptx = create_fidsync_template_slide(selected, [writeup])
            st.download_button("Download PowerPoint (.pptx)",
                               data=pptx,
                               file_name=f"{selected}_writeup.pptx",
                               mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

    st.markdown("---")
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")

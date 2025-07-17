import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="IPS Fund Evaluation", layout="wide")
st.title("IPS Investment Criteria Evaluation")

uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

def extract_fund_info(pdf):
    fund_info = []
    in_perf_section = False

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue

        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "Fund Performance: Current vs. Proposed Comparison" in line:
                in_perf_section = True

            if in_perf_section:
                if re.match(r"^[A-Z]{4,6}X?$", line.strip()):  # Ticker line
                    name_line = lines[i - 1].strip()
                    category = ""
                    for j in range(i - 2, max(i - 6, 0), -1):
                        if "Cap" in lines[j] or "Blend" in lines[j] or "Value" in lines[j] or "Growth" in lines[j]:
                            category = lines[j].strip()
                            break
                    fund_info.append({
                        "Fund Name": name_line,
                        "Category": category,
                        "Ticker": line.strip()
                    })
    return fund_info

def parse_value(text):
    try:
        return float(re.findall(r"[-+]?\d*\.\d+|\d+", text)[0])
    except:
        return None

def evaluate_metric(text, index):
    text = text.lower()
    if index == 0:
        return parse_value(text) >= 3
    elif index == 1:
        return "outperform" in text or ("r²" in text and parse_value(text) >= 95)
    elif index == 2:
        return "rank" in text and parse_value(text) <= 50
    elif index == 3:
        return "sharpe" in text and parse_value(text) <= 50
    elif index == 4:
        return ("sortino" in text and parse_value(text) <= 50) or ("tracking" in text and parse_value(text) < 90)
    elif index == 5:
        return "outperform" in text or ("r²" in text and parse_value(text) >= 95)
    elif index == 6:
        return "rank" in text and parse_value(text) <= 50
    elif index == 7:
        return "sharpe" in text and parse_value(text) <= 50
    elif index == 8:
        return ("sortino" in text and parse_value(text) <= 50) or ("tracking" in text and parse_value(text) < 90)
    elif index == 9:
        return "expense" in text and parse_value(text) < 50
    elif index == 10:
        return "consistent" in text
    return False

def extract_scorecard(pdf):
    fund_blocks = {}
    current_fund = None
    current_metrics = []

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        for line in lines:
            if "Fund Scorecard" in line:
                continue
            if re.match(r'^[A-Z][\w\s\-&,]+$', line.strip()) and len(line.strip().split()) > 2:
                if current_fund and current_metrics:
                    fund_blocks[current_fund] = current_metrics.copy()
                current_fund = line.strip()
                current_metrics = []
            elif any(metric in line for metric in ["Tenure", "Performance", "Sharpe", "Sortino", "Tracking", "Expense", "Style"]):
                current_metrics.append(line.strip())
        if current_fund and current_metrics:
            fund_blocks[current_fund] = current_metrics
    return fund_blocks

def build_table(fund_info_list, scorecard_blocks):
    quarter = f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year}"
    results = []

    for fund in fund_info_list:
        name = fund["Fund Name"]
        matched_name = next((sc_name for sc_name in scorecard_blocks if name.lower() in sc_name.lower()), None)
        metrics = scorecard_blocks.get(matched_name, [])
        pass_fail = []
        for i in range(11):
            if i < len(metrics):
                pass_fail.append("Pass" if evaluate_metric(metrics[i], i) else "Fail")
            else:
                pass_fail.append("Fail")
        fails = pass_fail.count("Fail")
        if fails <= 4:
            status = "Passed IPS Screen"
        elif fails == 5:
            status = "Informal Watch (IW)"
        else:
            status = "Formal Watch (FW)"

        results.append({
            "Name Of Fund": name,
            "Category": fund["Category"],
            "Ticker": fund["Ticker"],
            "Time Period": quarter,
            "Plan Assets": "$",
            **{str(i+1): pass_fail[i] for i in range(11)},
            "IPS Status": status
        })

    return pd.DataFrame(results)

# === Run the logic if file is uploaded ===
if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        fund_info_list = extract_fund_info(pdf)
        scorecard_blocks = extract_scorecard(pdf)
        df = build_table(fund_info_list, scorecard_blocks)

    st.success("Evaluation complete.")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "ips_evaluation.csv", "text/csv")

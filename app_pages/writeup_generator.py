import streamlit as st
import pdfplumber
import re
import io
from pptx.util import Inches
from utils.export.pptx_exporter import create_fidsync_template_slide

# --- Extract fund blocks from relevant pages ---
def extract_fund_blocks(pdf):
    fund_blocks = []
    capture = False
    for page in pdf.pages:
        text = page.extract_text()
        if text and "Fund Scorecard" in text:
            lines = text.split('\n')
            current_block = []
            for line in lines:
                if "Fund Scorecard" in line:
                    if current_block:
                        fund_blocks.append('\n'.join(current_block))
                        current_block = []
                current_block.append(line)
            if current_block:
                fund_blocks.append('\n'.join(current_block))
    return fund_blocks

# --- Parse metrics from fund block ---
def parse_metrics(block):
    metrics = {
        "Manager Tenure": None,
        "Excess Performance (3Yr)": None,
        "Excess Performance (5Yr)": None,
        "Peer Return Rank (3Yr)": None,
        "Peer Return Rank (5Yr)": None,
        "Expense Ratio Rank": None,
        "Sharpe Ratio (3Yr)": None,
        "Sharpe Ratio (5Yr)": None,
        "R-Squared (3Yr)": None,
        "R-Squared (5Yr)": None,
        "Tracking Error (3Yr)": None,
        "Tracking Error (5Yr)": None,
    }

    for line in block.split("\n"):
        for key in metrics:
            if key in line:
                if "Pass" in line:
                    metrics[key] = "Pass"
                elif "Review" in line:
                    metrics[key] = "Review"
                elif "Fail" in line:
                    metrics[key] = "Fail"
    return metrics

# --- Generate custom writeup paragraph ---
def generate_analysis(metrics):
    lines = []

    if metrics["Excess Performance (3Yr)"] == "Pass" and metrics["Excess Performance (5Yr)"] == "Pass":
        lines.append("The fund consistently outperformed its benchmark over both the 3- and 5-year periods.")
    elif metrics["Excess Performance (3Yr)"] == "Pass":
        lines.append("The fund demonstrated strong 3-year performance relative to its benchmark.")
    elif metrics["Excess Performance (5Yr)"] == "Pass":
        lines.append("The fund outpaced its benchmark over the 5-year horizon.")

    if metrics["Peer Return Rank (5Yr)"] == "Pass":
        lines.append("It ranks favorably among peers over the long term.")
    elif metrics["Peer Return Rank (3Yr)"] == "Pass":
        lines.append("It has performed competitively in the short term versus peer funds.")

    if metrics["Sharpe Ratio (5Yr)"] == "Pass":
        lines.append("Its 5-year Sharpe Ratio reflects attractive risk-adjusted returns.")
    elif metrics["Sharpe Ratio (3Yr)"] == "Pass":
        lines.append("The 3-year Sharpe Ratio shows moderate risk-adjusted strength.")

    if metrics["Expense Ratio Rank"] == "Pass":
        lines.append("The fund maintains a cost-efficient structure relative to peers.")

    if metrics["R-Squared (3Yr)"] == "Review" or metrics["R-Squared (5Yr)"] == "Review":
        lines.append("Benchmark alignment may warrant further scrutiny due to lower R-squared values.")

    if metrics["Tracking Error (3Yr)"] == "Review" or metrics["Tracking Error (5Yr)"] == "Review":
        lines.append("Tracking error should be reviewed to ensure consistent performance versus benchmark.")

    if not lines:
        return "This fund has a mixed evaluation across key metrics. Further analysis is recommended."

    return " ".join(lines)

# --- Streamlit UI ---
def run():
    st.set_page_config(page_title="Writeup Generator", layout="wide")
    st.title("Fund Writeup Generator")

    uploaded_pdf = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_pdf:
        with pdfplumber.open(uploaded_pdf) as pdf:
            blocks = extract_fund_blocks(pdf)

        if not blocks:
            st.error("No fund scorecard blocks detected.")
            return

        fund_names = [re.search(r"^(.+?) Fund (Meets|has been)", b, re.M) for b in blocks]
        fund_names = [m.group(1).strip() for m in fund_names if m]

        selected = st.selectbox("Select a fund", fund_names)

        if selected:
            match_block = next(b for b in blocks if selected in b)
            metrics = parse_metrics(match_block)
            writeup = generate_analysis(metrics)

            st.subheader("Preview")
            st.markdown(f"""
                <div style="background-color:#f6f9fc;padding:1rem;border-radius:0.5rem;border:1px solid #dbe2ea;">
                <b>Recommendation Summary</b><br><br>
                {writeup}
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.download_button("⬇ Export to Word (.docx)", create_fidsync_docx(selected, writeup), file_name=f"{selected}_writeup.docx"):
                    st.success("Word file ready.")

            with col2:
                if st.download_button("⬇ Export to PowerPoint (.pptx)", create_fidsync_template_slide(selected, [writeup]), file_name=f"{selected}_writeup.pptx"):
                    st.success("PowerPoint file ready.")


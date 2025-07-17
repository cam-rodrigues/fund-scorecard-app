import streamlit as st 
import pdfplumber
import re
from utils.export.pptx_exporter import create_fidsync_template_slide

# --- Extract fund blocks from relevant pages ---
def extract_fund_blocks(pdf):
    fund_blocks = []
    for page in pdf.pages:
        text = page.extract_text()
        if text and "Fund Scorecard" in text:
            fund_sections = text.split("Fund Scorecard")
            for section in fund_sections[1:]:  # Skip first if it's header
                block = "Fund Scorecard" + section.strip()
                fund_blocks.append(block)
    return fund_blocks

# --- Improved metric parser ---
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

# --- Professional-style writeup ---
def generate_analysis(m):
    lines = []

    # Performance
    if m["Excess Performance (3Yr)"]["status"] == "Pass" or m["Excess Performance (5Yr)"]["status"] == "Pass":
        perf3 = m["Excess Performance (3Yr)"]["value"]
        perf5 = m["Excess Performance (5Yr)"]["value"]
        if perf3 and perf5:
            lines.append(f"The fund has outperformed its benchmark by {perf3} over the trailing 3 years and by {perf5} over 5 years, signaling consistent long-term performance.")
        elif perf3:
            lines.append(f"The fund has posted {perf3} excess return over 3 years, indicating near-term strength.")
        elif perf5:
            lines.append(f"The fund delivered {perf5} excess return over 5 years, showcasing its long-term capability.")

    # Peer Ranks
    if m["Peer Return Rank (5Yr)"]["status"] == "Pass":
        rank = m["Peer Return Rank (5Yr)"]["value"]
        lines.append(f"Its 5-year peer return rank of {rank} places it among the strongest in its category.")
    elif m["Peer Return Rank (3Yr)"]["status"] == "Pass":
        rank = m["Peer Return Rank (3Yr)"]["value"]
        lines.append(f"The fund also ranks competitively over the past 3 years, with a peer ranking of {rank}.")

    # Sharpe
    if m["Sharpe Ratio Rank (5Yr)"]["status"] == "Pass":
        lines.append("Risk-adjusted returns over the last 5 years have been strong, with a high Sharpe ratio relative to peers.")
    elif m["Sharpe Ratio Rank (3Yr)"]["status"] == "Pass":
        lines.append("The fund's 3-year Sharpe ratio suggests solid risk-adjusted outperformance.")

    # Expense
    if m["Expense Ratio Rank"]["status"] == "Pass":
        exp = m["Expense Ratio Rank"]["value"]
        lines.append(f"With an expense ratio rank of {exp}, the fund remains cost-efficient compared to peers.")

    # Tenure
    if m["Manager Tenure"]["status"] == "Pass":
        val = m["Manager Tenure"]["value"]
        lines.append(f"The management team is experienced, having overseen the strategy for {val}.")

    # Reviews
    if m["Excess Performance (3Yr)"]["status"] == "Review" or m["Excess Performance (5Yr)"]["status"] == "Review":
        lines.append("Recent performance relative to the benchmark has been mixed and may warrant further review.")

    if m["Sharpe Ratio Rank (3Yr)"]["status"] == "Review" or m["Sharpe Ratio Rank (5Yr)"]["status"] == "Review":
        lines.append("Risk-adjusted returns are currently under evaluation and do not stand out within the peer set.")

    if not lines:
        return "This fund's performance is mixed across key metrics and should be reviewed further before making a recommendation."

    lines.append("Overall, the fund shows positive attributes that may make it suitable for continued monitoring or inclusion based on plan objectives.")
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

        fund_names = []
        for b in blocks:
            match = re.search(r"([A-Z][A-Za-z &\-]+?) Fund", b)
            if match:
                fund_names.append(match.group(1).strip())

        selected = st.selectbox("Select a fund", fund_names)

        if selected:
            selected_index = fund_names.index(selected)
            match_block = blocks[selected_index]
            metrics = parse_metrics(match_block)
            writeup = generate_analysis(metrics)

            st.subheader("Preview")
            st.markdown(f"""
                <div style="background-color:#f6f9fc;padding:1rem;border-radius:0.5rem;border:1px solid #dbe2ea;">
                <b>Recommendation Summary</b><br><br>
                {writeup}
                </div>
            """, unsafe_allow_html=True)

            pptx_data = create_fidsync_template_slide(selected, [writeup])
            st.download_button(
                "Download PowerPoint (.pptx)",
                data=pptx_data,
                file_name=f"{selected}_writeup.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

import streamlit as st
import pdfplumber
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from docx import Document
from io import BytesIO

def run():
    st.set_page_config(page_title="Writeup Generator", layout="wide")
    st.title("Writeup Generator")

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if not pdf_file:
        st.stop()

    # === Extract fund blocks from Fund Scorecard pages ===
    @st.cache_data(show_spinner=False)
    def extract_fund_blocks(pdf_bytes):
        fund_blocks = []
        fund_name_pattern = re.compile(r"[A-Z][A-Za-z0-9 ,\-&]{4,} Fund")
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if "FUND SCORECARD" in text.upper():
                    lines = text.split("\n")
                    for i, line in enumerate(lines):
                        if fund_name_pattern.search(line):
                            block = "\n".join(lines[i : i + 20])
                            fund_blocks.append(block)
        return fund_blocks

    fund_blocks = extract_fund_blocks(pdf_file)

    # === Extract fund names ===
    fund_names = []
    fund_block_map = {}
    for block in fund_blocks:
        match = re.search(r"([A-Z][A-Za-z0-9 ,\-&]{4,} Fund)", block)
        if match:
            name = match.group(1).strip()
            fund_names.append(name)
            fund_block_map[name] = block

    if not fund_names:
        st.warning("No valid fund names found.")
        st.stop()

    selected_fund = st.selectbox("Select a Fund", fund_names)
    block = fund_block_map[selected_fund]

    # === Build writeup text ===
    def build_writeup(fund_name, block):
        lines = block.split("\n")

        watchlist_status = "⚠️ On Watchlist"
        metrics_summary = []
        considerations = []

        for line in lines:
            line = line.strip()
            if "placed on watchlist" in line.lower():
                watchlist_status = "⚠️ On Watchlist"
            if "Meets Watchlist Criteria" in line:
                watchlist_status = "✅ Meets Watchlist Criteria"

            if "Manager Tenure" in line and "Pass" in line:
                tenure_match = re.search(r"(\d+\.\d+)\s+years", line)
                if tenure_match:
                    tenure = tenure_match.group(1)
                    metrics_summary.append(f"- Manager Tenure: {tenure} years")
                    considerations.append("Experienced management team")

            if "Excess Performance (3Yr)" in line:
                val = re.search(r"by\s+([-+]?\d+\.\d+)%", line)
                if val:
                    metrics_summary.append(f"- 3-Year Excess Return: +{val.group(1)}%")
                    considerations.append("3-year excess return above benchmark")

            if "Excess Performance (5Yr)" in line:
                val = re.search(r"by\s+([-+]?\d+\.\d+)%", line)
                if val:
                    metrics_summary.append(f"- 5-Year Excess Return: +{val.group(1)}%")
                    considerations.append("5-year excess return above benchmark")

            if "Peer Return Rank (3Yr)" in line:
                val = re.search(r"Rank is\s+(\d+)", line)
                if val:
                    metrics_summary.append(f"- 3-Year Peer Return Rank: {val.group(1)}th percentile")
                    considerations.append("Strong short-term peer ranking")

            if "Peer Return Rank (5Yr)" in line:
                val = re.search(r"Rank is\s+(\d+)", line)
                if val:
                    metrics_summary.append(f"- 5-Year Peer Return Rank: {val.group(1)}th percentile")
                    considerations.append("Strong long-term peer ranking")

            if "Expense Ratio Rank" in line:
                val = re.search(r"percentile rank is\s+(\d+)", line)
                if val:
                    metrics_summary.append(f"- Expense Ratio: {val.group(1)}th percentile")
                    considerations.append("Low cost relative to peers")

            if "Sharpe Ratio Rank (5Yr)" in line and "Pass" in line:
                considerations.append("Strong risk-adjusted performance")

            if "R-Squared" in line and "Review" in line:
                metrics_summary.append("- R-Squared: Requires Review")

        summary = [
            f"**Recommendation Summary**",
            "",
            f"We recommend **{fund_name}** as a potential primary candidate based on key performance indicators.",
            "",
            f"**Watchlist Status:** {watchlist_status}",
            "",
            "**Performance Highlights:**",
            *metrics_summary,
            "",
            "**Considerations:**",
            *["- " + c for c in set(considerations)],
            "",
            "This recommendation should be confirmed against current plan goals, investment policy benchmarks, and fiduciary guidelines."
        ]

        return "\n".join(summary)

    writeup = build_writeup(selected_fund, block)

    # === Display writeup ===
    st.subheader("📋 Writeup Preview")
    st.markdown(writeup)

    # === DOCX Export ===
    def export_docx(name, writeup):
        doc = Document()
        doc.add_heading(f'Proposal: {name}', 0)
        for line in writeup.split("\n"):
            doc.add_paragraph(line)
        bio = BytesIO()
        doc.save(bio)
        return bio.getvalue()

    # === PPTX Export ===
    def export_pptx(name, writeup):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.3), Inches(9), Inches(1))
        title_tf = title_box.text_frame
        run = title_tf.paragraphs[0].add_run()
        run.text = f"Recommendation: {name}"
        run.font.size = Pt(28)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 32, 96)

        # Body
        body_box = slide.shapes.add_textbox(Inches(0.3), Inches(1.3), Inches(9), Inches(5.5))
        body_tf = body_box.text_frame
        for line in writeup.split("\n"):
            if line.strip():
                body_tf.add_paragraph().text = line.strip()

        bio = BytesIO()
        prs.save(bio)
        return bio.getvalue()

    # === Download buttons ===
    st.download_button("📄 Export as DOCX", export_docx(selected_fund, writeup), file_name=f"{selected_fund}_proposal.docx")
    st.download_button("📊 Export as PPTX", export_pptx(selected_fund, writeup), file_name=f"{selected_fund}_slide.pptx")

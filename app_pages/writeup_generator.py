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
        metrics = []
        highlights = []

        for line in lines:
            line = line.strip()
            if "placed on watchlist" in line.lower():
                watchlist_status = "⚠️ On Watchlist"
            if "Meets Watchlist Criteria" in line:
                watchlist_status = "✅ Meets Watchlist Criteria"

            if "Manager Tenure" in line and "Pass" in line:
                val = re.search(r"(\d+\.\d+)\s+years", line)
                if val:
                    metrics.append(f"- **Manager Tenure:** {val.group(1)} years (Pass)")
                    highlights.append("Long-tenured management suggests consistency.")

            if "Excess Performance (3Yr)" in line:
                val = re.search(r"by\s+([-+]?\d+\.\d+)%", line)
                if val:
                    metrics.append(f"- **3-Year Excess Return:** +{val.group(1)}%")
                    highlights.append("Outperformed benchmark over 3 years.")

            if "Excess Performance (5Yr)" in line:
                val = re.search(r"by\s+([-+]?\d+\.\d+)%", line)
                if val:
                    metrics.append(f"- **5-Year Excess Return:** +{val.group(1)}%")
                    highlights.append("Strong long-term excess return over benchmark.")

            if "Peer Return Rank (3Yr)" in line:
                val = re.search(r"Rank is\s+(\d+)", line)
                if val:
                    metrics.append(f"- **3-Year Peer Return Rank:** {val.group(1)}th percentile")
                    highlights.append("Competitive short-term peer ranking.")

            if "Peer Return Rank (5Yr)" in line:
                val = re.search(r"Rank is\s+(\d+)", line)
                if val:
                    metrics.append(f"- **5-Year Peer Return Rank:** {val.group(1)}th percentile")
                    highlights.append("Top-tier long-term peer ranking.")

            if "Expense Ratio Rank" in line:
                val = re.search(r"percentile rank is\s+(\d+)", line)
                if val:
                    metrics.append(f"- **Expense Ratio Rank:** {val.group(1)}th percentile (Pass)")
                    highlights.append("Low expenses relative to peers.")

            if "Sharpe Ratio Rank (5Yr)" in line and "Pass" in line:
                highlights.append("Strong risk-adjusted returns (Sharpe).")

            if "R-Squared" in line and "Review" in line:
                metrics.append("- **R-Squared:** Requires Review")

        markdown = []

        markdown.append(f"### {fund_name}")
        markdown.append("")
        markdown.append(f"**Recommendation:** This fund is recommended as a primary candidate based on key performance and peer rankings.")
        markdown.append("")
        markdown.append(f"**Watchlist Status:** {watchlist_status}")
        markdown.append("")
        markdown.append("---")
        markdown.append("**Key Metrics Summary:**")
        markdown.extend(metrics)
        markdown.append("")
        markdown.append("---")
        markdown.append("**Analysis:**")
        if highlights:
            markdown.append("This fund shows:")
            for h in set(highlights):
                markdown.append(f"- {h}")
        else:
            markdown.append("This fund meets minimum watchlist standards but lacks notable strengths.")
        markdown.append("")
        markdown.append("**Conclusion:**")
        markdown.append("Based on the above factors, this fund is suitable for continued consideration aligned with plan objectives and fiduciary standards.")

        return "\n".join(markdown)

    writeup = build_writeup(selected_fund, block)

    # === Preview ===
    st.subheader("📋 Writeup Preview")
    st.markdown(writeup)

    # === DOCX Export ===
    def export_docx(name, writeup):
        doc = Document()
        doc.add_heading(f'Fund Proposal: {name}', 0)
        for line in writeup.split("\n"):
            doc.add_paragraph(line)
        bio = BytesIO()
        doc.save(bio)
        return bio.getvalue()

    # === PPTX Export ===
    def export_pptx(name, writeup):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank

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

    # === Downloads ===
    st.download_button("📄 Export as DOCX", export_docx(selected_fund, writeup), file_name=f"{selected_fund}_proposal.docx")
    st.download_button("📊 Export as PPTX", export_pptx(selected_fund, writeup), file_name=f"{selected_fund}_slide.pptx")

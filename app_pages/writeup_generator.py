import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches
from io import BytesIO
from datetime import datetime
from docx import Document
from pptx import Presentation
from pptx.util import Inches

# --- Ticker Lookup (stacked + inline formats) ---
def build_ticker_lookup(pdf):
    lookup = {}
    for page in pdf.pages:
        lines = page.extract_text().split("\n") if page.extract_text() else []
        for i in range(len(lines) - 1):
            name_line = lines[i].strip()
            ticker_line = lines[i + 1].strip()
            if (
                re.match(r"^[A-Z]{4,6}X?$", ticker_line)
                and len(name_line.split()) >= 3
                and not re.match(r"^[A-Z]{4,6}X?$", name_line)
            ):
                clean_name = " ".join(name_line.split())
                lookup[clean_name] = ticker_line.strip()
        for line in lines:
            line = line.strip()
            parts = line.rsplit(" ", 1)
            if (
                len(parts) == 2
                and re.match(r"^[A-Z]{4,6}X?$", parts[1])
                and len(parts[0].split()) >= 3
            ):
                lookup[parts[0].strip()] = parts[1].strip()
    return lookup

# --- Extract fund name from block ---
def get_fund_name(block, lookup):
    block_lower = block.lower()
    for name in lookup:
        if name.lower() in block_lower:
            return name
    lines = block.split("\n")
    top_lines = lines[:6]
    candidates = [line.strip() for line in top_lines if sum(c.isupper() for c in line) > 5]
    for line in candidates:
        matches = get_close_matches(line, lookup.keys(), n=1, cutoff=0.5)
        if matches:
            return matches[0]
    metric_start = None
    for i, line in enumerate(lines):
        if any(metric in line for metric in [
            "Manager Tenure", "Excess Performance", "Peer Return Rank",
            "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
            "Sortino Ratio Rank", "Tracking Error Rank"
        ]):
            metric_start = i
            break
    if metric_start and metric_start > 0:
        fallback_name = lines[metric_start - 1].strip()
        fallback_name = re.sub(r"(This|The)?\s?fund\s(has|meets).*", "", fallback_name, flags=re.IGNORECASE).strip()
        if fallback_name:
            return fallback_name
    return "UNKNOWN FUND"

# --- Generate a writeup from a fund row ---
def generate_fund_writeup(row):
    name = row["Fund Name"]
    ticker = row["Ticker"]
    meets = row["Meets Criteria"]
    metrics = "\n".join(
        f"- {k}: {v}" for k, v in row.items()
        if k not in ["Fund Name", "Ticker", "Meets Criteria"]
    )
    return f"""### {name} ({ticker})

**Watchlist Status:** {"✅ Meets Criteria" if meets == "Yes" else "⚠️ On Watchlist"}

**Metric Summary**
{metrics}
"""

# --- Main App ---
def run():
    st.set_page_config(page_title="Fund Writeup Generator", layout="wide")
    st.title("Fund Writeup Generator")

    st.markdown("Upload an MPI-style PDF fund scorecard. The app will extract each fund, evaluate watchlist status, and generate writeups.")

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if pdf_file:
        rows = []
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            status_text = st.empty()
            progress = st.progress(0)

            ticker_lookup = build_ticker_lookup(pdf)
            if not any("Enhanced Commodity" in name for name in ticker_lookup):
                ticker_lookup["WisdomTree Enhanced Commodity Stgy Fd"] = "WTES"

            for i, page in enumerate(pdf.pages):
                txt = page.extract_text()
                if not txt:
                    progress.progress((i + 1) / total_pages)
                    status_text.text(f"Skipping page {i + 1} (no text)...")
                    continue

                blocks = re.split(
                    r"\n(?=[^\n]*?(Fund )?(Meets Watchlist Criteria|has been placed on watchlist))",
                    txt)

                for block in blocks:
                    if not block.strip():
                        continue
                    fund_name = get_fund_name(block, ticker_lookup)
                    ticker = ticker_lookup.get(fund_name, "N/A")
                    meets = "Yes" if "placed on watchlist" not in block else "No"

                    metrics = {}
                    for line in block.split("\n"):
                        if line.startswith((
                            "Manager Tenure", "Excess Performance", "Peer Return Rank",
                            "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
                            "Sortino Ratio Rank", "Tracking Error Rank",
                            "Tracking Error (3Yr)", "Tracking Error (5Yr)"
                        )):
                            m = re.match(r"^(.*?)\s+(Pass|Review)", line.strip())
                            if m:
                                metrics[m.group(1).strip()] = m.group(2).strip()

                    if metrics:
                        rows.append({
                            "Fund Name": fund_name,
                            "Ticker": ticker,
                            "Meets Criteria": meets,
                            **metrics
                        })

                progress.progress((i + 1) / total_pages)
                status_text.text(f"Processed page {i + 1} of {total_pages}")

            progress.empty()
            status_text.empty()

        df = pd.DataFrame(rows)

        for i, row in df.iterrows():
            if row["Ticker"] == "N/A" and row["Fund Name"] != "UNKNOWN FUND":
                fund_name = row["Fund Name"]
                match = get_close_matches(fund_name, ticker_lookup.keys(), n=1, cutoff=0.5)
                if match:
                    df.at[i, "Ticker"] = ticker_lookup[match[0]]
                else:
                    for known_name in ticker_lookup:
                        if fund_name.lower() in known_name.lower() or known_name.lower() in fund_name.lower():
                            df.at[i, "Ticker"] = ticker_lookup[known_name]
                            break

        if not df.empty:
            st.success(f"✅ Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            # === Writeup Generator ===
            with st.expander("📝 Generate Fund Writeups"):
                selected_fund = st.selectbox("Select a fund", df["Fund Name"].tolist())
                selected_row = df[df["Fund Name"] == selected_fund].iloc[0]
                writeup = generate_fund_writeup(selected_row)

                st.subheader("📋 Writeup Preview")
                st.markdown(writeup)

                # DOCX export
                doc = Document()
                doc.add_heading(selected_fund, level=1)
                for line in writeup.splitlines():
                    doc.add_paragraph(line.replace("**", "").replace("###", ""))
                docx_buf = BytesIO()
                doc.save(docx_buf)
                st.download_button("📄 Download as DOCX", docx_buf.getvalue(), file_name=f"{selected_fund}_writeup.docx")

                # PPTX export
                prs = Presentation()
                slide = prs.slides.add_slide(prs.slide_layouts[5])
                box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(6.5))
                tf = box.text_frame
                for line in writeup.splitlines():
                    tf.add_paragraph().text = line.replace("**", "").replace("###", "")
                pptx_buf = BytesIO()
                prs.save(pptx_buf)
                st.download_button("📊 Download as PPTX", pptx_buf.getvalue(), file_name=f"{selected_fund}_writeup.pptx")

        else:
            st.warning("No fund entries found.")
    else:
        st.info("Please upload an MPI PDF to begin.")

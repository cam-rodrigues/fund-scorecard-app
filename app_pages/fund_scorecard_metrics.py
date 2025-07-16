import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches
from io import BytesIO
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from datetime import datetime

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

# --- Main App ---
def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

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
                            "Tracking Error (3Yr)", "Tracking Error (5Yr)")):
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
            st.success(f"Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download as CSV",
                                   data=csv,
                                   file_name="fund_criteria_results.csv",
                                   mime="text/csv")

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_cleaned = df.copy()
                
                    # Convert everything to string first, then replace all error values
                    df_cleaned = df_cleaned.astype(str).replace(["nan", "None", "NUM", "NaN", "NAN"], "")
                
                    df_cleaned.to_excel(writer, index=False, sheet_name="Fund Criteria", startrow=2)
                
                    workbook = writer.book
                    worksheet = writer.sheets["Fund Criteria"]
                
                    header_format = workbook.add_format({
                        'bold': True, 'bg_color': '#D9E1F2', 'font_color': '#1F4E78',
                        'align': 'center', 'valign': 'vcenter', 'border': 1, 'bottom': 2
                    })
                    status_format_pass = workbook.add_format({
                        'bg_color': '#C6EFCE', 'font_color': '#006100', 'border': 1
                    })
                    status_format_review = workbook.add_format({
                        'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'border': 1
                    })
                    normal_format = workbook.add_format({'border': 1})
                    center_format = workbook.add_format({'border': 1, 'align': 'center'})
                    updated_format = workbook.add_format({'italic': True, 'font_color': '#444444'})
                
                    worksheet.write('A1', datetime.now().strftime("Last Updated: %B %d, %Y"), updated_format)
                
                    for col_num, col_name in enumerate(df_cleaned.columns):
                        max_len = max(df_cleaned[col_name].astype(str).map(len).max(), len(col_name)) + 2
                        worksheet.set_column(col_num, col_num, max_len)
                        worksheet.write(2, col_num, col_name, header_format)
                
                    worksheet.autofilter(f"A3:{xl_col_to_name(len(df_cleaned.columns) - 1)}3")
                    worksheet.freeze_panes(3, 0)
                
                    for row in range(len(df_cleaned)):
                        for col in range(len(df_cleaned.columns)):
                            value = df_cleaned.iloc[row, col]
                            col_name = df_cleaned.columns[col]
                            fmt = center_format if col_name == "Ticker" else normal_format
                
                            if col_name == "Meets Criteria":
                                fmt = workbook.add_format({'border': 2, 'align': 'center'})
                
                            worksheet.write(row + 3, col, value, fmt)
                
                    for col_num, col_name in enumerate(df_cleaned.columns):
                        col_letter = xl_col_to_name(col_num)
                        data_range = f"{col_letter}4:{col_letter}{len(df_cleaned)+3}"
                
                        worksheet.conditional_format(data_range, {
                            'type': 'text', 'criteria': 'containing', 'value': 'Pass', 'format': status_format_pass
                        })
                        worksheet.conditional_format(data_range, {
                            'type': 'text', 'criteria': 'containing', 'value': 'Yes', 'format': status_format_pass
                        })
                        worksheet.conditional_format(data_range, {
                            'type': 'text', 'criteria': 'containing', 'value': 'Review', 'format': status_format_review
                        })
                        worksheet.conditional_format(data_range, {
                            'type': 'text', 'criteria': 'containing', 'value': 'No', 'format': status_format_review
                        })



                excel_data = output.getvalue()
                st.download_button("Download as Excel",
                                   data=excel_data,
                                   file_name="fund_criteria_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")

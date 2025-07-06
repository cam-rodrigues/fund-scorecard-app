import streamlit as st
import pandas as pd
import pdfplumber
import io
from difflib import SequenceMatcher
from utils.excel_utils import update_excel_with_template
from utils.pdf_utils import extract_data_from_pdf

# === Scoring Logic ===
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def run():
    st.markdown("## 🎯 FidSync: Fund Scorecard")

    st.markdown("""
        <style>
            .section-box {
                background-color: #f8f9fa;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                margin-bottom: 2rem;
            }
            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #1565c0;
                margin-bottom: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # === Section 1: File Upload ===
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">1. Upload Files</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        pdf_file = st.file_uploader("Upload PDF Report", type=["pdf"])
    with c2:
        excel_file = st.file_uploader("Upload Excel Template", type=["xlsx", "xlsm"])

    sheet_name = st.text_input("Excel Sheet Name (case-sensitive)", value="Current Period")

    c3, c4 = st.columns(2)
    with c3:
        start_page = st.number_input("Start Page", min_value=1, value=1)
    with c4:
        end_page = st.number_input("End Page", min_value=start_page, value=start_page + 1)

    st.markdown('</div>', unsafe_allow_html=True)

    # === Section 2: Options ===
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">2. Match Settings</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        threshold = st.slider("Match Sensitivity Threshold", 0.0, 1.0, 0.8, 0.01)
    with col2:
        exact_only = st.checkbox("Exact Match Only", value=False)

    st.markdown('</div>', unsafe_allow_html=True)

    # === Section 3: Investment Options ===
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">3. Provide Investment Options</div>', unsafe_allow_html=True)

    input_method = st.radio("Input Method", ["Paste (Manual)", "Upload CSV"], horizontal=True)
    investment_options = []

    if input_method == "Paste (Manual)":
        raw_text = st.text_area("Paste investment options here (one per line)", height=150)
        investment_options = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
    else:
        csv_file = st.file_uploader("Upload Investment Options CSV", type=["csv"], key="csv_upload")
        if csv_file:
            try:
                df = pd.read_csv(csv_file)
                investment_options = df.iloc[:, 0].dropna().astype(str).tolist()
            except Exception as e:
                st.error(f"❌ Failed to read CSV: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # === Warning if mismatch in counts ===
    if pdf_file and investment_options:
        try:
            pdf_data = io.BytesIO(pdf_file.read())
            fund_names = extract_data_from_pdf(pdf_data, start_page, end_page)

            if len(fund_names) != len(investment_options):
                st.warning(f"⚠️ Fund count ({len(fund_names)}) ≠ Investment options ({len(investment_options)}) — review before matching.")
            else:
                st.success(f"✅ {len(fund_names)} funds matched {len(investment_options)} options — ready to go!")

            st.session_state.fund_names = fund_names
            st.session_state.investment_options = investment_options
            st.session_state.settings = {
                "threshold": threshold,
                "exact_only": exact_only,
                "sheet_name": sheet_name,
                "excel_file": excel_file,
                "pdf_file": pdf_data
            }

        except Exception as e:
            st.error(f"❌ PDF extraction error: {e}")

    # === Match + Preview ===
    if st.button("🔍 Run Match"):
        fund_names = st.session_state.get("fund_names", [])
        investment_options = st.session_state.get("investment_options", [])
        settings = st.session_state.get("settings", {})

        if not (fund_names and investment_options and settings):
            st.error("⚠️ Missing data or settings. Please complete all prior steps.")
            return

        threshold = settings["threshold"]
        exact_only = settings["exact_only"]

        matches = []
        for fund in fund_names:
            best_match = None
            best_score = -1

            for option in investment_options:
                score = 1.0 if fund == option else similar(fund, option)
                if exact_only and fund != option:
                    continue
                if score > best_score:
                    best_match = option
                    best_score = score

            status = "Pass" if best_score >= threshold else "Fail"
            matches.append({
                "Fund Name (Raw)": fund,
                "Matched Option": best_match or "",
                "Score": round(best_score, 2),
                "Status": status
            })

        result_df = pd.DataFrame(matches)

        # === Summary Card ===
        pass_count = sum(1 for m in matches if m["Status"] == "Pass")
        fail_count = sum(1 for m in matches if m["Status"] == "Fail")

        st.markdown("### 📊 Match Summary")
        st.info(f"✅ Passed: {pass_count} | ❌ Failed: {fail_count} | Total: {len(matches)}")

        # === Table Preview ===
        st.markdown("### 🔍 Match Preview Table")
        st.dataframe(
            result_df.style
                .applymap(lambda val: 'background-color: #c8e6c9' if val == 'Pass' else ('background-color: #f8d7da' if val == 'Fail' else ''),
                          subset=["Status"])
                .format({"Score": "{:.2f}"})
        )

        # === Export Options ===
        st.markdown("### 📁 Export Options")
        col_export = st.columns(2)

        with col_export[0]:
            if settings["excel_file"]:
                if st.button("📤 Export to Excel Template"):
                    try:
                        excel_bytes = io.BytesIO(settings["excel_file"].read())
                        output = update_excel_with_template(excel_bytes, settings["sheet_name"], result_df)
                        st.download_button("📥 Download Updated Excel", data=output, file_name="FidSync_Scorecard.xlsx")
                        st.success("Excel file updated successfully.")
                    except Exception as e:
                        st.error(f"❌ Excel export failed: {e}")

        with col_export[1]:
            csv_buffer = io.StringIO()
            result_df.to_csv(csv_buffer, index=False)
            st.download_button("⬇️ Export Match Table (CSV)", data=csv_buffer.getvalue(), file_name="match_table.csv", mime="text/csv")

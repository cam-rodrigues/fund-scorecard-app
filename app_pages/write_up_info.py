# write_up_info.py

import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Write-Up Info Tool", layout="wide")
    st.title("Write-Up Info Tool")

    # === Step 0: Upload MPI PDF ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    
    if not uploaded_file:
        st.warning("Please upload an MPI PDF to proceed.")
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            st.success(f"MPI PDF successfully loaded with {len(pdf.pages)} pages.")
            st.session_state["mpi_pdf"] = pdf

            # === Step 1: Page 1 - Detect Reporting Quarter ===
            st.subheader("Step 1: Detect Reporting Quarter")

            page1_text = pdf.pages[0].extract_text() if pdf.pages else ""
            quarter_date = None
            quarter_label = None

            patterns = {
                r"3/31/20(\d{2})": "Q1, 20{}",
                r"6/30/20(\d{2})": "Q2, 20{}",
                r"9/30/20(\d{2})": "Q3, 20{}",
                r"12/31/20(\d{2})": "Q4, 20{}"
            }

            for pattern, label in patterns.items():
                match = re.search(pattern, page1_text)
                if match:
                    year_suffix = match.group(1)
                    quarter_label = label.format(year_suffix)
                    quarter_date = pattern[:5] + "20" + year_suffix
                    break

            reporting_info = {
                "quarter_label": quarter_label or "Unknown",
                "quarter_date": quarter_date or "Unknown",
                "total_options": None,
                "client_name": None,
                "prepared_by": None,
            }

            if quarter_label:
                st.success(f"Detected Quarter: {quarter_label}")
            else:
                st.error("Could not determine the reporting quarter from page 1.")

            # === Step 1.5: Extract Investment Option Count and Names ===
            st.subheader("Step 1.5: Reporting Info")

            # Total Options
            total_match = re.search(r"Total Options:\s*(\d+)", page1_text)
            if total_match:
                total_options = int(total_match.group(1))
                reporting_info["total_options"] = total_options
                st.write(f"**Total Investment Options:** {total_options}")
            else:
                st.warning("Could not find 'Total Options:' on page 1.")

            # Prepared For
            prepared_for_match = re.search(r"Prepared For:\s*\n(.*)", page1_text)
            if prepared_for_match:
                client_name = prepared_for_match.group(1).strip()
                reporting_info["client_name"] = client_name
                st.write(f"**Prepared For:** {client_name}")
            else:
                st.warning("Could not find 'Prepared For' client name.")

            # Prepared By
            prepared_by_match = re.search(r"Prepared By:\s*\n(.*)", page1_text)
            if prepared_by_match:
                prepared_by = prepared_by_match.group(1).strip()
                reporting_info["prepared_by"] = prepared_by
                st.write(f"**Prepared By:** {prepared_by}")
            else:
                st.warning("Could not find 'Prepared By' line.")

            # Save page 1 info
            st.session_state["reporting_info"] = reporting_info

            # === Step 2: TOC - Find Key Sections and Page Numbers ===
            st.subheader("Step 2: Table of Contents")

            toc_text = pdf.pages[1].extract_text() if len(pdf.pages) > 1 else ""
            toc_pages = {
                "fund_performance_page": None,
                "fund_scorecard_page": None,
                "fund_factsheets_page": None,
            }

            def extract_page_number(section_label, text):
                pattern = rf"{re.escape(section_label)}\s+(\d+)"
                match = re.search(pattern, text, flags=re.IGNORECASE)
                return int(match.group(1)) if match else None

            toc_pages["fund_performance_page"] = extract_page_number(
                "Fund Performance: Current vs. Proposed Comparison", toc_text)
            toc_pages["fund_scorecard_page"] = extract_page_number(
                "Fund Scorecard", toc_text)
            toc_pages["fund_factsheets_page"] = extract_page_number(
                "Fund Factsheets", toc_text)

            for label, page in toc_pages.items():
                label_display = label.replace("_", " ").title().replace("Page", "")
                if page:
                    st.write(f"**{label_display}** starts on page {page}")
                else:
                    st.warning(f"Could not find section: {label_display}")

            st.session_state["toc_pages"] = toc_pages

    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
# write_up_info.py

import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Write-Up Info Tool", layout="wide")
    st.title("Write-Up Info Tool")

    # === Step 0: Upload MPI PDF ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    
    if not uploaded_file:
        st.warning("Please upload an MPI PDF to proceed.")
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            st.success(f"MPI PDF successfully loaded with {len(pdf.pages)} pages.")
            st.session_state["mpi_pdf"] = pdf

            # === Step 1: Page 1 - Detect Reporting Quarter ===
            st.subheader("Step 1: Detect Reporting Quarter")

            page1_text = pdf.pages[0].extract_text() if pdf.pages else ""
            quarter_label = None
            quarter_date = None

            patterns = {
                r"3/31/20(\d{2})": "Q1, 20{}",
                r"6/30/20(\d{2})": "Q2, 20{}",
                r"9/30/20(\d{2})": "Q3, 20{}",
                r"12/31/20(\d{2})": "Q4, 20{}"
            }

            for pattern, label in patterns.items():
                match = re.search(pattern, page1_text)
                if match:
                    year_suffix = match.group(1)
                    quarter_label = label.format(year_suffix)
                    quarter_date = pattern[:5] + "20" + year_suffix
                    break

            if quarter_label:
                st.success(f"Detected Quarter: {quarter_label}")
            else:
                st.error("Could not determine the reporting quarter from page 1.")

            # === Step 1.5: Extract Total Options, Client, and Preparer Info ===
            st.subheader("Step 1.5: Extract Metadata")

            total_match = re.search(r"Total Options:\s*(\d+)", page1_text)
            total_options = int(total_match.group(1)) if total_match else None

            prepared_for_match = re.search(r"Prepared For:\s*\n(.+)", page1_text)
            prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else None

            prepared_by_match = re.search(r"Prepared By:\s*\n(.+)", page1_text)
            prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else None

            # Display values
            if total_options is not None:
                st.write(f"**Total Investment Options:** {total_options}")
            else:
                st.warning("Could not find total number of investment options.")

            if prepared_for:
                st.write(f"**Prepared For:** {prepared_for}")
            else:
                st.warning("Could not find 'Prepared For' client name.")

            if prepared_by:
                st.write(f"**Prepared By:** {prepared_by}")
            else:
                st.warning("Could not find 'Prepared By' name.")

            # Save everything for later use
            st.session_state["reporting_info"] = {
                "quarter_label": quarter_label,
                "quarter_date": quarter_date,
                "total_options": total_options,
                "prepared_for": prepared_for,
                "prepared_by": prepared_by
            }

    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
